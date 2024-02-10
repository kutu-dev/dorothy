from multiprocessing import Process
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
from dorothy.models import deserialize_resource_id
from dorothy.nodes import Controller, NodeInstancePath, NodeManifest
from dorothy.orchestrator import Orchestrator
from marshmallow import Schema, fields


class SongResourceId(Schema):
    song_resource_id = fields.Str(required=True)


class Song(Schema):
    resource_id = fields.Str(required=True)
    uri = fields.Str()
    title = fields.Str()


class SongList(Schema):
    songs = fields.List(fields.Nested(Song), required=True)


class Album(Schema):
    resource_id = fields.Str(required=True)
    title = fields.Str()


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

        self._rest_api_process = Process(target=self.start_rest_api_server)

    def start(self) -> None:
        self._rest_api_process.start()

    def cleanup(self) -> bool:
        self._rest_api_process.join()
        self._rest_api_process.close()

        return True

    def start_rest_api_server(self) -> None:
        port = int(self.config["port"])

        self._logger.info(f"Starting REST API server at localhost:{port}")

        app = web.Application()
        app.add_routes(
            [
                web.get("/songs", self.get_all_songs, allow_head=False),
                web.get("/songs/{song_resource_id}", self.get_song, allow_head=False),
                web.get(
                    "/channels/{channel_name}/queue", self.list_queue, allow_head=False
                ),
                web.put("/channels/{channel_name}/queue", self.add_to_queue),
                web.post("/channels/{channel_name}/play", self.play),
                web.post("/channels/{channel_name}/pause", self.pause),
                web.post("/channels/{channel_name}/play_pause", self.play_pause),
                web.post("/channels/{channel_name}/stop", self.stop),
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

        web.run_app(app, port=port, print=None)

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
        summary="List all songs in the queue",
    )
    async def list_queue(self, request: Request) -> Response:
        json_songs = [
            vars(song)
            for song in self.orchestrator.get_queue(request.match_info["channel_name"])
        ]

        return web.json_response(json_songs)

    @docs(
        tags=["channels"],
        summary="Add song to the queue",
    )
    @json_schema(SongResourceId)
    async def add_to_queue(self, request: Request) -> Response:
        data = await request.json()

        song_resource_id = deserialize_resource_id(data["song_resource_id"])
        self.orchestrator.add_to_queue(
            request.match_info["channel_name"], song_resource_id
        )

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Start the playback",
    )
    async def play(self, request: Request) -> Response:
        self._logger.info("Starting the playback")
        self.orchestrator.play(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Pause the playback",
    )
    async def pause(self, request: Request) -> Response:
        self._logger.info("Pausing the playback")
        self.orchestrator.pause(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Start or pause the playback",
    )
    async def play_pause(self, request: Request) -> Response:
        self._logger.info("Starting/pausing the playback")
        self.orchestrator.play_pause(request.match_info["channel_name"])

        return web.Response()

    @docs(
        tags=["channels"],
        summary="Stop the playback and discard the current song from the queue",
    )
    async def stop(self, request: Request) -> Response:
        self.orchestrator.stop(request.match_info["channel_name"])

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
