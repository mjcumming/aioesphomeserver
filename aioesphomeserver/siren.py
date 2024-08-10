"""
This module defines the SirenEntity class, which represents a siren entity in the system.
The SirenEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

# siren.py

import json
from urllib import parse
from typing import Optional, List
from aiohttp import web
from . import BasicEntity, ListEntitiesSirenResponse, SirenStateResponse, SirenCommandRequest

class SirenEntity(BasicEntity):
    """
    A siren entity that handles the state of a siren and interacts with external requests.
    """

    DOMAIN = "siren"

    def __init__(
        self,
        *args,
        tones: Optional[List[str]] = None,
        supports_duration: bool = False,
        supports_volume: bool = False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.tones = tones or []
        self.supports_duration = supports_duration
        self.supports_volume = supports_volume
        self.state = False

    async def build_list_entities_response(self) -> ListEntitiesSirenResponse: # type: ignore
        return ListEntitiesSirenResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            tones=self.tones,
            supports_duration=self.supports_duration,
            supports_volume=self.supports_volume,
        )

    async def build_state_response(self) -> SirenStateResponse: # type: ignore
        return SirenStateResponse(
            key=self.key,
            state=self.state,
        )

    async def state_json(self) -> str:
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "tones": self.tones,
            "supports_duration": self.supports_duration,
            "supports_volume": self.supports_volume,
        }
        return json.dumps(data)

    async def set_state(self, state: bool) -> None:
        self.state = state
        await self.notify_state_change()

    async def handle(self, key: int, message: SirenCommandRequest) -> None: # type: ignore
        if isinstance(message, SirenCommandRequest) and message.key == self.key:
            await self.set_state(message.state)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        router.add_route("GET", f"/siren/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response:
        data = await self.state_json()
        return web.Response(text=data)
