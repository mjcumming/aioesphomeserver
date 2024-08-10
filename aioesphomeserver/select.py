"""
This module defines the SelectEntity class, which represents a select entity in the system.
The SelectEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""
# select.py

import json
from urllib import parse
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
        super().__init__(*args, **kwargs)
        self.options = options or []
        self.state = ""
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesSelectResponse: # type: ignore
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
        return SelectStateResponse(
            key=self.key,
            state=self.state,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "options": self.options,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, state: str) -> None:
        self.state = state
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: SelectCommandRequest) -> None: # type: ignore
        if isinstance(message, SelectCommandRequest) and message.key == self.key:
            await self.set_state(message.state)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        router.add_route("GET", f"/select/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response:
        data = await self.state_json()
        return web.Response(text=data)
