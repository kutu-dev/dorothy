import sys
from logging import Logger

from setproctitle import setproctitle

from .config import ConfigManager
from .logging import get_logger
from .nodes import Controller
from .orchestrator import Orchestrator
from .plugin_handler import PluginHandler


def start_daemon() -> None:
    setproctitle("dorothy-daemon")

    logger = get_logger(__name__)
    config_manager = ConfigManager()
    plugin_handler = PluginHandler(config_manager)
    nodes = plugin_handler.load_nodes()

    try:
        start_mainloop(nodes.orchestrator, nodes.controllers, logger)
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


def start_mainloop(
    orchestrator: Orchestrator, controllers: list[Controller], logger: Logger
) -> None:
    for controller in controllers:
        logger.info(f'Starting controller "{controller.node_instance_path}"...')
        controller.start()

    logger.info("Starting the mainloop...")

    while True:
        orchestrator.check_if_song_finished()
