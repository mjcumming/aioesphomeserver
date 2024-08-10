# test_select.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, SelectEntity

logging.basicConfig(level=logging.INFO)

class TestSelectEntity(SelectEntity):
    def __init__(self, name):
        super().__init__(name=name, options=["Option 1", "Option 2", "Option 3"])

    async def random_select_state(self):
        while True:
            state = random.choice(self.options)
            await self.log(logging.INFO, self.DOMAIN, f"Setting select {self.name} state to {state}")
            await self.set_state(state)
            await asyncio.sleep(5)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Select",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_select = TestSelectEntity(name=f"{name} Select")
    device.add_entity(test_select)

    asyncio.create_task(test_select.random_select_state())

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Test Select Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
