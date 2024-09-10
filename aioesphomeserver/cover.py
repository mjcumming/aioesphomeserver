"""
This module defines the CoverEntity class, which represents a cover entity in the system.
The CoverEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from aiohttp import web
from . import BasicEntity, ListEntitiesCoverResponse, CoverStateResponse, CoverCommandRequest, CoverOperation, LegacyCoverState

class CoverEntity(BasicEntity):
    """
    A cover entity that handles the state of a cover and interacts with external requests.
    """

    DOMAIN = "cover"

    def __init__(
        self,
        *args,
        assumed_state: bool = False,
        supports_position: bool = False,
        supports_tilt: bool = False,
        supports_stop: bool = False,
        legacy_state: LegacyCoverState = LegacyCoverState.LEGACY_COVER_STATE_CLOSED, # type: ignore
        position: float = 0.0,
        tilt: float = 0.0,
        current_operation: CoverOperation = CoverOperation.COVER_OPERATION_IDLE, # type: ignore
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.assumed_state = assumed_state
        self.supports_position = supports_position
        self.supports_tilt = supports_tilt
        self.supports_stop = supports_stop
        self.legacy_state = legacy_state
        self.position = position
        self.tilt = tilt
        self.current_operation = current_operation

    async def build_list_entities_response(self) -> ListEntitiesCoverResponse: # type: ignore
        """
        Build and return the response for listing this cover entity.

        Returns:
            ListEntitiesCoverResponse: The response containing cover entity details.
        """
        return ListEntitiesCoverResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            device_class=self.device_class,
            assumed_state=self.assumed_state,
            supports_position=self.supports_position,
            supports_tilt=self.supports_tilt,
            supports_stop=self.supports_stop,
        )

    async def build_state_response(self) -> CoverStateResponse: # type: ignore
        """
        Build and return the state response for this cover entity.

        Returns:
            CoverStateResponse: The response containing the cover entity's current state.
        """
        return CoverStateResponse(
            key=self.key,
            legacy_state=self.legacy_state,
            position=self.position,
            tilt=self.tilt,
            current_operation=self.current_operation,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the cover entity's state.

        Returns:
            str: A JSON string representing the cover entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "legacy_state": self.legacy_state,
            "position": self.position,
            "tilt": self.tilt,
            "current_operation": self.current_operation,
            "supports_position": self.supports_position,
            "supports_tilt": self.supports_tilt,
            "supports_stop": self.supports_stop,
        }
        return json.dumps(data)

    async def set_cover_state(self, position: float, tilt: float, operation: CoverOperation) -> None: # type: ignore
        """
        Set the state of the cover entity.

        Args:
            position (float): The new position of the cover.
            tilt (float): The new tilt of the cover.
            operation (CoverOperation): The new operation state of the cover.
        """
        self.position = position
        self.tilt = tilt
        self.current_operation = operation
        await self.notify_state_change()

    async def handle(self, key: int, message: CoverCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the cover entity.

        Args:
            key (int): The key associated with the incoming message.
            message (CoverCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="cover", message=f"Handling CoverCommandRequest for {self.name}: {message}")

        if isinstance(message, CoverCommandRequest) and message.key == self.key:
            if message.has_position:
                await self.set_cover_state(position=message.position, tilt=self.tilt, operation=CoverOperation.COVER_OPERATION_IS_OPENING)
            elif message.has_tilt:
                await self.set_cover_state(position=self.position, tilt=message.tilt, operation=CoverOperation.COVER_OPERATION_IS_OPENING)
            elif message.stop:
                await self.set_cover_state(position=self.position, tilt=self.tilt, operation=CoverOperation.COVER_OPERATION_IDLE)
            await self.log(level=2, tag="cover", message=f"Cover state set for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this cover entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/cover/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the cover entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the cover entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
