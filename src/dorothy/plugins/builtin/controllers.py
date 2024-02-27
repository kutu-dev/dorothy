import asyncio
import logging
from multiprocessing import Process, set_start_method
from threading import Thread
from typing import Any

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp_apispec import (
    docs,
    json_schema,
    response_schema,
    setup_aiohttp_apispec,
    validation_middleware,
)

from dorothy.logging import get_logger
from dorothy.models import deserialize_resource_id
from dorothy.nodes import Controller, NodeInstancePath, NodeManifest
from dorothy.orchestrator import Orchestrator
from marshmallow import Schema, fields


class ResourceId(Schema):
    resource_id = fields.Str(required=True)


class Song(Schema):
    resource_id = fields.Str(required=True)
    uri = fields.Str()
    title = fields.Str()


class SongList(Schema):
    songs = fields.List(fields.Nested(Song), required=True)


class ChannelList(Schema):
    channels = fields.List(fields.Str(), required=True)


class Album(Schema):
    resource_id = fields.Str(required=True)
    title = fields.Str()
    number_of_songs = fields.Int(required=True)


class AlbumList(Schema):
    albums = fields.List(fields.Nested(Album), required=True)


class RestController(Controller):
    @classmethod
    def get_node_manifest(cls) -> NodeManifest:
        return NodeManifest(node_name="rest", default_config={"port": 6969})

    def __init__(
        self,
        config: dict[str, Any],
        node_instance_path: NodeInstancePath,
        orchestrator: Orchestrator,
    ) -> None:
        super().__init__(config, node_instance_path, orchestrator)

        self.port = int(self.config["port"])
        runner = self.get_app_runner()

        self._rest_api_thread = Thread(target=self.run_server, args=(runner,))

    def start(self) -> None:
        self.logger().info(f"Starting REST API server at localhost:{self.port}")
        self._rest_api_thread.start()

    def cleanup(self) -> bool:
        self._rest_api_thread.join()

        return True

    def get_app_runner(self):
        app = web.Application()
        app.add_routes(
            [
                web.get("/songs", self.get_all_songs, allow_head=False),
                web.get("/songs/{song_resource_id}", self.get_song, allow_head=False),
                web.get(
                    "/channels/{channel_name}/queue", self.list_queue, allow_head=False
                ),
                web.get("/channels", self.get_all_channels, allow_head=False),
                web.get("/channels/{channel_name}", self.get_channel_state, allow_head=False),
                web.put("/channels/{channel_name}/queue", self.add_to_queue),
                web.put(
                    "/channels/{channel_name}/queue/{position}", self.insert_to_queue
                ),
                web.delete(
                    "/channels/{channel_name}/queue/{position}", self.delete_from_queue
                ),
                web.post(
                    "/channels/{channel_name}/queue/{position}/play",
                    self.play_from_queue_given_index,
                ),
                web.post("/channels/{channel_name}/play", self.play),
                web.post("/channels/{channel_name}/pause", self.pause),
                web.post("/channels/{channel_name}/play_pause", self.play_pause),
                web.post("/channels/{channel_name}/stop", self.stop),
                web.post("/channels/{channel_name}/skip", self.skip),
                web.get("/albums", self.get_all_albums, allow_head=False),
                web.get(
                    "/albums/{album_resource_id}", self.get_album, allow_head=False
                ),
                web.get(
                    "/albums/{album_resource_id}/songs",
                    self.get_songs_from_album,
                    allow_head=False,
                ),
            ]
        )

        setup_aiohttp_apispec(
            app=app,
            title="Dorothy REST API Server",
            version="v1",
            url="/api/docs/swagger.json",
            swagger_path="/api/docs",
            in_place=True,
        )

        app.middlewares.append(validation_middleware)

        #web.run_app(app, port=port, print=None)
        return web.AppRunner(app)

    def run_server(self, runner):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, 'localhost', self.port)
        loop.run_until_complete(site.start())
        loop.run_forever()

    def get_channel_state_dict(self, channel_name: str) -> dict[str, Any]:
        current_song = self.orchestrator.get_current_song(channel_name)
        parsed_current_song = vars(current_song) if current_song is not None else None

        return {"current_song": parsed_current_song, "player_state": self.orchestrator.get_channel_state(channel_name).value}

    @docs(
        tags=["songs"],
        summary="Get all songs registered by the providers",
    )
    @response_schema(SongList, 200)
    async def get_all_songs(self, request: Request) -> Response:
        json_songs = []
        for song in self.orchestrator.get_all_songs():
            json_songs.append(vars(song))

        return web.json_response({"songs": json_songs})

    @docs(
        tags=["songs"],
        summary="Get all data of a song",
    )
    @response_schema(Song, 200)
    async def get_song(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["song_resource_id"])

        return web.json_response(vars(self.orchestrator.get_song(resource_id)))

    @docs(
        tags=["channels"],
        summary="Get all channels available",
    )
    @response_schema(ChannelList, 200)
    async def get_all_channels(self, request: Request) -> Response:
        return web.json_response({"channels": list(self.orchestrator.channels.keys())})

    @docs(
        tags=["channels"],
        summary="List all songs in the queue",
    )
    async def list_queue(self, request: Request) -> Response:
        json_songs = [
            vars(song)
            for song in self.orchestrator.get_queue(request.match_info["channel_name"])
        ]

        return web.json_response({"songs": json_songs})

    @docs(
        tags=["channels"],
        summary="Get all the relevant information about the current state of a channel",
    )
    async def get_channel_state(self, request: Request) -> Response:
        return web.json_response(self.get_channel_state_dict(request.match_info["channel_name"]))

    @docs(
        tags=["channels"],
        summary="Add song or album to the queue at the end",
    )
    @json_schema(ResourceId)
    async def add_to_queue(self, request: Request) -> Response:
        data = await request.json()

        resource_id = deserialize_resource_id(data["resource_id"])
        self.orchestrator.add_to_queue(request.match_info["channel_name"], resource_id)

        return web.Response()

    @docs(
        tags=["channels"],
        summary='Add song or album to the queue at the position specified by "{position}" ',
    )
    @json_schema(ResourceId)
    async def insert_to_queue(self, request: Request) -> Response:
        data = await request.json()

        if not request.match_info["position"].isdigit():
            return web.Response(status=422, text="The position must be an integer")

        position = int(request.match_info["position"])

        resource_id = deserialize_resource_id(data["resource_id"])
        self.orchestrator.insert_to_queue(
            request.match_info["channel_name"], resource_id, position
        )

        return web.Response()

    @docs(
        tags=["channels"],
        summary='Remove songs from the queue at the position specified by "{position}" ',
    )
    async def delete_from_queue(self, request: Request) -> Response:
        if not request.match_info["position"].isdigit():
            return web.Response(status=422, text="The position must be an integer")

        position = int(request.match_info["position"])

        self.orchestrator.remove_from_queue(
            request.match_info["channel_name"], position
        )

        return web.Response()

    @docs(
        tags=["channels"],
        summary='Start playing the song from the queue at the position specified by "{position}" ',
    )
    async def play_from_queue_given_index(self, request: Request) -> Response:
        if not request.match_info["position"].isdigit():
            return web.Response(status=422, text="The position must be an integer")

        position = int(request.match_info["position"])

        self.orchestrator.play_from_queue_given_index(
            request.match_info["channel_name"], position
        )

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Start the playback",
    )
    async def play(self, request: Request) -> Response:
        self.logger().info("Starting the playback")
        self.orchestrator.play(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Pause the playback",
    )
    async def pause(self, request: Request) -> Response:
        self.logger().info("Pausing the playback")
        self.orchestrator.pause(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Start or pause the playback",
    )
    async def play_pause(self, request: Request) -> Response:
        self.logger().info("Start/pause the playback")
        queue_changed = self.orchestrator.play_pause(request.match_info["channel_name"])

        return web.json_response({**self.get_channel_state_dict(request.match_info["channel_name"]), "queue_changed": queue_changed})

    @docs(
        tags=["channels"],
        summary="Stop the playback and discard the current song from the queue",
    )
    async def stop(self, request: Request) -> Response:
        self.orchestrator.stop(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Skip the current playing song from the queue and starts playing the next one if there's any",
    )
    async def skip(self, request: Request) -> Response:
        self.orchestrator.skip(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["albums"],
        summary="Get all albums registered by the providers",
    )
    @response_schema(AlbumList, 200)
    async def get_all_albums(self, request: Request) -> Response:
        json_albums = []
        for album in self.orchestrator.get_all_albums():
            json_albums.append(vars(album))

        return web.json_response({"albums": json_albums})

    @docs(
        tags=["albums"],
        summary="Get all data of a album",
    )
    @response_schema(Album, 200)
    async def get_album(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["album_resource_id"])

        return web.json_response(vars(self.orchestrator.get_album(resource_id)))

    @docs(
        tags=["albums"],
        summary="Get all songs from an album",
    )
    @response_schema(SongList, 200)
    async def get_songs_from_album(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["album_resource_id"])

        json_songs = [
            vars(song) for song in self.orchestrator.get_songs_from_album(resource_id)
        ]

        return web.json_response({"songs": json_songs})
