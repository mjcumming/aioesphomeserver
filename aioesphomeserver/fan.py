"""
This module defines the FanEntity class, which represents a fan entity in the system.
The FanEntity class handles state management, interaction with external requests,
and entity registration within a system.

Classes:
    - FanEntity: A class representing a fan entity capable of managing and reporting its state,
      including speed, direction, oscillation, and preset modes.
"""

# fan.py

from __future__ import annotations
import json
from urllib import parse
from typing import Optional, List
from aiohttp import web
from . import BasicEntity, ListEntitiesFanResponse, FanStateResponse, FanCommandRequest

class FanEntity(BasicEntity):
    """
    A fan entity that handles the state of a fan and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "fan".
        supports_oscillation (bool): Whether the fan supports oscillation.
        supports_speed (bool): Whether the fan supports speed control.
        supports_direction (bool): Whether the fan supports direction control.
        supported_speed_levels (int): Number of speed levels supported by the fan.
        supported_preset_modes (list[str]): List of supported preset modes.
        state (bool): The state of the fan (True for ON, False for OFF).
        oscillating (bool): Whether the fan is oscillating.
        speed_level (int): The current speed level of the fan.
        direction (int): The current direction of the fan.
        preset_mode (str): The current preset mode of the fan.
    """

    DOMAIN = "fan"

    def __init__(
        self,
        *args,
        supports_oscillation: bool = False,
        supports_speed: bool = False,
        supports_direction: bool = False,
        supported_speed_levels: int = 3,
        supported_preset_modes: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a FanEntity instance.

        Args:
            supports_oscillation (bool): Whether the fan supports oscillation.
            supports_speed (bool): Whether the fan supports speed control.
            supports_direction (bool): Whether the fan supports direction control.
            supported_speed_levels (int): Number of speed levels supported by the fan.
            supported_preset_modes (Optional[List[str]]): List of supported preset modes.
        """
        super().__init__(*args, **kwargs)
        self.supports_oscillation = supports_oscillation
        self.supports_speed = supports_speed
        self.supports_direction = supports_direction
        self.supported_speed_levels = supported_speed_levels
        self.supported_preset_modes = supported_preset_modes or []

        self.state = False
        self.oscillating = False
        self.speed_level = 1
        self.direction = 0  # FAN_DIRECTION_FORWARD
        self.preset_mode = ""

    async def build_list_entities_response(self) -> ListEntitiesFanResponse: # type: ignore
        """
        Build and return the response for listing this fan entity.

        Returns:
            ListEntitiesFanResponse: The response containing fan entity details.
        """
        return ListEntitiesFanResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supports_oscillation=self.supports_oscillation,
            supports_speed=self.supports_speed,
            supports_direction=self.supports_direction,
            supported_speed_levels=self.supported_speed_levels,
            icon=self.icon,
            entity_category=self.entity_category,
            supported_preset_modes=self.supported_preset_modes,
        )

    async def build_state_response(self) -> FanStateResponse: # type: ignore
        """
        Build and return the state response for this fan entity.

        Returns:
            FanStateResponse: The response containing the fan's current state.
        """
        return FanStateResponse(
            key=self.key,
            state=self.state,
            oscillating=self.oscillating,
            direction=self.direction,
            speed_level=self.speed_level,
            preset_mode=self.preset_mode,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the fan's state.

        Returns:
            str: A JSON string representing the fan's state.
        """
        state = "ON" if self.state else "OFF"
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
            "oscillating": self.oscillating,
            "direction": self.direction,
            "speed_level": self.speed_level,
            "preset_mode": self.preset_mode,
        }
        return json.dumps(data)

    async def set_state_from_command(self, command: FanCommandRequest) -> None: # type: ignore
        """
        Set the fan entity state from a command request.

        Args:
            command (FanCommandRequest): The command request containing new state values.
        """
        changed = False

        # Update state properties if they are part of the command
        for prop in [
            'state', 'oscillating', 'direction', 'speed_level', 'preset_mode'
        ]:
            has_prop = f"has_{prop}"
            if hasattr(command, has_prop) and getattr(command, has_prop):
                attr = getattr(command, prop)
                current_attr = getattr(self, prop)
                if attr != current_attr:
                    await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting {prop} to {attr}")
                    setattr(self, prop, attr)
                    changed = True

        if changed:
            await self.notify_state_change()

    async def handle(self, key: int, message: FanCommandRequest) -> None: # type: ignore
        """
        Handle incoming commands to change the state of the fan.

        Args:
            key (int): The key associated with the incoming message.
            message (FanCommandRequest): The command message to handle.
        """
        if isinstance(message, FanCommandRequest) and message.key == self.key:
            await self.set_state_from_command(message)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this fan entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/fan/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/fan/{self.object_id}/turn_on", self.route_turn_on)
        router.add_route("POST", f"/fan/{self.object_id}/turn_off", self.route_turn_off)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the fan.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the fan's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_on(self, request: web.Request) -> web.Response:
        """
        Handle a request to turn on the fan.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated fan state in JSON format.
        """
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(True, query)

        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_off(self, request: web.Request) -> web.Response:
        """
        Handle a request to turn off the fan.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated fan state in JSON format.
        """
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(False, query)

        data = await self.state_json()
        return web.Response(text=data)
