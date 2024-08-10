"""
Module for testing number devices using aioesphomeserver.

This script defines a class to simulate a number device that can be set to a specific value.
It tests different configurations like min/max values, step sizes, and modes, and logs changes from the client.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import NumberEntity, Device
from aioesphomeapi.api_pb2 import NumberMode, NumberCommandRequest  # Import the NumberMode and NumberCommandRequest for testing

# Set up logging
logging.basicConfig(level=logging.INFO)

class AdjustableNumber(NumberEntity):
    """
    Represents a number that can be set to a specific value.
    """
    def __init__(self, name, min_value, max_value, step, unit_of_measurement, mode):
        """
        Initialize an AdjustableNumber instance with specific settings.

        Args:
            name (str): The name of the number entity.
            min_value (float): The minimum value the number can take.
            max_value (float): The maximum value the number can take.
            step (float): The step size for the number.
            unit_of_measurement (str): The unit of measurement for the number.
            mode (int): The mode of the number (e.g., slider, box).
        """
        super().__init__(name=name, min_value=min_value, max_value=max_value, step=step, unit_of_measurement=unit_of_measurement, mode=mode)
        self._state = (min_value + max_value) / 2  # Initialize with a midpoint value

    async def adjust_value(self, new_value):
        """
        Adjusts the number value and logs the change.

        Args:
            new_value (float): The new value to set.
        """
        await self.set_state(new_value)
        logging.info("Adjusted number %s to %s", self.name, new_value)

    async def handle(self, key: int, message: NumberCommandRequest) -> None:
        """
        Handle incoming commands to change the state of the number.

        Args:
            key (int): The key associated with the incoming message.
            message (NumberCommandRequest): The command message to handle.
        """
        if isinstance(message, NumberCommandRequest):
            if message.key == self.key:
                logging.info("Received command for %s: %s", self.name, message)
                await self.set_state(message.state)

async def run_device(name, api_port, web_port):
    """
    Sets up and runs a device with adjustable numbers to test various configurations.

    Args:
        name (str): The name of the device.
        api_port (int): The API port to use.
        web_port (int): The web server port to use.
    """
    logging.info("Setting up %s with API port %d and Web port %d", name, api_port, web_port)

    device = Device(name=name)

    # Create instances of AdjustableNumber with different configurations
    number_slider = AdjustableNumber(name=f"{name} Slider", min_value=0.0, max_value=100.0, step=1.0, unit_of_measurement="%", mode=NumberMode.NUMBER_MODE_SLIDER)
    number_box = AdjustableNumber(name=f"{name} Box", min_value=0.0, max_value=100.0, step=0.5, unit_of_measurement="°C", mode=NumberMode.NUMBER_MODE_BOX)

    device.add_entity(number_slider)
    device.add_entity(number_box)

    # Simulate adjusting the number values
    adjust_slider_task = asyncio.create_task(number_slider.adjust_value(75.0))
    adjust_box_task = asyncio.create_task(number_box.adjust_value(25.5))

    try:
        # Call the device's run method to ensure Zeroconf registration and other setups
        await device.run(api_port, web_port)

        # Wait for the adjustment tasks to complete
        await asyncio.gather(adjust_slider_task, adjust_box_task)
    except asyncio.CancelledError:
        logging.warning("Device %s run was cancelled", name)
        adjust_slider_task.cancel()
        adjust_box_task.cancel()
        raise
    finally:
        logging.info("Cleaning up %s", name)

async def main():
    """
    Main entry point for setting up and running the number device.
    """
    await run_device("Test Number", 6053, 8080)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
