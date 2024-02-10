import sys
from typing import Annotated, Optional

import psutil
import typer
from rich.console import Console

from src.dorothy.tui import Tui

from . import __version__
from .daemon import start_daemon

app = typer.Typer(
    no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]}
)
error = Console(stderr=True)


@app.command()
def init() -> None:
    """Start the Dorothy daemon."""

    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if "dorothy-daemon" in proc.name().lower():
                error.print(
                    "[bold red]ERROR[/bold red]: It seems like",
                    f"the daemon is already running! (pid: {proc.pid})",
                )
                sys.exit(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    start_daemon()


@app.command()
def tui() -> None:
    Tui()


def version_callback(value: bool) -> None:
    if value:
        print(f"Dorothy {__version__}")
        print("Created with <3 by Kutu - https://dobon.dev")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "-v",
            "--version",
            callback=version_callback,
            help="Shows the installed version of Dorothy.",
        ),
    ] = False,
) -> None:
    # TODO Improve description
    """dorothy - a customizable music server"""


if __name__ == "__main__":
    app()
