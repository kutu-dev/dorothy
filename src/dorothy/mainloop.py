import asyncio
from logging import getLogger

from .config import ConfigManager
from .plugin_handler import PluginHandler


async def mainloop(config_manager: ConfigManager) -> None:
    """Get all the configured plugins and starts all the controllers.

    :param config_manager: A ConfigManager instance for the plugin handler.
    """

    logger = getLogger(__name__)
    plugin_handler = PluginHandler(config_manager)

    orchestrator, controllers = plugin_handler.load_nodes()
    controller_start_functions = [controller.start() for controller in controllers]

    logger.info("Starting the mainloop...")

    try:
        await asyncio.gather(*controller_start_functions, return_exceptions=True)

        while True:
            orchestrator.check_if_song_finished()
            print(orchestrator.get_all_songs())
            await asyncio.sleep(0.5)
    finally:
        logger.info("Shutting down Dorothy")
        orchestrator._cleanup_nodes()

        for controller in controllers:
            if not controller.cleanup():
                logger.warning(
                    f'Controller "{controller.node_instance_path}" has failed cleanup!'
                )
