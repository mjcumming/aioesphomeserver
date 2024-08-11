"""
This module defines the TextEntity class, which represents a text entity in the system.
The TextEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from typing import Optional
from aiohttp import web
from . import BasicEntity, ListEntitiesTextResponse, TextStateResponse, TextCommandRequest, TextMode

class TextEntity(BasicEntity):
    """
    A text entity that handles the state of a text input and interacts with external requests.
    """

    DOMAIN = "text"

    def __init__(
        self,
        *args,
        min_length: int = 0,
        max_length: int = 255,
        pattern: Optional[str] = None,
        mode: TextMode = TextMode.TEXT,
        **kwargs
    ):
        """
        Initialize a TextEntity instance.

        Args:
            min_length (int): The minimum length for the text input.
            max_length (int): The maximum length for the text input.
            pattern (Optional[str]): A regex pattern for the text input validation.
            mode (TextMode): The mode of the text input (e.g., TEXT or PASSWORD).
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.mode = mode
        self.state = ""
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesTextResponse: # type: ignore
        """
        Build and return the response for listing this text entity.

        Returns:
            ListEntitiesTextResponse: The response containing text entity details.
        """
        return ListEntitiesTextResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            min_length=self.min_length,
            max_length=self.max_length,
            pattern=self.pattern,
            mode=self.mode,
        )

    async def build_state_response(self) -> TextStateResponse: # type: ignore
        """
        Build and return the state response for this text entity.

        Returns:
            TextStateResponse: The response containing the text entity's current state.
        """
        return TextStateResponse(
            key=self.key,
            state=self.state,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the text entity's state.

        Returns:
            str: A JSON string representing the text entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "mode": self.mode,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, state: str) -> None:
        """
        Set the state of the text entity.

        Args:
            state (str): The new state to set for the text entity.
        """
        self.state = state
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: TextCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the text entity.

        Args:
            key (int): The key associated with the incoming message.
            message (TextCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="text", message=f"Handling TextCommandRequest for {self.name}: {message}")

        if isinstance(message, TextCommandRequest) and message.key == self.key:
            await self.set_state(message.state)
            await self.log(level=2, tag="text", message=f"Set state to {self.state} for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this text entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/text/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the text entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the text entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
