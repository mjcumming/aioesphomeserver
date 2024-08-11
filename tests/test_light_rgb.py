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

            logging.info("Setting light %s RGB to (R: %.0f, G: %.0f, B: %.0f) with brightness %.2f%%", self.name, red*255, green*255, blue*255, brightness * 100)
            await self.set_state_from_command(command)
            await asyncio.sleep(5)

    async def handle(self, key, message):
        if isinstance(message, LightCommandRequest):
            if message.key == self.key:
                logging.info("Received command for %s: %s", self.name, message)
                await self.set_state_from_command(message)

async def run_device(name, api_port, web_port):
    device = Device(
        name=name,
        mac_address=f"AC:BC:32:89:0E:{api_port:02x}",
        model="Test Dimmer",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    await device.log(logging.INFO, "setup", f"Setting up {name} with API port {api_port} and Web port {web_port}")

    # Add a LightEntity configured as a dimmer with random changes
    dimmer = RandomRGBLight(name=f"{name} Dimmer")
    device.add_entity(dimmer)

    # Run the random dimmer functionality
    dimmer_task = asyncio.create_task(dimmer.random_dimmer())

    try:
        # Run the device
        await device.run(api_port, web_port)
    except asyncio.CancelledError:
        await device.log(logging.INFO, "shutdown", "Shutting down device")
    finally:
        dimmer.stop()
        await dimmer_task
        await device.unregister_zeroconf()

async def main():
    # Define a single device
    name, api_port, web_port = "Test Light RGB", 6053, 8080
    await run_device(name, api_port, web_port)

async def shutdown(event_loop, signal=None):
    if signal:
        logging.info("Received exit signal %s...", signal.name)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    cancel_tasks = [task.cancel() for task in tasks]
    await asyncio.gather(*cancel_tasks, return_exceptions=True)
    event_loop.stop()

if __name__ == "__main__":
    # Set up basic logging configuration
    logging.basicConfig(level=logging.INFO)
    
    # Log the start of the main event loop using standard logging
    logging.info("Starting main event loop")
    
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Shutting down...")
    finally:
        loop.run_until_complete(shutdown(loop))
        loop.close()
        logging.info("Shutdown complete.")