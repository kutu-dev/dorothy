from multiprocessing import Process
from typing import Any

from aiohttp import web

# Be aware that these types are not exported
# by the __init__.py file of the package
from aiohttp.web_request import FileField, Request
from aiohttp.web_response import Response
from dorothy.nodes import Controller, NodeInstancePath, NodeManifest
from multidict import MultiDictProxy

from dorothy.orchestrator import Orchestrator


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
                web.get("/get_all_songs", self.get_all_songs),
                web.post("/add_to_queue", self.add_to_queue),
                web.post("/play", self.play),
                web.post("/stop", self.stop),
            ]
        )

        web.run_app(self.app, port=self._port, print=None)

    def valid_parameter(
        self, data: MultiDictProxy[str | bytes | FileField], key: str
    ) -> Response | str:
        if key not in data:
            return web.Response(status=422, reason=f'Missing parameter "{key}"')

        if type(data[key]) is not str:
            return web.Response(
                status=422,
                reason=f'Parameter "{key}" has an invalid type "{type(data[key])}" instead of "str"',
            )

        # Avoid Mypy not seeing that this will always be a string
        return str(data[key])

    async def get_all_songs(self, request: Request) -> Response:
        json_songs = []
        for song in self.orchestrator.get_all_songs():
            json_songs.append(vars(song))

        return web.json_response({"songs": json_songs})

    async def add_to_queue(self, request: Request) -> Response:
        data = await request.post()

        provider_id = self.valid_parameter(data, "provider_id")
        if type(provider_id) is Response:
            return provider_id

        item_id = self.valid_parameter(data, "item_id")
        if type(item_id) is Response:
            return item_id

        channel = self.valid_parameter(data, "channel")
        if type(channel) is Response:
            return channel

        self.orchestrator.add_to_queue(str(channel), Id(str(provider_id), str(item_id)))

        return web.Response()

    async def play(self, request: Request) -> Response:
        data = await request.post()

        channel = self.valid_parameter(data, "channel")
        if type(channel) is Response:
            return channel

        self.orchestrator.play(str(channel))

        return web.Response()

    async def stop(self, request: Request) -> Response:
        data = await request.post()

        channel = self.valid_parameter(data, "channel")
        if type(channel) is Response:
            return channel

        self.orchestrator.stop(str(channel))

        return web.Response()
