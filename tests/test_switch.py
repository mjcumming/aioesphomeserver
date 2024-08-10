"""
Module for testing switch devices using aioesphomeserver.

This script defines classes to simulate switch devices that can toggle their states.
It sets up multiple switch devices, each running in its own asyncio task, and handles
graceful shutdown on exit.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import SwitchEntity, Device
from aioesphomeserver.switch import SwitchCommandRequest 

# Set up logging
logging.basicConfig(level=logging.INFO)

class ToggleSwitch(SwitchEntity):
    """
    Represents a switch that toggles its state between ON and OFF every 5 seconds.
    """
    def __init__(self, name):
        super().__init__(name=name)
        self._state = False

    async def toggle(self):
        """
        Continuously toggles the switch state every 5 seconds.
        """
        try:
            while True:
                self._state = not self._state
                logging.info("Toggling switch %s to %s", self.name, 'ON' if self._state else 'OFF')
                await self.set_state(self._state)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logging.warning("ToggleSwitch %s was cancelled", self.name)
            raise

    async def set_state(self, state):
        """
        Sets the state of the switch and logs the change.

        Args:
            state (bool): The new state of the switch.
        """
        self._state = state
        await self.device.log(logging.INFO, self.DOMAIN, "[%s] Setting state to %s", self.object_id, state)
        await self.notify_state_change()

    async def handle(self, key, message):
        """
        Handles incoming client requests to change the switch state.

        Args:
            key (int): The key associated with the incoming message.
            message (SwitchCommandRequest): The command message to handle.
        """
        if isinstance(message, SwitchCommandRequest):
            if message.key == self.key:
                logging.info("Received command for %s: %s", self.name, message)
                await self.set_state(message.state)

async def run_device(name, api_port, web_port):
    """
    Sets up and runs a device with a toggle switch.

    Args:
        name (str): The name of the device.
        api_port (int): The API port to use.
        web_port (int): The web server port to use.
    """
    logging.info("Setting up %s with API port %d and Web port %d", name, api_port, web_port)

    device = Device(name=name)
    test_switch = ToggleSwitch(name=f"{name} Switch")
    
    device.add_entity(test_switch)  # Associate the switch with the device

    toggle_task = asyncio.create_task(test_switch.toggle())

    try:
        # Call the device's run method to ensure Zeroconf registration and other setups
        await device.run(api_port, web_port)

        # Wait for the toggle task to complete (this will run indefinitely in this example)
        await toggle_task
    except asyncio.CancelledError:
        logging.warning("Device %s run was cancelled", name)
        toggle_task.cancel()
        raise
    finally:
        logging.info("Cleaning up %s", name)

async def main():
    """
    Main entry point for setting up and running multiple switch devices.
    """
    devices = [
        ("Test Switch 1", 6053, 8080),
        ("Test Switch 2", 6054, 8081),
        ("Test Switch 3", 6055, 8082),
        ("Test Switch 4", 6056, 8083),
        ("Test Switch 5", 6057, 8084),
        ("Test Switch 6", 6058, 8085),
        ("Test Switch 7", 6059, 8086),
        ("Test Switch 8", 6060, 8087),
        ("Test Switch 9", 6061, 8088),
        ("Test Switch 10", 6062, 8089),
    ]
    await asyncio.gather(*(run_device(name, api_port, web_port) for name, api_port, web_port in devices))

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
