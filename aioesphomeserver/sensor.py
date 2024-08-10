"""
This module defines the SensorEntity class, which represents a sensor entity in the system.
The SensorEntity class handles state management, reporting sensor data, and entity registration
within a system.

Classes:
    - SensorEntity: A class representing a sensor entity capable of managing and reporting its state.
"""

from __future__ import annotations

import json

from aioesphomeapi.api_pb2 import (  # type: ignore
    SensorStateResponse,
    ListEntitiesSensorResponse,
)

from .basic_entity import BasicEntity


class SensorEntity(BasicEntity):
    """
    A sensor entity that handles the state of a sensor and reports sensor data.

    Attributes:
        DOMAIN (str): The domain associated with this entity, set to "sensor".
        unit_of_measurement (Optional[str]): The unit of measurement for the sensor's data.
        accuracy_decimals (Optional[int]): The number of decimal places to use when reporting the sensor's data.
        state_class (Optional[str]): The class of the sensor state (e.g., measurement, total, etc.).
        _state (float): The current state/value of the sensor.
    """

    DOMAIN = "sensor"

    def __init__(
        self,
        *args,
        unit_of_measurement: str = None,
        accuracy_decimals: int = None,
        state_class: str = None,
        **kwargs
    ):
        """
        Initialize a SensorEntity instance.

        Args:
            unit_of_measurement (Optional[str]): The unit of measurement for the sensor's data.
            accuracy_decimals (Optional[int]): The number of decimal places for the sensor's data.
            state_class (Optional[str]): The class of the sensor state.
        """
        super().__init__(*args, **kwargs)
        self.unit_of_measurement = unit_of_measurement
        self.accuracy_decimals = accuracy_decimals
        self.state_class = state_class
        self._state = 0.0

    async def build_list_entities_response(self) -> ListEntitiesSensorResponse: # type: ignore
        """
        Build and return the response for listing this sensor entity.

        Returns:
            ListEntitiesSensorResponse: The response containing sensor entity details.
        """
        return ListEntitiesSensorResponse(
            object_id=self.object_id,
            name=self.name,
            key=self.key,
            unique_id=self.unique_id,
            icon=self.icon,
            unit_of_measurement=self.unit_of_measurement,
            accuracy_decimals=self.accuracy_decimals,
            device_class=self.device_class,
            state_class=self.state_class,
            entity_category=self.entity_category,
        )

    async def build_state_response(self) -> SensorStateResponse: # type: ignore
        """
        Build and return the state response for this sensor entity.

        Returns:
            SensorStateResponse: The response containing the sensor's current state/value.
        """
        return SensorStateResponse(
            key=self.key,
            state=await self.get_state()
        )

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the sensor's state.

        Returns:
            str: A JSON string representing the sensor's state.
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
        Get the current state/value of the sensor.

        Returns:
            float: The current state/value of the sensor.
        """
        return self._state

    async def set_state(self, val: float) -> None:
        """
        Set the state/value of the sensor and notify if the state changes.

        Args:
            val (float): The new state/value of the sensor.
        """
        await self.device.log(3, self.DOMAIN, f"[{self.object_id}] Setting value to {val}")
        old_state = self._state
        self._state = val
        if val != old_state:
            await self.notify_state_change()
