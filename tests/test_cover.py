"""
Test suite for the CoverEntity class with enhanced logging.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, CoverEntity, CoverCommandRequest, CoverOperation

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCoverEntity(CoverEntity):
    def __init__(self, name):
        super().__init__(name=name, supports_position=True, supports_tilt=True, supports_stop=True)
        self._target_position = self.position
        self._target_tilt = self.tilt
        self._movement_task = None
        logger.info(f"Initialized TestCoverEntity: {name}")

    async def simulate_cover_command(self, position: float, tilt: float, stop: bool = False):
        """
        Simulate a cover command for testing.
        """
        logger.info(f"Simulating cover command for {self.name}: position={position}, tilt={tilt}, stop={stop}")
        command_request = CoverCommandRequest(key=self.key, has_position=True, position=position, has_tilt=True, tilt=tilt, stop=stop)
        await self.handle(self.key, command_request)

    async def handle(self, key: int, message: CoverCommandRequest) -> None:
        """
        Override handle method to include simulation logic and logging.
        """
        logger.debug(f"Handling command for {self.name}: {message}")
        await super().handle(key, message)

        if isinstance(message, CoverCommandRequest) and message.key == self.key:
            if message.has_position:
                self._target_position = message.position
                logger.info(f"{self.name}: New target position set to {self._target_position}")
            if message.has_tilt:
                self._target_tilt = message.tilt
                logger.info(f"{self.name}: New target tilt set to {self._target_tilt}")
            if message.stop:
                self._target_position = self.position
                self._target_tilt = self.tilt
                logger.info(f"{self.name}: Stop command received. Halting at current position {self.position} and tilt {self.tilt}")

            if self._movement_task:
                self._movement_task.cancel()
            self._movement_task = asyncio.create_task(self._simulate_movement())
            logger.debug(f"{self.name}: Started movement simulation task")

    async def _simulate_movement(self):
        """
        Simulate the cover movement over time.
        """
        logger.info(f"{self.name}: Starting movement simulation")
        while self.position != self._target_position or self.tilt != self._target_tilt:
            old_position = self.position
            old_tilt = self.tilt

            if self.position != self._target_position:
                self.position += 0.1 if self._target_position > self.position else -0.1
                self.position = round(max(0, min(1, self.position)), 2)

            if self.tilt != self._target_tilt:
                self.tilt += 0.1 if self._target_tilt > self.tilt else -0.1
                self.tilt = round(max(0, min(1, self.tilt)), 2)

            if old_position != self.position or old_tilt != self.tilt:
                logger.debug(f"{self.name}: Position changed from {old_position} to {self.position}, Tilt changed from {old_tilt} to {self.tilt}")

            operation = CoverOperation.COVER_OPERATION_IS_OPENING if self._target_position > old_position or self._target_tilt > old_tilt else CoverOperation.COVER_OPERATION_IS_CLOSING
            await self.set_cover_state(self.position, self.tilt, operation)
            await asyncio.sleep(0.1)  # Simulate movement delay

        logger.info(f"{self.name}: Movement simulation completed. Final position: {self.position}, Final tilt: {self.tilt}")
        await self.set_cover_state(self.position, self.tilt, CoverOperation.COVER_OPERATION_IDLE)

    async def set_cover_state(self, position: float, tilt: float, operation: CoverOperation) -> None:
        """
        Override set_cover_state to add logging.
        """
        old_position = self.position
        old_tilt = self.tilt
        old_operation = self.current_operation

        await super().set_cover_state(position, tilt, operation)

        if old_position != position or old_tilt != tilt or old_operation != operation:
            logger.info(f"{self.name}: State updated - Position: {old_position} -> {position}, Tilt: {old_tilt} -> {tilt}, Operation: {old_operation} -> {operation}")

async def run_device(name, api_port, web_port):
    logger.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

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

    logger.info(f"Added {test_cover.name} to device {device.name}")

    # Simulate initial command
    asyncio.create_task(test_cover.simulate_cover_command(0.5, 0.3))

    # Simulate additional commands after delays
    asyncio.create_task(delayed_command(test_cover, 5, 0.8, 0.6))
    asyncio.create_task(delayed_command(test_cover, 10, 0.2, 0.1))
    asyncio.create_task(delayed_stop(test_cover, 15))

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def delayed_command(cover, delay, position, tilt):
    await asyncio.sleep(delay)
    logger.info(f"Executing delayed command: position={position}, tilt={tilt}")
    await cover.simulate_cover_command(position, tilt)

async def delayed_stop(cover, delay):
    await asyncio.sleep(delay)
    logger.info("Executing delayed stop command")
    await cover.simulate_cover_command(cover.position, cover.tilt, stop=True)

async def main():
    """
    Main entry point for setting up and running the cover device.
    """
    logger.info("Starting main function")
    await run_device("Test Cover", 6053, 8080)

if __name__ == "__main__":
    logger.info("Starting main event loop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received exit signal (Ctrl+C). Cleaning up and exiting.")
    except asyncio.CancelledError:
        logger.info("Main event loop was cancelled")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")