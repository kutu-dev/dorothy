import sys
import time

from . import logging
from . import __version__, Colors
from .channel import Channel
from .config import ConfigManager
from .extensions import load_extensions


def main() -> int:
    logger = logging.get_logger(__name__)

    logger.info(f"{Colors.purple}     ___              _   _        ")
    logger.info(f"{Colors.purple}    |   \\ ___ _ _ ___| |_| |_ _  _ ")
    logger.info(f"{Colors.purple}    | |) / _ \\ '_/ _ \\  _| ' \\ || |")
    logger.info(f"{Colors.purple}    |___/\\___/_| \\___/\\__|_||_\\_, |")
    logger.info(f"{Colors.purple}                               |__/ ")
    logger.info(f"     {Colors.dim}Version: {__version__}{Colors.reset}")
    logger.info(f"  Time to mix {Colors.blue}drinks{Colors.reset} and change {Colors.red}lives{Colors.reset}")
    logger.info("")

    config_manager = ConfigManager()
    extensions = load_extensions(config_manager)

    # TODO Priority
    # TODO Unify Provider and Listener in a common class Node,
    # TODO make a NodeConfig for the nodes, make the orchestrator,
    # TODO make all the controllers system
    
    # TODO Not priority
    # TODO make a global config manager (in ConfigManager?) for Dorothy configs like (use_splash/skip_splash)
    # TODO Add linter and formater with custom configs using Ruff

    sys.exit()
    songs = extensions.providers[0].list_all_songs()

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
