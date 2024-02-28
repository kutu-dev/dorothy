import asyncio
import sys
from setproctitle import setproctitle

from .config import ConfigManager
from .logging import get_logger
from .nodes import Controller
from .orchestrator import Orchestrator
from .plugin_handler import PluginHandler


async def mainloop(orchestrator: Orchestrator, controllers: list[Controller]):
    controller_start_functions = [controller.start() for controller in controllers]
    await asyncio.gather(*controller_start_functions)

    while True:
        orchestrator.check_if_song_finished()
        await asyncio.sleep(0.5)


def start_daemon() -> None:
    setproctitle("dorothy-daemon")

    logger = get_logger(__name__)
    config_manager = ConfigManager()
    plugin_handler = PluginHandler(config_manager)
    nodes = plugin_handler.load_nodes()

    try:
        logger.info("Starting the mainloop...")
        asyncio.run(mainloop(nodes.orchestrator, nodes.controllers))
    except KeyboardInterrupt:
        pass
    finally:
        nodes.orchestrator.cleanup_nodes()

        for controller in nodes.controllers:
            if not controller.cleanup():
                logger.warning(
                    f'Controller "{controller.node_instance_path}" has failed cleanup!'
                )

    sys.exit()
