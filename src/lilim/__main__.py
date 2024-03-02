import curses

from .tui import Tui


def main() -> None:
    curses.wrapper(Tui)


if __name__ == "__main__":
    main()
