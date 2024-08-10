# test_text_sensor.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, TextSensorEntity

# Set up logging
logging.basicConfig(level=logging.INFO)

class TestTextSensorEntity(TextSensorEntity):
    def __init__(self, name):
        super().__init__(name=name, device_class="text")

    async def random_text_state(self):
        while True:
            state = random.choice(["Hello", "World", "ESPHome", "Test State"])
            await self.log(logging.INFO, self.DOMAIN, f"Setting text sensor {self.name} state to {state}")
            await self.set_state(state)
            await asyncio.sleep(5)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Text Sensor",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    # Add a TextSensorEntity with random state changes
    test_text_sensor = TestTextSensorEntity(name=f"{name} Text Sensor")
    device.add_entity(test_text_sensor)

    # Run the random text state functionality
    asyncio.create_task(test_text_sensor.random_text_state())

    try:
        # Run the device
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    # Define a single device
    name, api_port, web_port = "Test Text Sensor Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
