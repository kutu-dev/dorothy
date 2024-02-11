import curses
import sys
from abc import ABC, abstractmethod
from typing import Callable, Self, Type

import requests


class State(ABC):
    def __init__(
        self, change_state: Callable[[Type[Self], ...], None], *args, **kwargs
    ) -> None:
        self.list_buffer = []
        self.list_index = 0

        self.change_state = change_state

    @abstractmethod
    def action(self) -> None:
        ...

    @abstractmethod
    def back(self) -> None:
        ...


class Queue(State):
    def __init__(self, change_state: Callable[[Type[Self], ...], None]) -> None:
        super().__init__(change_state)

        self.list_buffer = requests.get(
            "http://localhost:6969/channels/main/queue"
        ).json()

    def action(self) -> None:
        requests.post(f"http://localhost:6969/channels/main/queue/{self.list_index}/play")

    def back(self) -> None:
        pass


class Song(State):
    def __init__(
        self, change_state: Callable[[Type[Self], ...], None], song_list_buffer: list
    ) -> None:
        super().__init__(change_state)

        self.list_buffer = song_list_buffer

    def action(self) -> None:
        requests.put(
            "http://localhost:6969/channels/main/queue",
            json={"song_resource_id": self.list_buffer[self.list_index]["resource_id"]},
        )

    def back(self) -> None:
        self.change_state(Album)


class Album(State):
    def __init__(self, change_state: Callable[[Type[Self], ...], None]) -> None:
        super().__init__(change_state)

        self.list_buffer = requests.get("http://localhost:6969/albums").json()["albums"]

    def action(self) -> None:
        album_id = self.list_buffer[self.list_index]["resource_id"]

        song_list_buffer = requests.get(
            f"http://localhost:6969/albums/{album_id}/songs"
        ).json()["songs"]

        self.change_state(Song, song_list_buffer)

    def back(self) -> None:
        pass


class Tui:
    def __init__(self):
        self.window = self.setup_curses()

        self.lines = curses.LINES - 1
        self.columns = curses.COLS - 1
        self.text_right_padding = 1

        self.list_vertical_top_padding = 3
        self.list_vertical_bottom_padding = 2

        self.list_lines = (
            curses.LINES
            - 1
            - self.list_vertical_top_padding
            - self.list_vertical_bottom_padding
        )

        self.state: State = Queue(self.change_state)
        self.update_list()
        self.start_mainloop()

    def debug_log(self, *args) -> None:
        message = ""

        for arg in args:
            message += f"'{str(arg)}' - "

        self.window.addstr(self.list_lines, 0, message)

    def setup_curses(self):
        window = curses.initscr()
        window.keypad(True)

        curses.noecho()
        curses.cbreak()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)

        return window

    def print_line(self, line: int, text: str, *args) -> None:
        empty_space_length = self.columns - len(text)

        self.window.addstr(
            line, self.text_right_padding, text + " " * empty_space_length, *args
        )

    def update_list(self) -> None:
        offset = max(0, self.state.list_index - int(self.list_lines / 2))

        start = offset
        end = self.list_lines + 1 + offset

        if end > len(self.state.list_buffer) > self.list_lines:
            start = len(self.state.list_buffer) - self.list_lines - 1
            end = len(self.state.list_buffer)

        cursor = self.state.list_index - start

        list_segment = self.state.list_buffer[start : end + 1]
        for line in range(self.list_lines + 1):
            if line > len(list_segment) - 1:
                self.print_line(line + self.list_vertical_top_padding, " ")
                continue

            if line == cursor:
                self.print_line(
                    line + self.list_vertical_top_padding,
                    list_segment[line]["title"],
                    curses.color_pair(1) | curses.A_BOLD,
                )
                continue

            self.print_line(
                line + self.list_vertical_top_padding, list_segment[line]["title"]
            )

    def scroll_up(self) -> None:
        if self.state.list_index <= 0:
            self.state.list_index = len(self.state.list_buffer) - 1
        else:
            self.state.list_index -= 1

        self.update_list()

    def scroll_down(self) -> None:
        if self.state.list_index >= len(self.state.list_buffer) - 1:
            self.state.list_index = 0
        else:
            self.state.list_index += 1

        self.update_list()

    def play_pause(self):
        requests.post("http://localhost:6969/channels/main/play_pause")

    def change_state(self, state: Type[State], *args, **kwargs) -> None:
        self.state = state(self.change_state, *args, **kwargs)

    def start_mainloop(self):
        while True:
            key = self.window.getkey()

            match key:
                case "q":
                    sys.exit()

                case "KEY_UP" | "k":
                    self.scroll_up()

                case "KEY_DOWN" | "j":
                    self.scroll_down()

                case "KEY_BACKSPACE":
                    self.state.back()
                    self.update_list()

                case "\n":
                    self.state.action()
                    self.update_list()
                    self.debug_log(f"http://localhost:6969/channels/main/queue/{self.state.list_index}/play")

                case " ":
                    self.play_pause()

                case "1":
                    self.change_state(Queue)
                    self.update_list()

                case "2":
                    self.change_state(Album)
                    self.update_list()


def tui():
    Tui()
