"""
This module defines the NativeApiServer class, which handles API requests and manages
client connections. It serves as a server entity that listens for and responds to
requests, including those related to entity state changes, device information, and
subscription management.

Classes:
    - NativeApiServer: A class that represents a server handling API requests and managing client connections.
    - NativeApiConnection: A helper class that manages individual client connections to the server.

Functions:
    - _varuint_to_bytes(value): Converts a varuint (variable-length unsigned integer) to bytes.
"""

from __future__ import annotations

import asyncio
import logging
from aiohttp import web

from .basic_entity import BasicEntity
from . import (  # type: ignore
    ConnectRequest,
    ConnectResponse,
    DeviceInfoRequest,
    DeviceInfoResponse,
    DisconnectRequest,
    DisconnectResponse,
    GetTimeRequest,
    GetTimeResponse,
    HelloRequest,
    HelloResponse,
    ListEntitiesDoneResponse,
    ListEntitiesRequest,
    MESSAGE_TYPE_TO_PROTO,
    PingRequest,
    PingResponse,
    SubscribeHomeAssistantStatesRequest,
    SubscribeHomeassistantServicesRequest,
    SubscribeLogsRequest,
    SubscribeLogsResponse,
    SubscribeStatesRequest,
)

# Create a reverse mapping for message types
PROTO_TO_MESSAGE_TYPE = {v: k for k, v in MESSAGE_TYPE_TO_PROTO.items()}

def _varuint_to_bytes(value: int) -> bytes:
    """Convert a varuint to bytes."""
    if value <= 0x7F:
        return bytes((value,))

    result = bytearray()
    while value:
        temp = value & 0x7F
        value >>= 7
        if value:
            result.append(temp | 0x80)
        else:
            result.append(temp)
    return bytes(result)

class NativeApiConnection:
    """Handles a single client connection to the NativeApiServer."""

    def __init__(self, server: NativeApiServer, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Initialize a NativeApiConnection.

        Args:
            server (NativeApiServer): The server managing this connection.
            reader (asyncio.StreamReader): The stream reader for incoming data.
            writer (asyncio.StreamWriter): The stream writer for outgoing data.
        """
        self.server = server
        self.reader = reader
        self.writer = writer
        self.subscribe_to_logs = False
        self.subscribe_to_states = False

    async def start(self) -> None:
        """Start handling messages from the client."""
        while True:
            await self.handle_next_message()

    async def handle_next_message(self) -> None:
        """Read and process the next message from the client."""
        msg = await self.read_next_message()

        if msg is None:
            return

        await self.server.log(f"{type(msg)}: {msg}")

        if isinstance(msg, HelloRequest):
            await self.handle_hello(msg)
        elif isinstance(msg, ConnectRequest):
            await self.handle_connect(msg)
        elif isinstance(msg, DisconnectRequest):
            await self.handle_disconnect(msg)
        elif isinstance(msg, SubscribeLogsRequest):
            await self.handle_subscribe_logs(msg)
        elif isinstance(msg, PingRequest):
            await self.handle_ping(msg)
        elif isinstance(msg, SubscribeStatesRequest):
            await self.handle_subscribe_states(msg)
        else:
            await self.server.handle_client_request(self, msg)

    async def handle_hello(self, msg: HelloRequest) -> None:
        """Handle a HelloRequest message."""
        resp = HelloResponse(api_version_major=1, api_version_minor=10)
        await self.write_message(resp)

    async def handle_connect(self, msg: ConnectRequest) -> None:
        """Handle a ConnectRequest message."""
        resp = ConnectResponse()
        await self.write_message(resp)

    async def handle_disconnect(self, msg: DisconnectRequest) -> None:
        """Handle a DisconnectRequest message."""
        resp = DisconnectResponse()
        await self.write_message(resp)
        self.writer.close()
        await self.writer.wait_closed()

    async def handle_subscribe_logs(self, msg: SubscribeLogsRequest) -> None:
        """Handle a SubscribeLogsRequest message."""
        self.subscribe_to_logs = True

        resp = SubscribeLogsResponse()
        resp.level = msg.level
        resp.message = b'Subscribed to logs'

        await self.write_message(resp)

    async def handle_subscribe_states(self, msg: SubscribeStatesRequest) -> None:
        """Handle a SubscribeStatesRequest message."""
        self.subscribe_to_states = True
        await self.server.log("Subscribed to states")
        await self.server.send_all_states(self)

    async def handle_ping(self, msg: PingRequest) -> None:
        """Handle a PingRequest message."""
        resp = PingResponse()
        await self.write_message(resp)

    async def log(self, message: str) -> None:
        """
        Send a log message to the client.

        Args:
            message (str): The log message to send.
        """
        resp = SubscribeLogsResponse()
        resp.message = str.encode(message)

        await self.write_message(resp)

    async def read_next_message(self):
        """Read the next message from the client."""
        preamble = await self._read_varuint()
        length = await self._read_varuint()
        message_type = await self._read_varuint()

        klass = MESSAGE_TYPE_TO_PROTO.get(message_type)
        if klass is None:
            return None

        msg = klass()
        msg_bytes = await self.reader.read(length)

        msg.MergeFromString(msg_bytes)

        return msg

    async def write_message(self, msg) -> None:
        """
        Write a message to the client.

        Args:
            msg: The message to write.
        """
        if msg is None:
            return

        out = []
        type_ = PROTO_TO_MESSAGE_TYPE[type(msg)]
        data = msg.SerializeToString()

        out.append(b"\0")
        out.append(_varuint_to_bytes(len(data)))
        out.append(_varuint_to_bytes(type_))
        out.append(data)

        self.writer.write(b"".join(out))
        await self.writer.drain()

    async def _read_varuint(self) -> int:
        """Read a variable-length unsigned integer from the client."""
        result = 0
        bitpos = 0
        while not self.reader.at_eof():
            val_byte = await self.reader.read(1)
            if len(val_byte) != 1:
                return -1

            val = val_byte[0]
            result |= (val & 0x7F) << bitpos
            if (val & 0x80) == 0:
                return result
            bitpos += 7
        return -1

class NativeApiServer(BasicEntity):
    """
    Represents a server that handles API requests and manages client connections.
    """

    DOMAIN = "server"

    def __init__(self, *args, port=6053, **kwargs):
        """
        Initialize a NativeApiServer instance.

        Args:
            port (int): The port on which the server listens. Defaults to 6053.
        """
        super().__init__(*args, **kwargs)
        self.port = port
        self._clients = set()

    async def run(self) -> None:
        """
        Start the server and begin accepting connections.
        """
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.port)
        async with server:
            await self.device.log(2, "api", f"starting on port {self.port}!")
            await server.start_serving()

            while True:
                await asyncio.sleep(3600)

    async def log(self, message: str) -> None:
        """
        Log a message to all connected clients that are subscribed to logs.

        Args:
            message (str): The message to log.
        """
        for client in self._clients:
            if client.subscribe_to_logs:
                await client.log(message)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Handle a new client connection.

        Args:
            reader (asyncio.StreamReader): The stream reader for incoming data.
            writer (asyncio.StreamWriter): The stream writer for outgoing data.
        """
        connection = NativeApiConnection(self, reader, writer)
        self._clients.add(connection)
        task = asyncio.create_task(connection.start())
        task.add_done_callback(lambda t: self._clients.discard(connection))

    async def handle_client_request(self, client: NativeApiConnection, message) -> None:
        """
        Handle a request from a client.

        Args:
            client (NativeApiConnection): The client making the request.
            message: The message received from the client.
        """
        if isinstance(message, SubscribeHomeassistantServicesRequest):
            pass
        elif isinstance(message, SubscribeHomeAssistantStatesRequest):
            pass
        elif isinstance(message, ListEntitiesRequest):
            await self.handle_list_entities(client, message)
        elif isinstance(message, DeviceInfoRequest):
            await self.handle_device_info(client)
        else:
            await self.device.publish(self, 'client_request', message)

    async def handle_list_entities(self, client: NativeApiConnection, message: ListEntitiesRequest) -> None:
        """
        Handle a ListEntitiesRequest message.

        Args:
            client (NativeApiConnection): The client making the request.
            message (ListEntitiesRequest): The message received from the client.
        """
        for entity in self.device.entities:
            msg = await entity.build_list_entities_response()
            if msg is not None:
                await client.write_message(msg)

        done_msg = ListEntitiesDoneResponse()
        await client.write_message(done_msg)

    async def handle_device_info(self, client: NativeApiConnection) -> None:
        """
        Handle a DeviceInfoRequest message.

        Args:
            client (NativeApiConnection): The client making the request.
        """
        msg = await self.device.build_device_info_response()
        await client.write_message(msg)

    async def send_all_states(self, client: NativeApiConnection) -> None:
        """
        Send all entity states to the client.

        Args:
            client (NativeApiConnection): The client to receive the states.
        """
        for entity in self.device.entities:
            msg = await entity.build_state_response()
            if msg is not None:
                await client.write_message(msg)

    async def handle(self, key: str, message) -> None:
        """
        Handle internal messages related to state changes or logs.

        Args:
            key (str): The key indicating the type of message.
            message: The message data.
        """
        if key == 'state_change':
            for client in self._clients:
                if client.subscribe_to_states:
                    await client.write_message(message)

        if key == 'log':
            msg = SubscribeLogsResponse(
                level=message[0],
                message=str.encode(message[1])
            )

            for client in self._clients:
                if client.subscribe_to_logs:
                    await client.write_message(msg)

    async def build_list_entities_response(self):
        """
        Build the response for listing entities. This method should be overridden by subclasses.
        """
        return None

    async def build_state_response(self):
        """
        Build the state response for this entity. This method should be overridden by subclasses.
        """
        return None

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the entity's state. This method should be overridden by subclasses.
        """
        return "{}"

    async def add_routes(self, router) -> None:
        """
        Add routes for this entity to a router. This method should be overridden by subclasses.

        Args:
            router: The router to which routes should be added.
        """
        router.add_route("GET", f"/server/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request) -> web.Response:
        """
        Handle GET requests to retrieve the server's state.

        Args:
            request: The incoming HTTP request.

        Returns:
            web.Response: The response containing the server's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
