"""
This module defines the ValveEntity class, which represents a valve entity in the system.
The ValveEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""

import json
from typing import Optional
from aiohttp import web
from . import BasicEntity, ListEntitiesValveResponse, ValveStateResponse, ValveCommandRequest, ValveOperation

class ValveEntity(BasicEntity):
    """
    A valve entity that handles the state of a valve and interacts with external requests.
    """

    DOMAIN = "valve"

    def __init__(
        self,
        *args,
        supports_position: bool = False,
        supports_stop: bool = False,
        position: float = 0.0,
        current_operation: ValveOperation = ValveOperation.VALVE_OPERATION_IDLE,
        **kwargs
    ):
        """
        Initialize a ValveEntity instance.

        Args:
            supports_position (bool): Whether the valve supports positioning.
            supports_stop (bool): Whether the valve supports stopping mid-operation.
            position (float): The current position of the valve.
            current_operation (ValveOperation): The current operation of the valve.
            *args: Additional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*args, **kwargs)
        self.supports_position = supports_position
        self.supports_stop = supports_stop
        self.position = position
        self.current_operation = current_operation
        self.missing_state = False

    async def build_list_entities_response(self) -> ListEntitiesValveResponse: # type: ignore
        """
        Build and return the response for listing this valve entity.

        Returns:
            ListEntitiesValveResponse: The response containing valve entity details.
        """
        return ListEntitiesValveResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            device_class=self.device_class,
            supports_position=self.supports_position,
            supports_stop=self.supports_stop,
        )

    async def build_state_response(self) -> ValveStateResponse: # type: ignore
        """
        Build and return the state response for this valve entity.

        Returns:
            ValveStateResponse: The response containing the valve entity's current state.
        """
        return ValveStateResponse(
            key=self.key,
            position=self.position,
            current_operation=self.current_operation,
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the valve entity's state.

        Returns:
            str: A JSON string representing the valve entity's state.
        """
        data = {
            "id": self.json_id,
            "name": self.name,
            "position": self.position,
            "current_operation": self.current_operation,
            "supports_position": self.supports_position,
            "supports_stop": self.supports_stop,
            "missing_state": self.missing_state,
        }
        return json.dumps(data)

    async def set_valve_state(self, position: float, operation: ValveOperation) -> None:
        """
        Set the state of the valve entity.

        Args:
            position (float): The new position of the valve.
            operation (ValveOperation): The new operation state of the valve.
        """
        self.position = position
        self.current_operation = operation
        await self.notify_state_change()

    async def handle(self, key: int, message: ValveCommandRequest) -> None: # type: ignore
        """
        Handle an incoming command to change the state of the valve entity.

        Args:
            key (int): The key associated with the incoming message.
            message (ValveCommandRequest): The command message to handle.
        """
        await self.log(level=2, tag="valve", message=f"Handling ValveCommandRequest for {self.name}: {message}")

        if isinstance(message, ValveCommandRequest) and message.key == self.key:
            if message.has_position:
                await self.set_valve_state(position=message.position, operation=ValveOperation.VALVE_OPERATION_IS_OPENING)
            elif message.stop:
                await self.set_valve_state(position=self.position, operation=ValveOperation.VALVE_OPERATION_IDLE)
            await self.log(level=2, tag="valve", message=f"Valve state set for {self.name}")

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add HTTP routes for this valve entity to the provided router.

        Args:
            router (web.UrlDispatcher): The router to which the routes should be added.
        """
        router.add_route("GET", f"/valve/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle a request to get the current state of the valve entity.

        Args:
            request (web.Request): The incoming HTTP request.

        Returns:
            web.Response: The response containing the valve entity's state in JSON format.
        """
        data = await self.state_json()
        return web.Response(text=data)
