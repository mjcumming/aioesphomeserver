"""
This module defines the DateEntity class, which represents a date entity in the system.
The DateEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from aiohttp import web
from . import BasicEntity, ListEntitiesDateResponse, DateStateResponse, DateCommandRequest

class DateEntity(BasicEntity):
    """
    A date entity that handles the state of a date and interacts with external requests.
    """

    DOMAIN = "date"

    def __init__(
        self,
        *args,
        year: int = 1970,
        month: int = 1,
        day: int = 1,
        **kwargs
    ):
        """
        Initialize a DateEntity instance.

        Args:
            year (int): The year for the date entity.
            month (int): The month for the date entity.
            day (int): The day for the date entity.
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.year = year
        self.month = month
        self.day = day
        self.missing_state = True

    async def build_list_entities_response(self) -> ListEntitiesDateResponse: # type: ignore
        """
        Build and return the response for listing this date entity.

        Returns:
            ListEntitiesDateResponse: The response containing date entity details.
        """
        return ListEntitiesDateResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> DateStateResponse: # type: ignore
        """
        Build and return the state response for this date entity.

        Returns:
            DateStateResponse: The response containing the date entity's current state.
        """
        return DateStateResponse(
            key=self.key,
            year=self.year,
            month=self.month,
            day=self.day,
            missing_state=self.missing_state,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the date entity's state.

        Returns:
            str: A JSON string representing the date entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_state(self, year: int, month: int, day: int) -> None:
        """
        Set the state of the date entity.

        Args:
            year (int): The year to set for the date entity.
            month (int): The month to set for the date entity.
            day (int): The day to set for the date entity.
        """
        self.year = year
        self.month = month
        self.day = day
        self.missing_state = False
        await self.notify_state_change()

    async def handle(self, key: int, message: DateCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the date entity.

        Args:
            key (int): The key associated with the incoming message.
            message (DateCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="date", message=f"Handling DateCommandRequest for {self.name}: {message}")

        if isinstance(message, DateCommandRequest) and message.key == self.key:
            await self.set_state(message.year, message.month, message.day)
            await self.log(level=2, tag="date", message=f"Set date to {self.year}-{self.month}-{self.day} for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this date entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/date/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the date entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the date entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
