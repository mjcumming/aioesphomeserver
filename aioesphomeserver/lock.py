"""
This module defines the LockEntity class, which represents a lock entity in the system.
The LockEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from typing import Optional 
from aiohttp import web
from . import BasicEntity, ListEntitiesLockResponse, LockStateResponse, LockCommandRequest, LockState, LockCommand

class LockEntity(BasicEntity):
    """
    A lock entity that handles the state of a lock and interacts with external requests.
    """

    DOMAIN = "lock"

    def __init__(
        self,
        *args,
        supports_open: bool = False,
        requires_code: bool = False,
        code_format: Optional[str] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.supports_open = supports_open
        self.requires_code = requires_code
        self.code_format = code_format
        self.state = LockState.LOCK_STATE_NONE

    async def build_list_entities_response(self) -> ListEntitiesLockResponse: # type: ignore
        return ListEntitiesLockResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            supports_open=self.supports_open,
            requires_code=self.requires_code,
            code_format=self.code_format,
        )

    async def build_state_response(self) -> LockStateResponse: # type: ignore
        return LockStateResponse(
            key=self.key,
            state=self.state,
        )

    async def state_json(self) -> str:
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "supports_open": self.supports_open,
            "requires_code": self.requires_code,
            "code_format": self.code_format,
        }
        return json.dumps(data)

    async def set_state(self, state: LockState) -> None: # type: ignore
        self.state = state
        await self.notify_state_change()

    async def handle(self, key: int, message: LockCommandRequest) -> None: # type: ignore
        if isinstance(message, LockCommandRequest) and message.key == self.key:
            if message.command == LockCommand.LOCK_LOCK:
                await self.set_state(LockState.LOCK_STATE_LOCKED)
            elif message.command == LockCommand.LOCK_UNLOCK:
                await self.set_state(LockState.LOCK_STATE_UNLOCKED)
            elif message.command == LockCommand.LOCK_OPEN and self.supports_open:
                await self.set_state(LockState.LOCK_STATE_UNLOCKING)

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        router.add_route("GET", f"/lock/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        data = await self.state_json()
        return web.Response(text=data)
