import sys
import time

from . import logging
from . import __version__, Colors
from .channel import Channel
from .config import ConfigManager
from .extensions import load_extensions
from .models import Controller
from .orchestrator import Orchestrator


def main() -> None:
    logger = logging.get_logger(__name__)

    logger.info(f"{Colors.purple}     ___              _   _        {Colors.reset}")
    logger.info(f"{Colors.purple}    |   \\ ___ _ _ ___| |_| |_ _  _ {Colors.reset}")
    logger.info(f"{Colors.purple}    | |) / _ \\ '_/ _ \\  _| ' \\ || |{Colors.reset}")
    logger.info(f"{Colors.purple}    |___/\\___/_| \\___/\\__|_||_\\_, |{Colors.reset}")
    logger.info(f"{Colors.purple}                               |__/ {Colors.reset}")
    logger.info(f"     {Colors.dim}Version: {__version__}{Colors.reset}")
    logger.info(f"  Time to mix {Colors.blue}drinks{Colors.reset} and change {Colors.red}lives{Colors.reset}")
    logger.info("")

    config_manager = ConfigManager()
    extensions = load_extensions(config_manager)
    orchestrator = Orchestrator(extensions.providers, extensions.listeners)

    try:
        start_mainloop(orchestrator, extensions.controllers)
    except KeyboardInterrupt:
        pass
    finally:
        orchestrator.cleanup_nodes()

    logger.info("See you at Tres Alicias...")
    sys.exit()

    # TODO Priority:
    #  - Finish parallel client connections to the socket and start making a little API for it
    #  - Make URI use urilib from Python instead of str (?)

    # TODO Not priority:
    #  - make a global config manager (in ConfigManager?)
    #     for Dorothy configs like (use_splash/skip_splash, colorless mode, goodbye message , etc)
    #  - Add linter and formater with custom configs using Ruff
    #  - URI transformers (when Discord bot is in the works)


def start_mainloop(orchestrator: Orchestrator, controllers: list[Controller]) -> None:
    for controller in controllers:
        controller.setup_controller(orchestrator)
        print("SES")

    while True:
        pass
