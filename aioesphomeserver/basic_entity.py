"""
This module defines the BasicEntity class, which represents a generic entity
in the system. The BasicEntity class provides basic functionality for managing
entity states, IDs, and device associations. It is intended to be subclassed
by more specific entity types.

Classes:
    - BasicEntity: A base class for entities that provides methods for managing
      entity state, IDs, and interactions with devices.

The class includes properties for generating object and unique IDs, as well as
methods for handling entity-specific logic like state changes, message handling,
and entity registration within a system.
"""

from __future__ import annotations

import re
import hashlib
from abc import ABC, abstractmethod
from typing import Optional


class BasicEntity(ABC):
    """
    A basic entity class that represents a generic entity in the system.

    Attributes:
        DOMAIN (str): The domain associated with this entity.
        name (str): The name of the entity.
        icon (Optional[str]): The icon associated with the entity.
        device_class (Optional[str]): The class of the device.
        entity_category (Optional[str]): The category of the entity.
        device (Optional[Device]): The device this entity belongs to.
        key (Optional[int]): A unique key assigned to this entity.
    """

    DOMAIN = ""

    def __init__(
        self,
        name: str,
        object_id: Optional[str] = None,
        unique_id: Optional[str] = None,
        icon: Optional[str] = None,
        device_class: Optional[str] = None,
        entity_category: Optional[str] = None,
    ):
        """
        Initialize a BasicEntity instance.

        Args:
            name (str): The name of the entity.
            object_id (Optional[str]): The object ID of the entity.
            unique_id (Optional[str]): The unique ID of the entity.
            icon (Optional[str]): The icon associated with the entity.
            device_class (Optional[str]): The class of the device.
            entity_category (Optional[str]): The category of the entity.
        """
        self.name = name
        self._assigned_object_id = object_id
        self._assigned_unique_id = unique_id
        self.icon = icon
        self.device_class = device_class
        self.entity_category = entity_category

        self.device = None
        self.key = None

        self._state = False

    def set_device(self, device) -> None:
        """
        Set the device associated with this entity.

        Args:
            device (Device): The device to associate with this entity.
        """
        self.device = device

    def set_key(self, key: int) -> None:
        """
        Set the unique key for this entity.

        Args:
            key (int): The key to assign to this entity.
        """
        self.key = key

    @property
    def object_id(self) -> str:
        """
        Get the object ID of the entity.

        Returns:
            str: The object ID.
        """
        if self._assigned_object_id is not None:
            return self._assigned_object_id
        else:
            obj_id = self.name.lower()
            obj_id = re.sub(r"\s+", "_", obj_id)
            obj_id = re.sub(r"[^\w]", "", obj_id)
            self._assigned_object_id = obj_id
            return obj_id

    @property
    def unique_id(self) -> str:
        """
        Get the unique ID of the entity.

        Returns:
            str: The unique ID.
        """
        if self._assigned_unique_id is not None:
            return self._assigned_unique_id
        else:
            m = hashlib.sha256()
            m.update(self.device.name.encode())
            m.update(self.device.mac_address.encode())
            m.update(self.object_id.encode())
            m.update(self.DOMAIN.encode())
            uid = m.hexdigest()[0:16]
            self._assigned_unique_id = uid
            return uid

    @property
    def json_id(self) -> str:
        """
        Get the JSON ID of the entity, which combines the domain and object ID.

        Returns:
            str: The JSON ID.
        """
        return f"{self.DOMAIN}-{self.object_id}"

    @abstractmethod
    async def build_list_entities_response(self) -> None:
        """
        Build the response for listing entities. This method must be overridden by subclasses.
        """

    @abstractmethod
    async def build_state_response(self) -> None:
        """
        Build the state response for this entity. This method must be overridden by subclasses.
        """

    @abstractmethod
    async def state_json(self) -> None:
        """
        Generate a JSON representation of the entity's state. This method must be overridden by subclasses.
        """

    async def can_handle(self, key: int, message: dict) -> bool: # pylint: disable=unused-argument
        """
        Determine if the entity can handle a given message.

        Args:
            key (int): The key associated with the message.
            message (dict): The message to handle.

        Returns:
            bool: True if the entity can handle the message, False otherwise.
        """
        return True

    @abstractmethod
    async def handle(self, key: int, message: dict) -> None:
        """
        Handle a given message. This method must be overridden by subclasses.

        Args:
            key (int): The key associated with the message.
            message (dict): The message to handle.
        """

    @abstractmethod
    async def add_routes(self, router) -> None:
        """
        Add routes for this entity to a router. This method must be overridden by subclasses.

        Args:
            router: The router to which routes should be added.
        """

    async def notify_state_change(self) -> None:
        """
        Notify that the entity's state has changed.
        """
        await self.device.publish(
            self,
            'state_change',
            await self.build_state_response()
        )

    async def log(self, level, tag, message, *args):
        """
        Log a message using the device's logging function.

        Args:
            level (int): The log level (e.g., logging.INFO, logging.ERROR).
            tag (str): A tag for categorizing the log message.
            message (str): The message to log.
            *args: Additional arguments for formatting the message.
        """
        await self.device.log(level, f"{self.DOMAIN}.{tag}", message, *args)