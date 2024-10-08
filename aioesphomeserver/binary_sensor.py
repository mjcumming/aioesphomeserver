"""
This module defines the BinarySensorEntity class, which represents a binary sensor entity in the system.
The BinarySensorEntity class handles state management, interaction with external requests,
and entity registration within a system.

Classes:
    - BinarySensorEntity: A class representing a binary sensor entity capable of managing 
      and reporting its state.
"""

from __future__ import annotations

import json
from typing import Optional
from aiohttp import web

from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesBinarySensorResponse,
    BinarySensorStateResponse,
)

from .basic_entity import BasicEntity


class BinarySensorEntity(BasicEntity):
    """
    A binary sensor entity that handles the state of a binary sensor and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "binary_sensor".
        _state (bool): The internal state of the binary sensor (True for ON, False for OFF).
        is_status_binary_sensor (bool): Indicates if this is a status binary sensor.
    """

    DOMAIN = "binary_sensor"

    def __init__(
        self,
        *args,
        is_status_binary_sensor: bool = False,
        **kwargs
    ):
        """
        Initialize a BinarySensorEntity instance.

        Args:
            is_status_binary_sensor (bool): Indicates if this is a status binary sensor.
            *args: Positional arguments passed to the parent BasicEntity class.
            **kwargs: Keyword arguments passed to the parent BasicEntity class.
        """
        super().__init__(*args, **kwargs)
        self._state = False
        self.is_status_binary_sensor = is_status_binary_sensor

    async def build_list_entities_response(self) -> ListEntitiesBinarySensorResponse:
        """
        Build and return the response for listing this binary sensor entity.

        Returns:
            ListEntitiesBinarySensorResponse: The response containing binary sensor entity details.
        """
        return ListEntitiesBinarySensorResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            device_class=self.device_class,
            is_status_binary_sensor=self.is_status_binary_sensor,
            disabled_by_default=False,  # Assuming binary sensors are always enabled
            icon=self.icon,
            entity_category=self.entity_category
        )

    async def build_state_response(self) -> BinarySensorStateResponse:
        """
        Build and return the state response for this binary sensor entity.

        Returns:
            BinarySensorStateResponse: The response containing the binary sensor's current state.
        """
        return BinarySensorStateResponse(
            key=self.key,
            state=self._state,
            missing_state=False  # Assuming the state is always known
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the binary sensor's state.

        Returns:
            str: A JSON string representing the binary sensor's state.
        """
        state_str = "ON" if self._state else "OFF"
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state_str,
            "value": self._state,
        }
        return json.dumps(data)

    async def get_state(self) -> bool:
        """
        Get the current state of the binary sensor.

        Returns:
            bool: The current state of the binary sensor (True for ON, False for OFF).
        """
        return self._state

    async def set_state(self, val: bool) -> None:
        """
        Set the state of the binary sensor and notify if the state changes.

        Args:
            val (bool): The new state of the binary sensor (True for ON, False for OFF).
        """
        if self._state != val:
            await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting state to {val}")
            self._state = val
            await self.notify_state_change()

    async def can_handle(self, key: int, message: dict) -> bool:
        """
        Determine if this entity can handle the given message.

        Args:
            key (int): The key associated with the message.
            message (dict): The message to be handled.

        Returns:
            bool: True if this entity can handle the message, False otherwise.
        """
        # Binary sensors typically don't handle incoming messages, so we return False
        return False

    async def handle(self, key: int, message: dict) -> None:
        """
        Handle incoming messages for the binary sensor entity.

        Args:
            key (int): The key associated with the message.
            message (dict): The message to be handled.

        Note:
            Binary sensors typically don't handle incoming state changes,
            so this method doesn't perform any actions.
        """
        # Binary sensors typically don't handle incoming messages, so we just log it
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Received message: {message}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this binary sensor entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/binary_sensor/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response:
        """
        Handle a request to get the current state of the binary sensor.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the binary sensor's state in JSON format.
        """
        try:
            data = await self.state_json()
            return web.Response(text=data, content_type='application/json')
        except Exception as e:
            await self.device.log(2, self.DOMAIN, f"[{self.object_id}] Error in route_get_state: {str(e)}")
            return web.Response(status=500, text="Internal Server Error")