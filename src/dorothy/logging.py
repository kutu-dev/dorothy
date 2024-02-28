import logging

import colorama


def dim(message: str) -> str:
    return f"{colorama.Style.DIM}{message}{colorama.Style.RESET_ALL}"


class ColorizedFormatter(logging.Formatter):
    """Custom formatter used to make log messages colored according to their level"""

    def format(self, record: logging.LogRecord) -> str:
        colors = {
            logging.DEBUG: colorama.Fore.CYAN,
            logging.INFO: colorama.Fore.GREEN,
            logging.WARNING: colorama.Fore.YELLOW,
            logging.ERROR: colorama.Fore.RED,
            logging.CRITICAL: colorama.Fore.MAGENTA,
        }

        colorized_log_level = (
            f"[{colors[record.levelno]} %(levelname)s {colorama.Style.RESET_ALL}]"
        )

        formatter = logging.Formatter(
            f'{colorized_log_level} %(asctime)s {dim("(%(name)s)")} %(message)s'
        )

        return formatter.format(record)


def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    # TODO This should be managed by a global CLI flag when starting the daemon
    #  or using an entry in the config (more prone to errors?)
    ch.setLevel(logging.INFO)

    formatter = ColorizedFormatter()

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
