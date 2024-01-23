import logging
import colorama
from . import Colors


class ColorizedFormatter(logging.Formatter):
    """Custom formatter used to make log messages colored according to their level"""

    def format(self, record):

        colors = {
            logging.DEBUG: Colors.cyan,
            logging.INFO: Colors.green,
            logging.WARNING: Colors.yellow,
            logging.ERROR: Colors.red,
            logging.CRITICAL: Colors.magenta
        }

        colorized_log_level = f"[{colors[record.levelno]} %(levelname)s {Colors.reset}]"

        formatter = logging.Formatter(
            f"{colorized_log_level} %(asctime)s {colorama.Style.DIM}(%(name)s){Colors.reset} %(message)s"
        )

        return formatter.format(record)


def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = ColorizedFormatter()

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
