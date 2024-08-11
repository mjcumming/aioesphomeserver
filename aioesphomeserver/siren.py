# siren.py

import json
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
        """
        Initialize a SirenEntity instance.

        Args:
            tones (Optional[List[str]]): A list of available tones for the siren.
            supports_duration (bool): Whether the siren supports setting a duration.
            supports_volume (bool): Whether the siren supports setting volume.
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.tones = tones or []
        self.supports_duration = supports_duration
        self.supports_volume = supports_volume
        self.state = False

    async def build_list_entities_response(self) -> ListEntitiesSirenResponse: # type: ignore
        """
        Build and return the response for listing this siren entity.

        Returns:
            ListEntitiesSirenResponse: The response containing siren entity details.
        """
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
        """
        Build and return the state response for this siren entity.

        Returns:
            SirenStateResponse: The response containing the siren entity's current state.
        """
        return SirenStateResponse(
            key=self.key,
            state=self.state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the siren entity's state.

        Returns:
            str: A JSON string representing the siren entity's state.
        """
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
        """
        Set the state of the siren entity.

        Args:
            state (bool): The new state to set for the siren entity.
        """
        self.state = state
        await self.notify_state_change()

    async def handle(self, key: int, message: SirenCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the siren entity.

        Args:
            key (int): The key associated with the incoming message.
            message (SirenCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="siren", message=f"Handling SirenCommandRequest for {self.name}: {message}")

        if isinstance(message, SirenCommandRequest) and message.key == self.key:
            await self.set_state(message.state)
            await self.log(level=2, tag="siren", message=f"Set state to {self.state} for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this siren entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/siren/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the siren entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the siren entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
