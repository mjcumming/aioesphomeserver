# test_fan.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, FanEntity, FanCommandRequest

# Set up logging
logging.basicConfig(level=logging.INFO)

class TestFanEntity(FanEntity):
    def __init__(self, name):
        super().__init__(
            name=name,
            supports_oscillation=True,
            supports_speed=True,
            supports_direction=True,
            supported_speed_levels=3,
            supported_preset_modes=["Normal", "Sleep"]
        )

    async def random_fan_state(self):
        while True:
            state = random.choice([True, False])
            oscillating = random.choice([True, False])
            speed_level = random.randint(1, 3)
            direction = random.choice([0, 1])
            preset_mode = random.choice(["Normal", "Sleep"])

            await self.log(logging.INFO, self.DOMAIN, f"Setting fan {self.name} state to {state}, oscillating: {oscillating}, speed_level: {speed_level}, direction: {direction}, preset_mode: {preset_mode}")

            command = FanCommandRequest(
                key=self.key,
                has_state=True,
                state=state,
                has_oscillating=True,
                oscillating=oscillating,
                has_speed_level=True,
                speed_level=speed_level,
                has_direction=True,
                direction=direction,
                has_preset_mode=True,
                preset_mode=preset_mode
            )
            await self.set_state_from_command(command)
            await asyncio.sleep(5)

    async def handle(self, key, message):
        if isinstance(message, FanCommandRequest):
            if message.key == self.key:
                await self.log(logging.INFO, self.DOMAIN, f"Received command for {self.name}: {message}")
                await self.set_state_from_command(message)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Fan",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    # Add a FanEntity with random state changes
    test_fan = TestFanEntity(name=f"{name} Fan")
    device.add_entity(test_fan)

    # Run the random fan state functionality
    asyncio.create_task(test_fan.random_fan_state())

    try:
        # Run the device
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    # Define a single device
    name, api_port, web_port = "Test Fan Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
