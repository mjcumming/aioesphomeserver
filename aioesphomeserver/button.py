"""
This module defines the ButtonEntity class, which represents a button entity in the system.
The ButtonEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""
# button.py

import json
import logging
from typing import Optional 
from aiohttp import web
from . import BasicEntity, ListEntitiesButtonResponse, ButtonCommandRequest

class ButtonEntity(BasicEntity):
    """
    A button entity that handles the state of a button and interacts with external requests.
    """

    DOMAIN = "button"

    def __init__(
        self,
        *args,
        device_class: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a ButtonEntity instance.

        Args:
            device_class (Optional[str]): The class of the device (e.g., button type).
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.device_class = device_class
        self.pressed = False  # Track if button is pressed

    async def build_list_entities_response(self) -> ListEntitiesButtonResponse: # type: ignore
        """
        Build the response for listing entities.

        Returns:
            ListEntitiesButtonResponse: The response object containing entity details.
        """
        return ListEntitiesButtonResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            device_class=self.device_class,
        )

    async def build_state_response(self) -> None:
        """
        Build the state response for the button entity.
        Note: Button does not maintain state, so this is a no-op.
        """
        pass

    async def state_json(self) -> str:
        """
        Build the JSON representation of the button state.

        Returns:
            str: The JSON string representing the button state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "pressed": self.pressed,  # Include pressed state in response
        }
        return json.dumps(data)

    async def handle(self, key: int, message: ButtonCommandRequest) -> None: # type: ignore
        """
        Handle a button press command.

        Args:
            key (int): The key of the button entity.
            message (ButtonCommandRequest): The command request message.
        """
        if isinstance(message, ButtonCommandRequest) and message.key == self.key:
            await self.log(logging.INFO, self.DOMAIN, f"Button {self.name} pressed.")
            self.pressed = True  # Set pressed state to True when button is pressed
            # Reset the pressed state after handling the command
            self.pressed = False

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for the button entity.

        Args:
            router (web.UrlDispatcher): The URL dispatcher to add routes to.
        """
        router.add_route("POST", f"/button/{self.object_id}/press", self.route_press)

    async def route_press(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle the HTTP request to press the button.

        Args:
            request (web.Request): The HTTP request object.

        Returns:
            web.Response: The HTTP response containing the button state.
        """
        command_request = ButtonCommandRequest(key=self.key)
        await self.handle(self.key, command_request)
        data = await self.state_json()
        return web.Response(text=data)