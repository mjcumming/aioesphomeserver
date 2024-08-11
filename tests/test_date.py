"""
Test suite for the DateEntity class.
"""

import asyncio
import logging
import sys
import os
from aioesphomeserver import Device, DateEntity, DateCommandRequest

logging.basicConfig(level=logging.INFO)

class TestDateEntity(DateEntity):
    def __init__(self, name):
        super().__init__(name=name, year=2024, month=8, day=10)

    async def simulate_date_input(self, year: int, month: int, day: int):
        """
        Simulate a date input for testing.
        """
        await self.log(logging.INFO, self.DOMAIN, f"Simulating date input for {self.name}: {year}-{month}-{day}")
        command_request = DateCommandRequest(key=self.key, year=year, month=month, day=day)
        await self.handle(self.key, command_request)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Date",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_date = TestDateEntity(name=f"{name} Date")
    device.add_entity(test_date)

    asyncio.create_task(test_date.simulate_date_input(2024, 8, 10))

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    """
    Main entry point for setting up and running the date device.
    """
    await run_device("Test Date", 6053, 8080)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
