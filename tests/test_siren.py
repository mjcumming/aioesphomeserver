# test_siren.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, SirenEntity, SirenCommandRequest

logging.basicConfig(level=logging.INFO)

class TestSirenEntity(SirenEntity):
    def __init__(self, name):
        super().__init__(
            name=name,
            tones=["Tone 1", "Tone 2", "Tone 3"],
            supports_duration=True,
            supports_volume=True,
        )

    async def random_siren_state(self):
        while True:
            state = random.choice([True, False])
            await self.log(logging.INFO, self.DOMAIN, f"Setting siren {self.name} state to {state}")
            await self.set_state(state)
            await asyncio.sleep(5)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Siren",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_siren = TestSirenEntity(name=f"{name} Siren")
    device.add_entity(test_siren)

    asyncio.create_task(test_siren.random_siren_state())

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Test Siren Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
