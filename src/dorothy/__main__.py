import sys
import time

from . import logging
from . import __version__, Colors
from .channel import Channel
from .config import ConfigManager
from .extensions import load_extensions
from .orchestrator import Orchestrator


def main() -> int:
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

    for controller in extensions.controllers:
        controller.setup_controller(orchestrator)

    orchestrator.cleanup_nodes()

    logger.info("See you at Tres Alicias...")

    # TODO Priority:
    #  - Make thinks "life" with Process (or maybe another approach)
    #  - Make URI use urilib from Python instead of str (?)

    # TODO Not priority:
    #  - make a global config manager (in ConfigManager?)
    #     for Dorothy configs like (use_splash/skip_splash, colorless mode, goodbye message , etc)
    #  - Add linter and formater with custom configs using Ruff
    #  - URI transformers (when Discord bot is in the works)

    sys.exit()


    channel = Channel()
    logger.debug("channel Adding song: " + songs[0].uri)
    channel.add_to_queue(songs[0])
    channel.listeners.extend(extensions.listeners)
    channel.play()

    channel_EOPOOO = Channel()
    logger.debug("channel1 Adding song: " + songs[1].uri)
    channel_EOPOOO.add_to_queue(songs[1])
    channel_EOPOOO.listeners.extend(extensions.listeners)
    channel_EOPOOO.play()

    # TODO This isn't stopping "channel" for some reason
    # TODO Improve the extension instantiation to clean all of them is a top priority
    time.sleep(5)
    print("Stopping 0")
    channel.cleanup_listeners()
    time.sleep(5)
    print("Stopping 1")
    channel_EOPOOO.cleanup_listeners()

    return 0
