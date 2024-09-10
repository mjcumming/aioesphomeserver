"""
This module defines a basic server setup using aioesphomeserver.

The server sets up various entities, including binary sensors, switches, lights,
and a listener for handling entity interactions. The server is designed to run
asynchronously, utilizing asyncio for concurrent operations.

Classes:
    - SwitchListener: A listener class that reacts to switch state changes and updates a binary sensor.

Functions:
    - (none, as this script runs the server directly when executed)
"""

import asyncio
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..aioesphomeserver import (
    BinarySensorEntity,
    Device,
    EntityListener,
    NativeApiServer,
    SwitchEntity,
    SwitchStateResponse,
    WebServer,
    LightEntity,
    SensorEntity,
)

from aioesphomeapi import LightColorCapability

class SwitchListener(EntityListener):
    """
    A listener class that listens for switch state changes and updates
    the state of a related binary sensor.
    """
    
    async def handle(self, key, message):
        """
        Handle the incoming message from the switch entity.

        Args:
            key (int): The key associated with the message.
            message (SwitchStateResponse): The message containing the switch state.
        """
        sensor = self.device.get_entity("test_binary_sensor")
        if sensor is not None:
            await sensor.set_state(message.state)

if __name__ == "__main__":
    # Create and configure the device with various entities.
    device = Device(
        name="Test Device",
        mac_address="AC:BC:32:89:0E:C9",
        model="Test Device",
        project_name="aioesphomeserver",
        project_version="1.0.0",
    )

    # Add a binary sensor entity to the device.
    device.add_entity(
        BinarySensorEntity(
            name="Test Binary Sensor",
        )
    )

    # Add a switch entity to the device.
    device.add_entity(
        SwitchEntity(
            name="Test Switch",
        )
    )

    # Add a sensor entity to the device.
    device.add_entity(
        SensorEntity(
            name="Test Sensor"
        )
    )

    # Add a switch listener entity to the device.
    device.add_entity(
        SwitchListener(
            name="_listener",
            entity_id="test_switch"
        )
    )

    # Add a light entity to the device with various effects and color modes.
    device.add_entity(
        LightEntity(
            name="Text Light",
            effects=["Foo", "Bar", "Sparkle"],
            color_modes=[LightColorCapability.ON_OFF | LightColorCapability.BRIGHTNESS | LightColorCapability.RGB | LightColorCapability.WHITE],
        )
    )

    # Run the device's main event loop.
    asyncio.run(device.run())
