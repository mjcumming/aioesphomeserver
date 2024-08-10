"""
Device module for managing and advertising devices using Zeroconf.

This module defines the Device class, which allows for the registration
of a device on the network using Zeroconf. The class supports adding
entities, managing device information, and handling service discovery.

Classes:
    - Device: Represents a networked device with Zeroconf support.

Functions:
    - (none, since all functionalities are encapsulated within the class)
"""
# pylint: disable=too-many-instance-attributes
import asyncio
import logging 
import socket
import re
import random
import threading
from inspect import getframeinfo, stack
from zeroconf import Zeroconf, ServiceInfo
from . import DeviceInfoResponse
from .logger import format_log


class Device:
    """
    Represents a networked device that can be advertised and discovered via Zeroconf.

    This class provides methods to register and unregister the device on the network
    using Zeroconf, as well as manage device information and related entities.
    """

    def __init__(
        self,
        name,
        mac_address=None,
        model=None,
        project_name=None,
        project_version=None,
        manufacturer="aioesphomeserver",
        friendly_name=None,
        suggested_area=None,
        network=None,
        board=None,
        platform=None
    ):
        """
        Initializes a new Device instance.

        Args:
            name (str): The name of the device.
            mac_address (str, optional): The MAC address of the device. If None, a random one is generated.
            model (str, optional): The model of the device.
            project_name (str, optional): The project name associated with the device.
            project_version (str, optional): The version of the project.
            manufacturer (str, optional): The manufacturer of the device. Defaults to "aioesphomeserver".
            friendly_name (str, optional): A human-readable name for the device.
            suggested_area (str, optional): The suggested area where the device should be placed.
            network (str, optional): The network type (e.g., "wifi").
            board (str, optional): The board type (e.g., "esp01_1m").
            platform (str, optional): The platform (e.g., "ESP8266").
        """
        self.name = name
        self.mac_address = mac_address or self._generate_mac_address()
        self.model = model
        self.project_name = project_name
        self.project_version = project_version
        self.manufacturer = manufacturer
        self.friendly_name = friendly_name
        self.suggested_area = suggested_area
        self.network = network
        self.board = board
        self.platform = platform
        self.entities = []
        self.zeroconf = None
        self.service_info = None
        self.zeroconf_thread = None
        self.api_port = None
        self.web_port = None

    def _generate_mac_address(self):
        """
        Generates a random MAC address for the device.

        Returns:
            str: A randomly generated MAC address.
        """
        return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

    def _get_ip_address(self):
        """
        Gets the local IP address of the device.

        Returns:
            str: The local IP address.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            ip_address = s.getsockname()[0]
        except socket.error:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address

    async def build_device_info_response(self):
        """
        Builds a device info response.

        Returns:
            DeviceInfoResponse: The response containing device information.
        """
        return DeviceInfoResponse(
            uses_password=False,
            name=self.name,
            mac_address=self.mac_address,
        )

    async def log(self, level, tag, message, *args):
        """
        Logs a message with a specified level and tag using the standard logging module.

        Args:
            level (int): The log level (e.g., logging.INFO, logging.ERROR).
            tag (str): A tag for categorizing the log message.
            message (str): The message to log.
            *args: Additional arguments for formatting the message.
        """
        # Get the caller information for better context in the logs
        caller = getframeinfo(stack()[1][0])
        formatted_log = format_log(level, tag, caller.lineno, message % args)

        # Use Python's logging module to log the formatted message
        logging.log(level, "%s - %s: %s" % (self.name, tag, formatted_log))

    async def publish(self, publisher, key, message):
        """
        Publishes a message to all entities that can handle it.

        Args:
            publisher: The entity publishing the message.
            key (str): The key identifying the type of message.
            message (str): The message content.
        """
        for entity in self.entities:
            if publisher == entity:
                continue
            if await entity.can_handle(key, message):
                await entity.handle(key, message)

    def add_entity(self, entity):
        """
        Adds an entity to the device.

        Args:
            entity: The entity to add.

        Raises:
            ValueError: If an entity with the same object_id already exists.
        """
        entity.device = self
        entity.key = len(self.entities) + 1

        existing_entity = [e for e in self.entities if e.object_id == entity.object_id]
        if len(existing_entity) > 0:
            raise ValueError(f"Duplicate object_id: {entity.object_id}")

        self.entities.append(entity)

    def get_entity(self, object_id):
        """
        Retrieves an entity by its object_id.

        Args:
            object_id (str): The object_id of the entity to retrieve.

        Returns:
            The entity with the specified object_id, or None if not found.
        """
        for entity in self.entities:
            if entity.object_id == object_id:
                return entity
        return None

    def get_entity_by_key(self, key):
        """
        Retrieves an entity by its key.

        Args:
            key (int): The key of the entity to retrieve.

        Returns:
            The entity with the specified key, or None if not found.
        """
        if key > len(self.entities):
            return None
        return self.entities[key - 1]

    async def run(self, api_port, web_port):
        """
        Runs the device by starting its entities and registering it with Zeroconf.

        Args:
            api_port (int): The API port to use.
            web_port (int): The web server port to use.
        """
        from . import NativeApiServer, WebServer # pylint: disable=import-outside-toplevel

        self.api_port = api_port
        self.web_port = web_port

        self.add_entity(NativeApiServer(name="_server", port=self.api_port))
        self.add_entity(WebServer(name="_web_server", port=self.web_port))

        # Call register_zeroconf to start the Zeroconf registration
        self.register_zeroconf(self.api_port)

        async with asyncio.TaskGroup() as tg:
            for entity in self.entities:
                if hasattr(entity, 'run'):
                    tg.create_task(entity.run())

    def register_zeroconf(self, port):
        """
        Starts the registration of the device with Zeroconf in a separate thread.

        Args:
            port (int): The port to register with Zeroconf.
        """
        self.zeroconf_thread = threading.Thread(target=self._register_zeroconf_in_thread, args=(port,))
        self.zeroconf_thread.start()

    def _register_zeroconf_in_thread(self, port):
        """
        Registers the device with Zeroconf in a separate thread.

        Args:
            port (int): The port to register with Zeroconf.
        """
        try:
            zeroconf = Zeroconf()
            service_type = "_esphomelib._tcp.local."
            sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', self.name).lower()
            service_name = f"{sanitized_name}.{service_type}"
            ip_address = self._get_ip_address()
            hostname = f"{sanitized_name}.local."

            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(ip_address)],
                port=port,
                properties={
                    "network": self.network or "wifi",
                    "board": self.board or "esp01_1m",
                    "platform": self.platform or "ESP8266",
                    "mac": self.mac_address.replace(":", "").lower(),
                    "version": self.project_version,
                    "friendly_name": self.friendly_name or self.name,
                },
                server=hostname,
            )

            zeroconf.register_service(service_info)
            self.service_info = service_info
            self.zeroconf = zeroconf

            # Synchronous logging in the thread context
            logging.info("Zeroconf service registered: %s on port %s", service_name, port)
        except Exception as e:
            logging.error("Failed to register Zeroconf service: %s", e)

    def unregister_zeroconf(self):
        """
        Unregisters the device from Zeroconf and stops the Zeroconf thread.
        """
        if self.zeroconf and self.service_info:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
        if self.zeroconf_thread:
            self.zeroconf_thread.join()
