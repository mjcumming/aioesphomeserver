"""
This module defines the MediaPlayerEntity class, which represents a media player entity in the system.
The MediaPlayerEntity class handles state management, interaction with external requests,
and entity registration within a system.
"""
# media_player.py

import json
from urllib import parse
from aiohttp import web
from . import BasicEntity, ListEntitiesMediaPlayerResponse, MediaPlayerStateResponse, MediaPlayerCommandRequest, MediaPlayerState, MediaPlayerCommand

class MediaPlayerEntity(BasicEntity):
    """
    A media player entity that handles the state of a media player and interacts with external requests.
    """

    DOMAIN = "media_player"

    def __init__(
        self,
        *args,
        supports_pause: bool = False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.supports_pause = supports_pause
        self.state = MediaPlayerState.MEDIA_PLAYER_STATE_IDLE
        self.volume = 1.0
        self.muted = False

    async def build_list_entities_response(self) -> ListEntitiesMediaPlayerResponse: # type: ignore
        return ListEntitiesMediaPlayerResponse(
            object_id=self.object_id,
            key=self.key,
            name=self.name,
            unique_id=self.unique_id,
            icon=self.icon,
            entity_category=self.entity_category,
            supports_pause=self.supports_pause,
        )

    async def build_state_response(self) -> MediaPlayerStateResponse: # type: ignore
        return MediaPlayerStateResponse(
            key=self.key,
            state=self.state,
            volume=self.volume,
            muted=self.muted,
        )

    async def state_json(self) -> str:
        data = {
            "id": self.json_id,
            "name": self.name,
            "state": self.state,
            "volume": self.volume,
            "muted": self.muted,
            "supports_pause": self.supports_pause,
        }
        return json.dumps(data)

    async def set_state(self, state: MediaPlayerState) -> None:
        self.state = state
        await self.notify_state_change()

    async def handle(self, key: int, message: MediaPlayerCommandRequest) -> None: # type: ignore
        if isinstance(message, MediaPlayerCommandRequest) and message.key == self.key:
            if message.has_command:
                if message.command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PLAY:
                    await self.set_state(MediaPlayerState.MEDIA_PLAYER_STATE_PLAYING)
                elif message.command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_PAUSE and self.supports_pause:
                    await self.set_state(MediaPlayerState.MEDIA_PLAYER_STATE_PAUSED)
                elif message.command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_STOP:
                    await self.set_state(MediaPlayerState.MEDIA_PLAYER_STATE_IDLE)
                elif message.command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_MUTE:
                    self.muted = True
                elif message.command == MediaPlayerCommand.MEDIA_PLAYER_COMMAND_UNMUTE:
                    self.muted = False

            if message.has_volume:
                self.volume = message.volume

            await self.notify_state_change()

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        router.add_route("GET", f"/media_player/{self.object_id}", self.route_get_state)

    async def route_get_state(self, request: web.Request) -> web.Response:
        data = await self.state_json()
        return web.Response(text=data)
