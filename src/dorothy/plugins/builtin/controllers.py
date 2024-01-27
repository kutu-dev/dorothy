from multiprocessing import Process

from aiohttp import web
from aiohttp.web_request import Request
from dorothy.config import ConfigSchema
from dorothy.models import Controller, Id


class RestController(Controller):
    config_schema = ConfigSchema(
        node_id="rest-controller", node_type=Controller, default_config={"port": 7171}
    )

    def __init__(self) -> None:
        super().__init__()

    def start(self) -> None:
        self.port = int(self.instance_config["port"])
        self.rest_api_process = Process(target=self.start_rest_api_server)
        self.rest_api_process.start()

    def start_rest_api_server(self) -> None:
        self.logger.info(f"Starting REST API server at localhost:{self.port}")

        self.app = web.Application()
        self.app.add_routes(
            [
                web.get("/get_all_songs", self.get_all_songs),
                web.post("/add_to_queue", self.add_to_queue),
                web.post("/play", self.play),
                web.post("/stop", self.stop),
            ]
        )

        web.run_app(self.app, port=self.port, print=False)

    async def get_all_songs(self, request: Request) -> None:
        json_songs = []
        for song in self.orchestrator.get_all_songs():
            json_songs.append(vars(song))

        return web.json_response({"songs": json_songs})

    async def add_to_queue(self, request: Request) -> None:
        data = await request.post()

        if "provider_id" not in data:
            return web.Response(status=422, reason='Missing parameter "provider_id"')

        if "item_id" not in data:
            return web.Response(status=422, reason='Missing parameter "item_id"')

        if "channel" not in data:
            return web.Response(status=422, reason='Missing parameter "channel"')

        self.orchestrator.add_to_queue(
            data["channel"], Id(data["provider_id"], data["item_id"])
        )

        return web.Response()

    async def play(self, request: Request) -> None:
        data = await request.post()

        if "channel" not in data:
            return web.Response(status=422, reason='Missing parameter "channel"')

        self.orchestrator.play(data["channel"])

        return web.Response()

    async def stop(self, request: Request) -> None:
        data = await request.post()

        if "channel" not in data:
            return web.Response(status=422, reason='Missing parameter "channel"')

        self.orchestrator.stop(data["channel"])

        return web.Response()

    def cleanup(self) -> bool:
        self.rest_api_process.terminate()
        self.rest_api_process.close()

        return True
