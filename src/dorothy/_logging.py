import logging
from logging import basicConfig, INFO


def configure_logging(log_level: str) -> None:
    """Configure the logging of the app.

    Args:
        log_level: The log level string to set the global level to.

    Raises:
        ValueError: Raised if the given `log_level` is not valid.
    """

    match log_level.lower():
        case "critical":
            log_level_int = logging.CRITICAL
        case "error":
            log_level_int = logging.ERROR
        case "warning":
            log_level_int = logging.WARNING
        case "info":
            log_level_int = logging.INFO
        case "debug":
            log_level_int = logging.DEBUG
        case _:
            raise ValueError("An invalid log level string was provided")

    basicConfig(
        level=log_level_int,
        format="[ %(levelname)s ] %(asctime)s (%(name)s) %(message)s",
    )
