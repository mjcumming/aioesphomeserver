"""
Test suite for the TimeEntity class.
"""

import asyncio
import logging
import sys
import os
from aioesphomeserver import Device, TimeEntity, TimeCommandRequest

logging.basicConfig(level=logging.INFO)

class TestTimeEntity(TimeEntity):
    def __init__(self, name):
        super().__init__(name=name, hour=10, minute=30, second=0)

    async def simulate_time_input(self, hour: int, minute: int, second: int):
        """
        Simulate a time input for testing.
        """
        await self.log(logging.INFO, self.DOMAIN, f"Simulating time input for {self.name}: {hour}:{minute}:{second}")
        command_request = TimeCommandRequest(key=self.key, hour=hour, minute=minute, second=second)
        await self.handle(self.key, command_request)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Time",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_time = TestTimeEntity(name=f"{name} Time")
    device.add_entity(test_time)

    asyncio.create_task(test_time.simulate_time_input(12, 45, 30))

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    """
    Main entry point for setting up and running the time device.
    """
    await run_device("Test Time", 6053, 8080)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
