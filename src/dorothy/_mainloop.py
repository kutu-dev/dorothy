import asyncio
from logging import getLogger

from ._config import ConfigManager
from ._plugin_handler import PluginHandler


async def mainloop(config_manager: ConfigManager) -> None:
    """Get all the configured plugins and start the controllers.

    Args:
        config_manager: A configuration manager instance to handle plugin
            initialization.
    """

    logger = getLogger(__name__)
    plugin_handler = PluginHandler(config_manager)

    orchestrator, controllers = plugin_handler.load_nodes()
    controlers_tasks = [
        asyncio.create_task(controller.start()) for controller in controllers
    ]

    logger.info("Starting the mainloop...")

    try:
        await asyncio.gather(*controlers_tasks, return_exceptions=True)

        while True:
            orchestrator.check_if_song_finished()
            await asyncio.sleep(0.5)

    except asyncio.exceptions.CancelledError:
        pass

    finally:
        logger.info("Shutting down Dorothy")

        for controller in controllers:
            cleanup_status = await controller.cleanup()
            if cleanup_status is not None:
                logger.warning(
                    f'Controller "{controller.node_instance_path}" has failed '
                    + "cleanup "
                    + f'with error "{cleanup_status}"'
                )

        tasks = asyncio.all_tasks()

        current = asyncio.current_task()
        tasks.remove(current)

        for task in tasks:
            task.cancel()

        orchestrator._cleanup_nodes()
