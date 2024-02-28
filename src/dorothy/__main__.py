import cProfile
import sys
from typing import Annotated, Optional

import psutil
import typer
from rich.console import Console

from . import __version__
from .daemon import start_daemon


def main() -> None:
    start_daemon()


if __name__ == "__main__":
    main()
