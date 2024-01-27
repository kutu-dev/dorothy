import sys

from . import Colors, __version__
from .config import ConfigManager
from .logging import get_logger
from .models import Controller
from .orchestrator import Orchestrator
from .plugin_handler import load_plugins


def main() -> None:
    logger = get_logger(__name__)

    logger.info(f"{Colors.purple}     ___              _   _        {Colors.reset}")
    logger.info(f"{Colors.purple}    |   \\ ___ _ _ ___| |_| |_ _  _ {Colors.reset}")
    logger.info(f"{Colors.purple}    | |) / _ \\ '_/ _ \\  _| ' \\ || |{Colors.reset}")
    logger.info(f"{Colors.purple}    |___/\\___/_| \\___/\\__|_||_\\_, |{Colors.reset}")
    logger.info(f"{Colors.purple}                               |__/ {Colors.reset}")
    logger.info(f"     {Colors.dim}Version: {__version__}{Colors.reset}")
    logger.info(
        f"  Time to mix {Colors.blue}drinks{Colors.reset} and change {Colors.red}lives{Colors.reset}"
    )
    logger.info("")

    config_manager = ConfigManager()
    plugins = load_plugins(config_manager)
    orchestrator = Orchestrator(plugins.providers, plugins.listeners)

    try:
        start_mainloop(orchestrator, plugins.controllers)
    except KeyboardInterrupt:
        pass
    finally:
        orchestrator.cleanup_nodes()

        for controller in plugins.controllers:
            if not controller.cleanup():
                logger.warning(
                    f'Controller {Colors.dim}"{controller.instance_id}"{Colors.reset} has failed cleanup!'
                )

    logger.info("See you at Tres Alicias...")
    sys.exit()

    # TODO Priority:
    #  - FIX MYPY TYPING
    #  - ADD @overload too the models

    # TODO Not priority:
    #  - make a global config manager (in ConfigManager?)
    #     for Dorothy configs like (use_splash/skip_splash, colorless mode, goodbye message , etc)
    #  - Add linter and formater with custom configs using Ruff
    #  - URI transformers (when Discord bot is in the works)

    # TODO Exception overhaul:
    #  - When a Exception ocurrs loading a plugin


def start_mainloop(orchestrator: Orchestrator, controllers: list[Controller]) -> None:
    for controller in controllers:
        controller.setup_controller(orchestrator)
        print("SES")

    while True:
        pass
