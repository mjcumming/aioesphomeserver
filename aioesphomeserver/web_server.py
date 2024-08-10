"""
This module defines the WebServer class, which serves as a web server entity
for handling HTTP requests and streaming server-sent events (SSE).

Classes:
    - WebServer: A class that represents a web server entity capable of
      handling HTTP requests and streaming SSE events.
"""

import asyncio
import os
from aiohttp import web
from aiohttp_sse import sse_response
from .basic_entity import BasicEntity

class WebServer(BasicEntity):
    """
    Represents a web server entity that handles HTTP requests and streams server-sent events (SSE).

    Attributes:
        port (int): The port on which the web server listens.
        queue (asyncio.Queue): A queue for managing events to be sent to clients via SSE.
    """

    DOMAIN = "web_server"

    def __init__(self, *args, port=8080, **kwargs):
        """
        Initialize a WebServer instance.

        Args:
            port (int): The port on which the web server listens. Defaults to 8080.
        """
        super().__init__(*args, **kwargs)
        self.port = port
        self.queue = asyncio.Queue()

    async def index(self, _request: web.Request) -> web.FileResponse:
        """
        Handle requests for the index page.

        Args:
            _request (web.Request): The incoming HTTP request.

        Returns:
            web.FileResponse: The response serving the index.html file.
        """
        return web.FileResponse(
            path=os.path.dirname(__file__) + '/index.html'
        )

    async def handle(self, key: str, message: dict) -> None:
        """
        Handle internal messages related to state changes or logs.

        Args:
            key (str): The key indicating the type of message.
            message (dict): The message data.
        """
        if key == "state_change":
            key = message.key
            entity = self.device.get_entity_by_key(key)
            data = await entity.state_json()
            await self.queue.put(("state", data))

        if key == "log":
            await self.queue.put(("log", message))

    async def events(self, request: web.Request) -> web.StreamResponse:
        """
        Handle SSE requests for real-time events.

        Args:
            request (web.Request): The incoming HTTP request for SSE.

        Returns:
            web.StreamResponse: The response streaming events to the client.
        """
        async with sse_response(request) as resp:
            for entity in self.device.entities:
                data = await entity.state_json()
                if data is not None:
                    await resp.send(data, event="state")

            while resp.is_connected():
                event, data = await self.queue.get()
                if event == "log":
                    data = data[1]

                try:
                    await resp.send(data, event=event)
                except ConnectionResetError:
                    break

        return resp

    async def run(self) -> None:
        """
        Start the web server and begin handling requests.

        This method sets up the web server, adds routes, and begins listening on the specified port.
        """
        app = web.Application()
        app.router.add_route("GET", "/events", self.events)
        app.router.add_route("GET", "/", self.index)

        for entity in self.device.entities:
            await entity.add_routes(app.router)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await self.device.log(2, "web", f"Starting web server on port {self.port}!")

        await site.start()

        while True:
            await asyncio.sleep(1)
            await self.queue.put(("ping", ""))

    async def build_list_entities_response(self) -> None:
        """
        Build the response for listing entities. This method should be overridden by subclasses.
        """
        return None

    async def build_state_response(self) -> None:
        """
        Build the state response for this entity. This method should be overridden by subclasses.
        """
        return None

    async def state_json(self) -> str:
        """
        Generate a JSON representation of the entity's state. This method should be overridden by subclasses.

        Returns:
            str: A JSON string representing the entity's state.
        """
        return "{}"

    async def add_routes(self, router: web.UrlDispatcher) -> None:
        """
        Add routes for this entity to a router.

        Args:
            router (web.UrlDispatcher): The router to which routes should be added.
        """
        router.add_route("GET", f"/{self.object_id}", self.index)
