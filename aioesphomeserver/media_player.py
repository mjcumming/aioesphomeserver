from typing import List, Optional
import json
from aiohttp import web

# Third-party imports
from aioesphomeapi.api_pb2 import MediaPlayerState, MediaPlayerCommand

# Local imports
from . import BasicEntity, ListEntitiesMediaPlayerResponse, MediaPlayerStateResponse, MediaPlayerCommandRequest

class MediaPlayerSupportedFormat:
    def __init__(self, format: str, sample_rate: int, num_channels: int, purpose: int, sample_bytes: int):
        self.format = format
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.purpose = purpose
        self.sample_bytes = sample_bytes

class MediaPlayer(BasicEntity):
    DOMAIN = "media_player"

    def __init__(self, name: str, supports_pause: bool = True, supported_formats: List[MediaPlayerSupportedFormat] = None, **kwargs):
        super().__init__(name, **kwargs)
        self.supports_pause = supports_pause
        self.supported_formats = supported_formats or []
        self._state = MediaPlayerState.MEDIA_PLAYER_STATE_IDLE
        self._volume = 0.5
        self._muted = False
        self._media_url: Optional[str] = None

    async def build_list_entities_response(self):
        return ListEntitiesMediaPlayerResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            disabled_by_default=False,
            entity_category=self.entity_category,
            supports_pause=self.supports_pause,
            supported_formats=[
                {
                    "format": fmt.format,
                    "sample_rate": fmt.sample_rate,
                    "num_channels": fmt.num_channels,
                    "purpose": fmt.purpose,
                    "sample_bytes": fmt.sample_bytes
                } for fmt in self.supported_formats
            ]
        )

    async def build_state_response(self):
        return MediaPlayerStateResponse(
            key=self.key,
            state=self._state,
            volume=self._volume,
            muted=self._muted
        )

    async def handle(self, key, message):
        if isinstance(message, MediaPlayerCommandRequest) and message.key == self.key:
            if message.has_command:
                await self._handle_command(message.command)
            if message.has_volume:
                await self.set_volume(message.volume)
            if message.has_media_url:
                await self.set_media_url(message.media_url)
            if message.has_announcement:
                await self.handle_announcement(message.announcement)
            await self.notify_state_change()

    async def _handle_command(self, command: MediaPlayerCommand):
        if command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PLAY:
            self._state = MediaPlayerState.MEDIA_PLAYER_STATE_PLAYING
        elif command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PAUSE and self.supports_pause:
            self._state = MediaPlayerState.MEDIA_PLAYER_STATE_PAUSED
        elif command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_STOP:
            self._state = MediaPlayerState.MEDIA_PLAYER_STATE_IDLE
        elif command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_MUTE:
            self._muted = True
        elif command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_UNMUTE:
            self._muted = False

    async def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))

    async def set_media_url(self, url: str):
        self._media_url = url
        self._state = MediaPlayerState.MEDIA_PLAYER_STATE_PLAYING

    async def handle_announcement(self, is_announcement: bool):
        # Implement announcement handling logic here
        pass

    # Additional methods for controlling the media player
    async def play(self):
        await self._handle_command(MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PLAY)
        await self.notify_state_change()

    async def pause(self):
        if self.supports_pause:
            await self._handle_command(MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PAUSE)
            await self.notify_state_change()

    async def stop(self):
        await self._handle_command(MediaPlayerCommand.MEDIA_PLAYER_COMMAND_STOP)
        await self.notify_state_change()

    async def mute(self):
        await self._handle_command(MediaPlayerCommand.MEDIA_PLAYER_COMMAND_MUTE)
        await self.notify_state_change()

    async def unmute(self):
        await self._handle_command(MediaPlayerCommand.MEDIA_PLAYER_COMMAND_UNMUTE)
        await self.notify_state_change()

    # Implement the required abstract methods
    async def add_routes(self, router: web.UrlDispatcher):
        router.add_route("GET", f"/media_player/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request):
        data = await self.state_json()
        return web.Response(text=data)

    async def state_json(self):
        state = await self.build_state_response()
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": MediaPlayerState.Name(state.state),
            "volume": state.volume,
            "muted": state.muted,
            "media_url": self._media_url
        }
        return json.dumps(data)