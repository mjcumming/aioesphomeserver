"""
This module defines the SwitchEntity class, which represents a switch entity in the system.
The SwitchEntity class handles state management, interaction with external requests,
and entity registration within a system.

Classes:
    - SwitchEntity: A class representing a switch entity capable of managing and reporting its state.
"""

from __future__ import annotations

import json
from aiohttp import web

from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesSwitchResponse,
    SwitchCommandRequest,
    SwitchStateResponse,
)

from .basic_entity import BasicEntity

class SwitchEntity(BasicEntity):
    """
    A switch entity that handles the state of a switch and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "switch".
        assumed_state (Optional[bool]): Whether the state of the switch is assumed (not known for certain).
        _state (bool): The internal state of the switch (True for ON, False for OFF).
    """

    DOMAIN = "switch"

    def __init__(
        self,
        *args,
        assumed_state: bool = None,
        **kwargs
    ):
        """
        Initialize a SwitchEntity instance.

        Args:
            assumed_state (Optional[bool]): Whether the state is assumed (not known for certain).
        """
        super().__init__(*args, **kwargs)
        self.assumed_state = assumed_state
        self._state = False

    async def build_list_entities_response(self) -> ListEntitiesSwitchResponse: # type: ignore
        """
        Build and return the response for listing this switch entity.

        Returns:
            ListEntitiesSwitchResponse: The response containing switch entity details.
        """
        return ListEntitiesSwitchResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            device_class=self.device_class,
            assumed_state=self.assumed_state,
        )

    async def build_state_response(self) -> SwitchStateResponse: # type: ignore
        """
        Build and return the state response for this switch entity.

        Returns:
            SwitchStateResponse: The response containing the switch's current state.
        """
        return SwitchStateResponse(
            key=self.key,
            state=await self.get_state()
        )

    async def get_state(self) -> bool:
        """
        Get the current state of the switch.

        Returns:
            bool: The current state of the switch (True for ON, False for OFF).
        """
        return self._state

    async def set_state(self, val: bool) -> None:
        """
        Set the state of the switch and notify if the state changes.

        Args:
            val (bool): The new state of the switch (True for ON, False for OFF).
        """
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting state to {val}")
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the switch's state.

        Returns:
            str: A JSON string representing the switch's state.
        """
        state = await self.get_state()
        state_str = "ON" if state else "OFF"

        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state_str,
            "value": state,
        }
        return json.dumps(data)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this switch entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/switch/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/switch/{self.object_id}/turn_on", self.route_turn_on)
        router.add_route("POST", f"/switch/{self.object_id}/turn_off", self.route_turn_off)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument 
        """
        Handle a request to get the current state of the switch.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the switch's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_off(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to turn off the switch.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated switch state in JSON format.
        """
        await self.set_state(False)
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_on(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument # type: ignore
        """
        Handle a request to turn on the switch.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated switch state in JSON format.
        """
        await self.set_state(True)
        data = await self.state_json()
        return web.Response(text=data)

    async def handle(self, key: int, message: SwitchCommandRequest) -> None: # type: ignore
        """
        Handle incoming commands to change the state of the switch.

        Args:
            key (int): The key associated with the incoming message.
            message (SwitchCommandRequest): The command message to handle.
        """
        if isinstance(message, SwitchCommandRequest):
            if message.key == self.key:
                await self.set_state(message.state)
