"""
This module defines the NumberEntity class, which represents a numeric entity
within the system. The NumberEntity class provides functionalities for managing
a numeric input, including handling its configuration like minimum and maximum values,
step size, and unit of measurement.

The NumberEntity class is typically used for devices or entities where the value
can be adjusted through a slider, input box, or other numeric controls.

Classes:
    - NumberEntity: A class that models a numeric entity with adjustable value, 
      supporting different modes of input and various configurations.
"""

from __future__ import annotations

import json
from aiohttp import web
from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesNumberResponse,
    NumberStateResponse,
    NumberMode,
    NumberCommandRequest,
)
from .basic_entity import BasicEntity


class NumberEntity(BasicEntity):
    """
    Represents a number entity within the system.

    This class is responsible for managing the state of a numeric entity, including
    handling its configuration like min/max values, step size, and unit of measurement.
    It can be used to model sliders, input boxes, or other numeric inputs.

    Attributes:
        DOMAIN (str): The domain of the entity, typically 'number'.
        min_value (float): The minimum value the entity can take.
        max_value (float): The maximum value the entity can take.
        step (float): The step size for value changes.
        unit_of_measurement (str): The unit of measurement for the value.
        mode (NumberMode): The mode of the number entity, determining how the value is input.
        _state (float): The current state of the entity.
    """

    DOMAIN = "number"

    def __init__(
        self,
        *args,
        min_value: float = None,
        max_value: float = None,
        step: float = None,
        unit_of_measurement: str = None,
        mode: NumberMode = NumberMode.NUMBER_MODE_AUTO, # type: ignore
        **kwargs,
    ):
        """
        Initialize a NumberEntity instance.

        Args:
            min_value (float): The minimum value the entity can take.
            max_value (float): The maximum value the entity can take.
            step (float): The step size for value changes.
            unit_of_measurement (str): The unit of measurement for the value.
            mode (NumberMode): The mode of the number entity, determining how the value is input.
        """
        super().__init__(*args, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.unit_of_measurement = unit_of_measurement
        self.mode = mode
        self._state = 0.0

    async def build_list_entities_response(self) -> ListEntitiesNumberResponse: # type: ignore
        """
        Build the response for listing the number entity.

        Returns:
            ListEntitiesNumberResponse: The response containing the entity's details.
        """
        return ListEntitiesNumberResponse(
            object_id=self.object_id,
            name=self.name,
            key=self.key,
            unique_id=self.unique_id,
            icon=self.icon,
            min_value=self.min_value,
            max_value=self.max_value,
            step=self.step,
            unit_of_measurement=self.unit_of_measurement,
            mode=self.mode,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> NumberStateResponse: # type: ignore
        """
        Build the state response for this number entity.

        Returns:
            NumberStateResponse: The response containing the entity's current state.
        """
        return NumberStateResponse(
            key=self.key,
            state=await self.get_state(),
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the entity's state.

        Returns:
            str: JSON-encoded state of the entity.
        """
        state = await self.get_state()
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state,
        }
        return json.dumps(data)

    async def get_state(self) -> float:
        """
        Get the current state of the entity.

        Returns:
            float: The current state.
        """
        return self._state

    async def set_state(self, val: float) -> None:
        """
        Set the state of the entity and notify if the state changes.

        Args:
            val (float): The new state to set.
        """
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting value to {val}")
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()

    async def handle(self, key: int, message: NumberCommandRequest) -> None: # type: ignore
        """
        Handle incoming commands to change the number state.

        Args:
            key (int): The key associated with the incoming message.
            message (NumberCommandRequest): The command message to handle.
        """
        if message.key == self.key:
            await self.set_state(message.state)

    async def add_routes(self, router) -> None:
        """
        Add HTTP routes for the number entity.

        Args:
            router: The router to which routes should be added.
        """
        router.add_route("GET", f"/number/{self.object_id}", self.route_get_state)
        router.add_route("POST", f"/number/{self.object_id}/set", self.route_set_state)

    async def route_get_state(self, request) -> web.Response: # pylint: disable=unused-argument
        """
        Handle GET requests to retrieve the current state of the number entity.

        Args:
            request: The incoming web request.

        Returns:
            web.Response: The HTTP response containing the current state.
        """
        data = await self.state_json()
        return web.Response(text=data)

    async def route_set_state(self, request) -> web.Response:
        """
        Handle POST requests to set the state of the number entity.

        Args:
            request: The incoming web request.

        Returns:
            web.Response: The HTTP response after setting the state.
        """
        data = await request.json()
        val = data.get("state")
        await self.set_state(float(val))
        return web.Response(text=await self.state_json())
