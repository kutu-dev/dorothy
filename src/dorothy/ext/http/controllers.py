from multiprocessing import Process
import time

from src.dorothy.config import ConfigSchema
from src.dorothy.models import Controller


class HttpController(Controller):
    config_schema = ConfigSchema(
        node_id="http-controller",
        node_type=Controller
    )

    def __init__(self):
        super().__init__()

    def start_controller(self) -> None:
        main_process = Process(target=self.start_api())
        main_process.start()

    def start_api(self) -> None:
        time.sleep(5)

        song = self.orchestrator.get_all_songs()[0]
        self.orchestrator.add_to_queue("main", song)
        self.orchestrator.play("main")
