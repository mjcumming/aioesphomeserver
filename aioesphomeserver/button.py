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
        super().__init__(*args, **kwargs)
        self.device_class = device_class

    async def build_list_entities_response(self) -> ListEntitiesButtonResponse: # type: ignore
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
        pass  # Button does not maintain state

    async def state_json(self) -> str:
        data = {
            "id": self.json_id,
            "name": self.name,
        }
        return json.dumps(data)

    async def handle(self, key: int, message: ButtonCommandRequest) -> None: # type: ignore
        if isinstance(message, ButtonCommandRequest) and message.key == self.key:
            await self.log(logging.INFO, self.DOMAIN, f"Button {self.name} pressed.")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        router.add_route("POST", f"/button/{self.object_id}/press", self.route_press)

    async def route_press(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        command_request = ButtonCommandRequest(key=self.key)
        await self.handle(self.key, command_request)
        data = await self.state_json()
        return web.Response(text=data)
