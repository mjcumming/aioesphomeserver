import asyncio
import logging
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, LightEntity, LightCommandRequest
from aioesphomeapi import LightColorCapability

# Set up logging
logging.basicConfig(level=logging.INFO)

class RandomRGBLight(LightEntity):
    def __init__(self, name):
        super().__init__(name=name, color_modes=[
            LightColorCapability.RGB  # Set to use the RGB color mode
        ])

    async def random_rgb_light(self):
        while True:
            brightness = random.uniform(0, 1)  # Set brightness as a float between 0 and 1
            red = random.uniform(0, 1)  # Random red channel value
            green = random.uniform(0, 1)  # Random green channel value
            blue = random.uniform(0, 1)  # Random blue channel value

            logging.info(f"Setting light {self.name} RGB to (R: {red*255:.0f}, G: {green*255:.0f}, B: {blue*255:.0f}) with brightness {brightness * 100:.2f}%")

            command = LightCommandRequest(
                key=self.key,
                has_state=True,
                state=True,
                has_brightness=True,
                brightness=brightness,
                has_rgb=True,
                red=red,
                green=green,
                blue=blue,
                has_color_mode=True,
                color_mode=LightColorCapability.RGB  # Set color mode to RGB
            )
            await self.set_state_from_command(command)
            await asyncio.sleep(5)

    async def handle(self, key, message):
        if isinstance(message, LightCommandRequest):
            if message.key == self.key:
                logging.info(f"Received command for {self.name}: {message}")
                await self.set_state_from_command(message)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Light",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    # Add a LightEntity configured as an RGB light with random changes
    rgb_light = RandomRGBLight(name=f"{name} RGB Light")
    device.add_entity(rgb_light)

    # Run the random RGB light functionality
    asyncio.create_task(rgb_light.random_rgb_light())

    try:
        # Run the device
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    # Define a single device
    name, api_port, web_port = "Test Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
