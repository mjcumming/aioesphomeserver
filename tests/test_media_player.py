# test_media_player.py

import asyncio
import random
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device, MediaPlayerEntity, MediaPlayerCommandRequest, MediaPlayerCommand

logging.basicConfig(level=logging.INFO)

class TestMediaPlayerEntity(MediaPlayerEntity):
    def __init__(self, name):
        super().__init__(name=name, supports_pause=True)

    async def random_media_player_command(self):
        while True:
            command = random.choice([MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PLAY, MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PAUSE, MediaPlayerCommand.MEDIA_PLAYER_COMMAND_STOP])
            await self.log(logging.INFO, self.DOMAIN, f"Setting media player {self.name} command to {command}")
            command_request = MediaPlayerCommandRequest(
                key=self.key,
                has_command=True,
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
        model="Test Media Player",
        project_name="aioesphomeserver",
        project_version="1.0.0",
        network="wifi",
        board="esp01_1m",
        platform="ESP8266"
    )

    test_media_player = TestMediaPlayerEntity(name=f"{name} Media Player")
    device.add_entity(test_media_player)

    asyncio.create_task(test_media_player.random_media_player_command())

    try:
        await device.run(api_port, web_port)
    finally:
        await device.unregister_zeroconf()

async def main():
    name, api_port, web_port = "Test Media Player Device", 6053, 8080
    await run_device(name, api_port, web_port)

if __name__ == "__main__":
    logging.info("Starting main event loop")
    asyncio.run(main())
