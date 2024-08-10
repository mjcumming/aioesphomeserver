"""
This module defines the LightEntity class, which represents a light entity in the system.
The LightEntity class handles state management, interaction with external requests,
and entity registration within a system.

Classes:
    - LightEntity: A class representing a light entity capable of managing and reporting its state,
      including color modes, brightness, effects, and RGB control.
"""

from __future__ import annotations
from urllib import parse
import json
from aiohttp import web
from typing import Optional, List

from aioesphomeapi import LightColorCapability
from . import BasicEntity, ListEntitiesLightResponse, LightStateResponse, LightCommandRequest

class LightEntity(BasicEntity):
    """
    A light entity that handles the state of a light and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "light".
        supported_color_modes (list[int]): The list of supported color modes.
        effects (list[str]): The list of available effects.
        effect (Optional[str]): The currently active effect.
        state (bool): The state of the light (True for ON, False for OFF).
        brightness (float): The brightness level of the light.
        color_brightness (float): The brightness level of the color.
        color_temperature (float): The color temperature of the light.
        cold_white (float): The level of cold white.
        warm_white (float): The level of warm white.
        transition_length (int): The length of the transition in seconds.
        flash_length (int): The length of the flash in seconds.
        color_mode (int): The current color mode.
        red (float): The red color channel value.
        green (float): The green color channel value.
        blue (float): The blue color channel value.
        white (float): The white color channel value.
    """

    DOMAIN = "light"

    def __init__(
        self,
        *args,
        color_modes: Optional[List[int]] = None,
        effects: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a LightEntity instance.

        Args:
            color_modes (Optional[List[int]]): The supported color modes for this light.
            effects (Optional[List[str]]): The list of available effects.
        """
        super().__init__(*args, **kwargs)

        if color_modes is None:
            color_modes = [LightColorCapability.ON_OFF]

        self.supported_color_modes = color_modes

        if effects is None:
            self.effects = []
            self.effect = None
        else:
            self.effects = effects
            self.effect = effects[0] if effects else None

        self.state = False
        self.brightness = 1.0
        self.color_brightness = 1.0
        self.color_temperature = 1.0
        self.cold_white = 1.0
        self.warm_white = 1.0
        self.transition_length = 0
        self.flash_length = 0
        self.color_mode = color_modes[0] if color_modes else 0
        self.red = 1.0
        self.green = 1.0
        self.blue = 1.0
        self.white = 1.0

    async def build_list_entities_response(self) -> ListEntitiesLightResponse: # type: ignore
        """
        Build and return the response for listing this light entity.

        Returns:
            ListEntitiesLightResponse: The response containing light entity details.
        """
        return ListEntitiesLightResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            supported_color_modes=self.supported_color_modes,
            effects=self.effects,
            icon=self.icon,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> LightStateResponse: # type: ignore
        """
        Build and return the state response for this light entity.

        Returns:
            LightStateResponse: The response containing the light's current state.
        """
        return LightStateResponse(
            key=self.key,
            state=self.state,
            brightness=self.brightness,
            color_mode=self.color_mode,
            color_brightness=self.color_brightness,
            red=self.red,
            green=self.green,
            blue=self.blue,
            white=self.white,
            color_temperature=self.color_temperature,
            cold_white=self.cold_white,
            warm_white=self.warm_white,
            effect=self.effect,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the light's state.

        Returns:
            str: A JSON string representing the light's state.
        """
        state = "ON" if self.state else "OFF"
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
            "supports_rgb": self.supported_color_modes and LightColorCapability.RGB in self.supported_color_modes,
        }

        if self.brightness is not None:
            data["brightness"] = int(self.brightness * 255)

        if self.supported_color_modes:
            data["color_mode"] = self.color_mode
            if LightColorCapability.RGB in self.supported_color_modes:
                data["color"] = {
                    "r": int(self.red * 255),
                    "g": int(self.green * 255),
                    "b": int(self.blue * 255),
                }
            if LightColorCapability.WHITE in self.supported_color_modes:
                data["white_value"] = int(self.white * 255)
            if LightColorCapability.COLOR_TEMPERATURE in self.supported_color_modes:
                data["color_temperature"] = self.color_temperature
            if self.color_brightness is not None:
                data["color_brightness"] = int(self.color_brightness * 255)

        if self.effects:
            data["effects"] = self.effects
            data["effect"] = self.effect

        return json.dumps(data)

    async def set_state_from_command(self, command: LightCommandRequest) -> None: # type: ignore
        """
        Set the light entity state from a command request.

        Args:
            command (LightCommandRequest): The command request containing new state values.
        """
        changed = False

        # Update state properties if they are part of the command
        for prop in [
            'state', 'brightness', 'white', 'effect', 'color_brightness',
            'color_temperature', 'cold_white', 'warm_white', 'transition_length', 'flash_length'
        ]:
            has_prop = f"has_{prop}"
            if hasattr(command, has_prop) and getattr(command, has_prop):
                attr = getattr(command, prop)
                current_attr = getattr(self, prop)
                if attr != current_attr:
                    await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting {prop} to {attr}")
                    setattr(self, prop, attr)
                    changed = True

        # Handle RGB updates
        if command.has_rgb:
            if self.red != command.red:
                self.red = command.red
                changed = True

            if self.green != command.green:
                self.green = command.green
                changed = True

            if self.blue != command.blue:
                self.blue = command.blue
                changed = True

            # Ensure that the color mode is set to RGB when RGB values are updated
            if command.has_color_mode and command.color_mode == LightColorCapability.RGB:
                if self.color_mode != LightColorCapability.RGB:
                    self.color_mode = LightColorCapability.RGB
                    changed = True

        if changed:
            await self.notify_state_change()

    async def set_state_from_query(self, state: bool, query: dict) -> None:
        """
        Set the light entity state from query parameters.

        Args:
            state (bool): The state to set (True for ON, False for OFF).
            query (dict): The query parameters containing new state values.
        """
        cmd = LightCommandRequest(
            has_state=True,
            state=state
        )

        for prop in ['effect']:
            if prop in query:
                setattr(cmd, f"has_{prop}", True)
                setattr(cmd, prop, query[prop][0])

        for prop in ['brightness', 'white_value']:
            if prop in query:
                setattr(cmd, f"has_{prop}", True)
                setattr(cmd, prop, float(query[prop][0]) / 255.0)

        for short_color, color in [('r', 'red'), ('g', 'green'), ('b', 'blue')]:
            if short_color in query:
                cmd.has_rgb = True
                setattr(cmd, color, float(query[short_color][0]) / 255.0)

        # Set color mode to RGB if RGB values are provided
        if cmd.has_rgb:
            cmd.has_color_mode = True
            cmd.color_mode = LightColorCapability.RGB

        await self.set_state_from_command(cmd)

    async def handle(self, key: int, message: LightCommandRequest) -> None:
        """
        Handle incoming commands to change the state of the light.

        Args:
            key (int): The key associated with the incoming message.
            message (LightCommandRequest): The command message to handle.
        """
        if isinstance(message, LightCommandRequest) and message.key == self.key:
            await self.set_state_from_command(message)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this light entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/light/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/light/{self.object_id}/turn_on", self.route_turn_on)
        router.add_route("POST", f"/light/{self.object_id}/turn_off", self.route_turn_off)

    async def route_get_state(self, request: web.Request) -> web.Response:
        """
        Handle a request to get the current state of the light.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the light's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_on(self, request: web.Request) -> web.Response:
        """
        Handle a request to turn on the light.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated light state in JSON format.
        """
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(True, query)

        data = await self.state_json()
        return web.Response(text=data)

    async def route_turn_off(self, request: web.Request) -> web.Response:
        """
        Handle a request to turn off the light.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the updated light state in JSON format.
        """
        query = parse.parse_qs(request.query_string)
        await self.set_state_from_query(False, query)

        data = await self.state_json()
        return web.Response(text=data)
