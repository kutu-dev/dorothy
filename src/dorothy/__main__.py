import asyncio
from logging import getLogger

from dorothy.config import ConfigManager
from .args import get_args
from .logging import configure_logging
from .mainloop import mainloop


def main() -> None:
    """Main entry of Dorothy, runs the mainloop in an asyncio event loop"""

    args = get_args()

    configure_logging(args.log_level)
    logger = getLogger(__name__)

    logger.debug("Booting up Dorothy...")
    config_manager = ConfigManager(args.config)
    asyncio.run(mainloop(config_manager))


if __name__ == "__main__":
    main()
