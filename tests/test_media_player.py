import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aioesphomeserver import Device
from aioesphomeserver.media_player import MediaPlayer, MediaPlayerSupportedFormat
from aioesphomeapi.api_pb2 import MediaPlayerState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaPlayerTestClient:
    def __init__(self, device_name, api_port, web_port):
        self.device = Device(
            name=device_name,
            mac_address=f"AC:BC:32:89:0E:{api_port:02x}",
            model="Test Media Player Device",
            project_name="aioesphomeserver",
            project_version="1.0.0"
        )
        self.api_port = api_port
        self.web_port = web_port

        supported_formats = [
            MediaPlayerSupportedFormat("mp3", 44100, 2, 0, 2),  # 0 for DEFAULT purpose
            MediaPlayerSupportedFormat("wav", 48000, 2, 1, 2)   # 1 for ANNOUNCEMENT purpose
        ]

        self.media_player = MediaPlayer(f"{device_name} Media Player", supports_pause=True, supported_formats=supported_formats)
        self.device.add_entity(self.media_player)

    async def run(self):
        device_task = asyncio.create_task(self.device.run(self.api_port, self.web_port))
        cli_task = asyncio.create_task(self.command_line_interface())

        try:
            await asyncio.gather(device_task, cli_task)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled. Shutting down...")
        finally:
            await self.device.unregister_zeroconf()

    async def command_line_interface(self):
        while True:
            command = await asyncio.get_event_loop().run_in_executor(None, input, "Enter command (play, pause, stop, mute, unmute, volume, url, state, quit): ")
            
            if command == "play":
                await self.media_player.play()
            elif command == "pause":
                await self.media_player.pause()
            elif command == "stop":
                await self.media_player.stop()
            elif command == "mute":
                await self.media_player.mute()
            elif command == "unmute":
                await self.media_player.unmute()
            elif command == "volume":
                volume = float(input("Enter volume (0.0 - 1.0): "))
                await self.media_player.set_volume(volume)
            elif command == "url":
                url = input("Enter media URL: ")
                await self.media_player.set_media_url(url)
                logger.info(f"Media URL set to: {url}")
            elif command == "state":
                state = await self.media_player.build_state_response()
                logger.info(f"Current state: {MediaPlayerState.Name(state.state)}, Volume: {state.volume}, Muted: {state.muted}")
            elif command == "quit":
                logger.info("Quitting...")
                break
            else:
                logger.warning("Unknown command")

async def main():
    client = MediaPlayerTestClient("Test Media Player", 6053, 8081)
    await client.run()

if __name__ == "__main__":
    logger.info("Starting Media Player Test Client")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)