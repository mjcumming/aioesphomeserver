# test_button.py

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, ButtonEntity, ButtonCommandRequest

logging.basicConfig(level=logging.INFO)

class TestButtonEntity(ButtonEntity):
    def __init__(self, name):
        super().__init__(name=name, device_class="button")

    async def simulate_button_press(self):
        await self.log(logging.INFO, self.DOMAIN, f"Simulating button press for {self.name}")
        command_request = ButtonCommandRequest(key=self.key)
        await self.handle(self.key, command_request)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Button",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_button = TestButtonEntity(name=f"{name} Button")
    device.add_entity(test_button)

    asyncio.create_task(test_button.simulate_button_press())

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Test Button Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
