from multiprocessing import Process
from typing import Any

from aiohttp import web

# Be aware that these types are not exported
# by the __init__.py file of the package
from aiohttp.web_request import FileField, Request
from aiohttp.web_response import Response
from dorothy.models import deserialize_resource_id
from dorothy.nodes import Controller, NodeInstancePath, NodeManifest
from dorothy.orchestrator import Orchestrator
from multidict import MultiDictProxy


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
        self._logger = self.get_logger()
        self._port = int(self.config["port"])
        self._rest_api_process = Process(target=self.start_rest_api_server)

    def start(self) -> None:
        self._rest_api_process.start()

    def cleanup(self) -> bool:
        self._rest_api_process.join()
        self._rest_api_process.close()

        return True

    def start_rest_api_server(self) -> None:
        self._logger.info(f"Starting REST API server at localhost:{self._port}")

        self.app = web.Application()
        self.app.add_routes(
            [
                web.get("/songs", self.get_all_songs),
                web.get("/songs/{song_resource_id}", self.get_song),
                web.put("/channels/{channel_name}/queue", self.add_to_queue),
                web.post("/channels/{channel_name}/play", self.play),
                web.post("/channels/{channel_name}/stop", self.stop),
            ]
        )

        web.run_app(self.app, port=self._port, print=None)

    def valid_parameter(
        self, data: MultiDictProxy[str | bytes | FileField], key: str
    ) -> tuple[str, Response | None]:
        if key not in data:
            return "", web.Response(status=422, reason=f'Missing parameter "{key}"')

        if isinstance(data[key], str):
            return "", web.Response(
                status=422,
                reason=f'Parameter "{key}" has an invalid'
                + f'type "{type(data[key])}" instead of "str"',
            )

        # Cast it to str because Mypy can't see that it will always be a string
        return str(data[key]), None

    async def get_all_songs(self, request: Request) -> Response:
        json_songs = []
        for song in self.orchestrator.get_all_songs():
            json_songs.append(vars(song))

        return web.json_response({"songs": json_songs})

    async def get_song(self, request: Request) -> Response:
        resource_id = deserialize_resource_id(request.match_info["song_resource_id"])

        return web.json_response(vars(self.orchestrator.get_song(resource_id)))

    async def add_to_queue(self, request: Request) -> Response:
        data = await request.post()

        song_resource_id, error = self.valid_parameter(data, "song_resource_id")
        if error is not None:
            return error

        resource_id = deserialize_resource_id(song_resource_id)
        self.orchestrator.add_to_queue(request.match_info["channel_name"], resource_id)

        return web.Response()

    async def play(self, request: Request) -> Response:
        self.orchestrator.play(request.match_info["channel_name"])

        return web.Response()

    async def stop(self, request: Request) -> Response:
        self.orchestrator.stop(request.match_info["channel_name"])

        return web.Response()
