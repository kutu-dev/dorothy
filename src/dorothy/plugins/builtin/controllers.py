import asyncio
import logging
import time
from multiprocessing import Process, set_start_method, Queue
from threading import Thread
from typing import Any

import aiohttp.web
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
from dorothy.deserializers import deserialize_resource_id
from dorothy.nodes import Controller, NodeInstancePath, NodeManifest
from dorothy.orchestrator import Orchestrator
from marshmallow import Schema, fields


class ResourceId(Schema):
    resource_id = fields.Str(required=True)


class SongSchema(Schema):
    resource_id = fields.Str()
    uri = fields.Str()
    duration = fields.Int()
    title = fields.Str()
    album_name = fields.Str()
    artist_name = fields.Str()


class SongList(Schema):
    songs = fields.List(fields.Nested(SongSchema()))


class ChannelList(Schema):
    channels = fields.List(fields.Str())


class AlbumSchema(Schema):
    resource_id = fields.Str()
    title = fields.Str()
    song_list = fields.List(fields.Nested(SongSchema()))


class AlbumList(Schema):
    albums = fields.List(fields.Nested(AlbumSchema()))


class ChannelState(Schema):
    current_song = fields.Str()
    player_state = fields.Str()


class RestController(Controller):
    @classmethod
    def get_node_manifest(cls) -> NodeManifest:
        return NodeManifest(name="rest", default_config={"port": 6969})

    def __init__(
        self,
        config: dict[str, Any],
        node_instance_path: NodeInstancePath,
        orchestrator: Orchestrator,
    ) -> None:
        super().__init__(config, node_instance_path, orchestrator)

        self.port = int(self.config["port"])
        app = self.get_web_app()
        self.runner = web.AppRunner(app)

    async def start(self) -> None:
        self.logger().info(f"Starting REST API server at localhost:{self.port}")

        await self.runner.setup()
        site = web.TCPSite(self.runner, "localhost", self.port)
        await site.start()

    async def cleanup(self) -> bool:
        # TODO NOT WAITED
        self.runner.cleanup()
        return True

    def get_web_app(self) -> aiohttp.web.Application:
        app = web.Application()
        app.add_routes(
            [
                web.get("/songs", self.get_all_songs, allow_head=False),
                web.get("/songs/{song_resource_id}", self.get_song, allow_head=False),
                web.get(
                    "/channels/{channel_name}/queue", self.list_queue, allow_head=False
                ),
                web.get("/channels", self.get_all_channels, allow_head=False),
                web.get(
                    "/channels/{channel_name}", self.get_channel_state, allow_head=False
                ),
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

        # web.run_app(app, port=self.port, print=None)
        return app

    def get_channel_state_dict(self, channel_name: str) -> dict[str, Any]:
        current_song = self.orchestrator.get_current_song(channel_name)
        parsed_current_song = current_song.dict() if current_song is not None else None

        return {
            "current_song": parsed_current_song,
            "player_state": self.orchestrator.get_channel_state(channel_name).value,
        }

    @docs(
        tags=["songs"],
        summary="Get all songs registered by the providers",
    )
    @response_schema(
        SongList, 200, description="List of all songs registered by the providers"
    )
    async def get_all_songs(self, request: Request) -> Response:
        json_songs = []
        for song in self.orchestrator.get_all_songs():
            json_songs.append(song.dict())

        return web.json_response({"songs": json_songs})

    @docs(
        tags=["songs"],
        summary="Get all data of a song",
    )
    @response_schema(SongSchema, 200, description="All the data of the requested song")
    async def get_song(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["song_resource_id"])

        return web.json_response(self.orchestrator.get_song(resource_id).dict())

    @docs(
        tags=["channels"],
        summary="Get all channels available",
    )
    @response_schema(ChannelList, 200, description="The available channels names")
    async def get_all_channels(self, request: Request) -> Response:
        return web.json_response({"channels": list(self.orchestrator.channels.keys())})

    @docs(
        tags=["channels"],
        summary="List all songs in the queue",
    )
    @response_schema(SongList, 200, description="All the songs in the queue")
    async def list_queue(self, request: Request) -> Response:
        json_songs = [
            song.dict()
            for song in self.orchestrator.get_queue(request.match_info["channel_name"])
        ]

        return web.json_response({"songs": json_songs})

    @docs(
        tags=["channels"],
        summary="Get all the relevant information about the current state of a channel",
    )
    @response_schema(
        ChannelState,
        200,
        description='The state of the requested channel. "player_state" can be "PLAYING", "PAUSED" or "STOPPED".',
    )
    async def get_channel_state(self, request: Request) -> Response:
        return web.json_response(
            self.get_channel_state_dict(request.match_info["channel_name"])
        )

    @docs(
        tags=["channels"],
        summary="Add song or album to the queue at the end",
        responses={
            200: {"description": "Song or album successfully added to the queue"}
        },
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
        responses={
            200: {"description": "Song or album successfully inserted to the queue"}
        },
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
        responses={200: {"description": "Song successfully removed from the queue"}},
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
        responses={200: {"description": "Start playing the requested song"}},
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
        responses={200: {"description": "Playback started"}},
    )
    async def play(self, request: Request) -> Response:
        self.logger().info("Starting the playback")
        self.orchestrator.play(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Pause the playback",
        responses={200: {"description": "Playback paused"}},
    )
    async def pause(self, request: Request) -> Response:
        self.logger().info("Pausing the playback")
        self.orchestrator.pause(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Start or pause the playback",
    )
    @response_schema(
        ChannelState,
        200,
        description='The state of the requested channel. "player_state" can be "PLAYING", "PAUSED" or "STOPPED".',
    )
    async def play_pause(self, request: Request) -> Response:
        self.logger().info("Start/pause the playback")
        queue_changed = self.orchestrator.play_pause(request.match_info["channel_name"])

        return web.json_response(
            {
                **self.get_channel_state_dict(request.match_info["channel_name"]),
                "queue_changed": queue_changed,
            }
        )

    @docs(
        tags=["channels"],
        summary="Stop the playback and discard the current song from the queue",
        responses={200: {"description": "Successfully stop the playback"}},
    )
    async def stop(self, request: Request) -> Response:
        self.orchestrator.stop(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Skip the current playing song from the queue and starts playing the next one if there's any",
        responses={200: {"description": "Succesfully skip the current song"}},
    )
    async def skip(self, request: Request) -> Response:
        self.orchestrator.skip(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["albums"],
        summary="Get all albums registered by the providers",
    )
    @response_schema(
        AlbumList, 200, description="The list of albums registered by the providers"
    )
    async def get_all_albums(self, request: Request) -> Response:
        json_albums = []
        for album in self.orchestrator.get_all_albums():
            json_albums.append(album.dict())

        return web.json_response({"albums": json_albums})

    @docs(
        tags=["albums"],
        summary="Get all data of a album",
    )
    @response_schema(
        AlbumSchema, 200, description="All the data of the requested album"
    )
    async def get_album(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["album_resource_id"])

        return web.json_response(self.orchestrator.get_album(resource_id).dict())
