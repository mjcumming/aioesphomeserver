"""
Test suite for the CoverEntity class.
"""

import asyncio
import logging
from aioesphomeserver import Device, CoverEntity, CoverCommandRequest

logging.basicConfig(level=logging.INFO)

class TestCoverEntity(CoverEntity):
    def __init__(self, name):
        super().__init__(name=name, supports_position=True, supports_tilt=True, supports_stop=True)

    async def simulate_cover_command(self, position: float, tilt: float, stop: bool = False):
        """
        Simulate a cover command for testing.
        """
        await self.log(logging.INFO, self.DOMAIN, f"Simulating cover command for {self.name}: position={position}, tilt={tilt}, stop={stop}")
        command_request = CoverCommandRequest(key=self.key, has_position=True, position=position, has_tilt=True, tilt=tilt, stop=stop)
        await self.handle(self.key, command_request)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Cover",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_cover = TestCoverEntity(name=f"{name} Cover")
    device.add_entity(test_cover)

    asyncio.create_task(test_cover.simulate_cover_command(0.5, 0.3))

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    """
    Main entry point for setting up and running the cover device.
    """
    await run_device("Test Cover", 6053, 8080)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logging.info("Main event loop was cancelled")
