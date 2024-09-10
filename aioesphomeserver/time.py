"""
This module defines the TimeEntity class, which represents a time entity in the system.
The TimeEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from aiohttp import web
from . import BasicEntity, ListEntitiesTimeResponse, TimeStateResponse, TimeCommandRequest

class TimeEntity(BasicEntity):
    """
    A time entity that handles the state of a time and interacts with external requests.
    """

    DOMAIN = "time"

    def __init__(
        self,
        *args,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        **kwargs
    ):
        """
        Initialize a TimeEntity instance.

        Args:
            hour (int): The hour for the time entity.
            minute (int): The minute for the time entity.
            second (int): The second for the time entity.
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.hour = hour
        self.minute = minute
        self.second = second
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesTimeResponse: # type: ignore
        """
        Build and return the response for listing this time entity.

        Returns:
            ListEntitiesTimeResponse: The response containing time entity details.
        """
        return ListEntitiesTimeResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> TimeStateResponse: # type: ignore
        """
        Build and return the state response for this time entity.

        Returns:
            TimeStateResponse: The response containing the time entity's current state.
        """
        return TimeStateResponse(
            key=self.key,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the time entity's state.

        Returns:
            str: A JSON string representing the time entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, hour: int, minute: int, second: int) -> None:
        """
        Set the state of the time entity.

        Args:
            hour (int): The hour to set for the time entity.
            minute (int): The minute to set for the time entity.
            second (int): The second to set for the time entity.
        """
        self.hour = hour
        self.minute = minute
        self.second = second
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: TimeCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the time entity.

        Args:
            key (int): The key associated with the incoming message.
            message (TimeCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="time", message=f"Handling TimeCommandRequest for {self.name}: {message}")

        if isinstance(message, TimeCommandRequest) and message.key == self.key:
            await self.set_state(message.hour, message.minute, message.second)
            await self.log(level=2, tag="time", message=f"Set time to {self.hour}:{self.minute}:{self.second} for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this time entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/time/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the time entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the time entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
