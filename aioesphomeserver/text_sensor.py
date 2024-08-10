"""
This module defines the TextSensorEntity class, which represents a text sensor entity in the system.
The TextSensorEntity class handles state management, interaction with external requests, 
and entity registration within a system.

Classes:
    - TextSensorEntity: A class representing a text sensor entity capable of managing and reporting 
      its state, including handling cases where the state may be missing or not yet set.
"""

from __future__ import annotations
from typing import Optional
from aiohttp import web
import json
from . import BasicEntity, ListEntitiesTextSensorResponse, TextSensorStateResponse

class TextSensorEntity(BasicEntity):
    """
    A text sensor entity that handles the state of a text sensor and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "text_sensor".
        state (str): The current state of the text sensor.
        missing_state (bool): Whether the text sensor has a valid state.
    """

    DOMAIN = "text_sensor"

    def __init__(
        self,
        *args,
        device_class: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a TextSensorEntity instance.

        Args:
            device_class (Optional[str]): The class of the device this sensor represents.
        """
        super().__init__(*args, **kwargs)
        self.device_class = device_class
        self.state = ""
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesTextSensorResponse: # type: ignore
        """
        Build and return the response for listing this text sensor entity.

        Returns:
            ListEntitiesTextSensorResponse: The response containing text sensor entity details.
        """
        return ListEntitiesTextSensorResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            device_class=self.device_class,
        )

    async def build_state_response(self) -> TextSensorStateResponse: # type: ignore
        """
        Build and return the state response for this text sensor entity.

        Returns:
            TextSensorStateResponse: The response containing the text sensor's current state.
        """
        return TextSensorStateResponse(
            key=self.key,
            state=self.state,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the text sensor's state.

        Returns:
            str: A JSON string representing the text sensor's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, state: str) -> None:
        """
        Set the text sensor entity state.

        Args:
            state (str): The new state to set for the text sensor.
        """
        self.state = state
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: TextSensorStateResponse) -> None: # type: ignore
        """
        Handle incoming commands to change the state of the text sensor.

        Args:
            key (int): The key associated with the incoming message.
            message (TextSensorStateResponse): The command message to handle.
        """
        if isinstance(message, TextSensorStateResponse) and message.key == self.key:
            await self.set_state(message.state)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this text sensor entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/text_sensor/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the text sensor.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the text sensor's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
