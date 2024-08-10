import asyncio
import random
import sys 
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, LightEntity, LightCommandRequest
from aioesphomeapi import LightColorCapability
import logging

class RandomDimmer(LightEntity):
    def __init__(self, name):
        super().__init__(name=name, color_modes=[LightColorCapability.BRIGHTNESS])
        self.running = True

    async def random_dimmer(self):
        while self.running:
            brightness = random.uniform(0, 1)  # Set brightness as a float between 0 and 1
            await self.log(logging.INFO, "random_dimmer", "Setting dimmer %s brightness to %.2f%%", self.name, brightness * 100)
            command = LightCommandRequest(
                key=self.key,
                has_state=True,
                state=True,
                has_brightness=True,
                brightness=brightness
            )
            await self.set_state_from_command(command)
            await asyncio.sleep(5)

    async def handle(self, key, message):
        if isinstance(message, LightCommandRequest):
            if message.key == self.key:
                await self.log(logging.INFO, "handle", "Received command for %s: %s", self.name, message)
                await self.set_state_from_command(message)

    def stop(self):
        self.running = False

async def run_device(name, api_port, web_port):
    device = Device(
        name=name,
        mac_address=f"AC:BC:32:89:0E:{api_port:02x}",
        model="Test Device",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    await device.log(logging.INFO, "setup", f"Setting up {name} with API port {api_port} and Web port {web_port}")

    # Add a LightEntity configured as a dimmer with random changes
    dimmer = RandomDimmer(name=f"{name} Dimmer")
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
    name, api_port, web_port = "Test Device", 6053, 8080
    await run_device(name, api_port, web_port)

async def shutdown(loop, signal=None):
    if signal:
        logging.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

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