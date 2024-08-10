# test_lock.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, LockEntity, LockCommandRequest, LockCommand

logging.basicConfig(level=logging.INFO)

class TestLockEntity(LockEntity):
    def __init__(self, name):
        super().__init__(
            name=name,
            supports_open=True,
            requires_code=False,
        )

    async def random_lock_state(self):
        while True:
            command = random.choice([LockCommand.LOCK_LOCK, LockCommand.LOCK_UNLOCK, LockCommand.LOCK_OPEN])
            await self.log(logging.INFO, self.DOMAIN, f"Setting lock {self.name} command to {command}")
            command_request = LockCommandRequest(
                key=self.key,
                command=command
            )
            await self.handle(self.key, command_request)
            await asyncio.sleep(5)

async def run_device(name, api_port, web_port):
    logging.info(f"Setting up {name} with API port {api_port} and Web port {web_port}")

    mac_address = f"AC:BC:32:89:0E:{api_port:02x}"

    device = Device(
        name=name,
        mac_address=mac_address,
        model="Test Lock",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_lock = TestLockEntity(name=f"{name} Lock")
    device.add_entity(test_lock)

    asyncio.create_task(test_lock.random_lock_state())

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Test Lock Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
