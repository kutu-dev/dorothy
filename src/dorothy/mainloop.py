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
    controlers_tasks = [asyncio.create_task(controller.start()) for controller in controllers]

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

        orchestrator._cleanup_nodes()

        for controller in controllers:
            cleanup_message = await controller.cleanup()
            if cleanup_message is not None:
                logger.warning(
                    f'Controller "{controller.node_instance_path}" has failed cleanup with error "{cleanup_message}"'
                )

        tasks = asyncio.all_tasks()
        # get the current task
        current = asyncio.current_task()
        # remove current task from all tasks
        tasks.remove(current)
        # cancel all remaining running tasks
        for task in tasks:
            task.cancel()
