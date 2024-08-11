"""
Test suite for the TextEntity class.
"""

import asyncio
import logging
import sys
import os
from aioesphomeserver import Device, TextEntity, TextCommandRequest

logging.basicConfig(level=logging.INFO)

class TestTextEntity(TextEntity):
    def __init__(self, name):
        super().__init__(name=name, min_length=0, max_length=255, mode=0)

    async def simulate_text_input(self, text: str):
        """
        Simulate a text input for testing.
        """
        await self.log(logging.INFO, self.DOMAIN, f"Simulating text input for {self.name}: {text}")
        command_request = TextCommandRequest(key=self.key, state=text)
        await self.handle(self.key, command_request)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Text",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_text = TestTextEntity(name=f"{name} Text")
    device.add_entity(test_text)

    asyncio.create_task(test_text.simulate_text_input("Hello World"))

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    """
    Main entry point for setting up and running the text device.
    """
    await run_device("Test Text", 6053, 8080)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
