from argparse import ArgumentParser, Namespace
from pathlib import Path

from . import __version__


def get_args() -> Namespace:
    """Set up an argument parser and process command-line arguments.
    It already ends execution when checking the version or the help menu.

    :return: Namespace containing all arguments parsed from the command line
    """

    parser = ArgumentParser(
        prog="Dorothy Music Player",
        description="A minimalistic music player based on the use of plugins to customize it to your needs",
        epilog="Created with <3 by Kutu :: https://dobon.dev",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        metavar="DIRECTORY_PATH",
        help="Use a custom path for the config directory instead of using the default one of your system",
    )

    parser.add_argument(
        "-l",
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Set the logging level, defaults to info",
    )

    return parser.parse_args()
