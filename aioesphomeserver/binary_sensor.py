"""
This module defines the BinarySensorEntity class, which represents a binary sensor entity in the system.
The BinarySensorEntity class handles state management, interaction with external requests,
and entity registration within a system.

Classes:
    - BinarySensorEntity: A class representing a binary sensor entity capable of managing and reporting its state.
"""

from __future__ import annotations

import json
from aioesphomeapi.api_pb2 import (  # type: ignore
    ListEntitiesBinarySensorResponse,
    BinarySensorStateResponse,
)
from .basic_entity import BasicEntity


class BinarySensorEntity(BasicEntity):
    """
    A binary sensor entity that handles the state of a binary sensor and interacts with external requests.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "binary_sensor".
        _state (bool): The internal state of the binary sensor (True for ON, False for OFF).
    """

    DOMAIN = "binary_sensor"

    def __init__(self, *args, **kwargs):
        """
        Initialize a BinarySensorEntity instance.

        Args:
            args: Positional arguments passed to the parent BasicEntity class.
            kwargs: Keyword arguments passed to the parent BasicEntity class.
        """
        super().__init__(*args, **kwargs)
        self._state = False

    async def build_list_entities_response(self) -> ListEntitiesBinarySensorResponse:
        """
        Build and return the response for listing this binary sensor entity.

        Returns:
            ListEntitiesBinarySensorResponse: The response containing binary sensor entity details.
        """
        return ListEntitiesBinarySensorResponse(
            object_id=self.object_id,
            name=self.name,
            key=self.key,
            unique_id=self.unique_id,
            device_class=self.device_class,
            icon=self.icon,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> BinarySensorStateResponse:
        """
        Build and return the state response for this binary sensor entity.

        Returns:
            BinarySensorStateResponse: The response containing the binary sensor's current state.
        """
        return BinarySensorStateResponse(
            key=self.key,
            state=await self.get_state()
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the binary sensor's state.

        Returns:
            str: A JSON string representing the binary sensor's state.
        """
        state = await self.get_state()
        state_str = "ON" if state else "OFF"

        data = {
            "id": self.json_id,
            "name": self.name,
            "state": state_str,
            "value": state,
        }
        return json.dumps(data)

    async def get_state(self) -> bool:
        """
        Get the current state of the binary sensor.

        Returns:
            bool: The current state of the binary sensor (True for ON, False for OFF).
        """
        return self._state

    async def set_state(self, val: bool) -> None:
        """
        Set the state of the binary sensor and notify if the state changes.

        Args:
            val (bool): The new state of the binary sensor (True for ON, False for OFF).
        """
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()
