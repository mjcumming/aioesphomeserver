"""
This module defines the SelectEntity class, which represents a select entity in the system.
The SelectEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""
# select.py

import json
from typing import Optional, List
from aiohttp import web
from . import BasicEntity, ListEntitiesSelectResponse, SelectStateResponse, SelectCommandRequest

class SelectEntity(BasicEntity):
    """
    A select entity that handles the state of a select input and interacts with external requests.
    """

    DOMAIN = "select"

    def __init__(
        self,
        *args,
        options: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize a SelectEntity instance.

        Args:
            options (Optional[List[str]]): A list of selectable options for the entity.
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.options = options or []
        self.state = ""
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesSelectResponse: # type: ignore
        """
        Build and return the response for listing this select entity.

        Returns:
            ListEntitiesSelectResponse: The response containing select entity details.
        """
        return ListEntitiesSelectResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            options=self.options,
        )

    async def build_state_response(self) -> SelectStateResponse: # type: ignore
        """
        Build and return the state response for this select entity.

        Returns:
            SelectStateResponse: The response containing the select entity's current state.
        """
        return SelectStateResponse(
            key=self.key,
            state=self.state,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the select entity's state.

        Returns:
            str: A JSON string representing the select entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "options": self.options,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, state: str) -> None:
        """
        Set the state of the select entity.

        Args:
            state (str): The new state to set for the select entity.
        """
        self.state = state
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: SelectCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the select entity.

        Args:
            key (int): The key associated with the incoming message.
            message (SelectCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="select", message=f"Handling SelectCommandRequest for {self.name}: {message}")

        if isinstance(message, SelectCommandRequest) and message.key == self.key:
            await self.set_state(message.state)
            await self.log(level=2, tag="select", message=f"Set state to {self.state} for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this select entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/select/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the select entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the select entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
