import curses
import sys
import time
import urllib.parse
from enum import Enum

import requests


class BUFFER_TYPES(Enum):
    ALBUM = "album"
    SONG = "song"


class Tui:
    def __init__(self):
        self.window = curses.initscr()
        self.window.keypad(True)

        curses.noecho()
        curses.cbreak()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)

        self.lines = curses.LINES - 1
        self.columns = curses.COLS - 1

        self.list_buffer = []
        self.list_buffer_type: BUFFER_TYPES | None = None
        self.list_index = 0

        self.load_albums_to_buffer()
        self.start_mainloop()

    def debug_log(self, *args) -> None:
        message = ""

        for arg in args:
            message += f"'{str(arg)}' - "

        self.window.addstr(self.lines, 0, message)

    def refresh_screen(self) -> None:
        self.window.clear()

        offset = max(0, self.list_index - int(self.lines / 2))

        start = offset
        end = self.lines + 1 + offset

        if end > len(self.list_buffer) > self.lines:
            start = len(self.list_buffer) - self.lines - 1
            end = len(self.list_buffer)

        cursor = self.list_index - start

        for index, album in enumerate(self.list_buffer[start:end]):
            if index == cursor:
                self.window.addstr(
                    index, 0, album["title"], curses.color_pair(1) | curses.A_BOLD
                )
                continue

            self.window.addstr(index, 0, album["title"])

    def scroll_up(self) -> None:
        if self.list_index <= 0:
            self.list_index = len(self.list_buffer) - 1
        else:
            self.list_index -= 1

        self.refresh_screen()

    def scroll_down(self) -> None:
        if self.list_index >= len(self.list_buffer) - 1:
            self.list_index = 0
        else:
            self.list_index += 1

        self.refresh_screen()

    def action(self) -> None:
        match self.list_buffer_type:
            case BUFFER_TYPES.ALBUM:
                album_id = self.list_buffer[self.list_index]["resource_id"]

                self.list_buffer = requests.get(
                    f"http://localhost:6969/albums/{album_id}/songs"
                ).json()["songs"]
                self.list_buffer_type = BUFFER_TYPES.SONG
                self.refresh_screen()

            case BUFFER_TYPES.SONG:
                requests.put(
                    "http://localhost:6969/channels/main/queue",
                    json={
                        "song_resource_id": self.list_buffer[self.list_index][
                            "resource_id"
                        ]
                    },
                )

    def back(self) -> None:
        match self.list_buffer_type:
            case BUFFER_TYPES.SONG:
                self.load_albums_to_buffer()

    def play(self):
        self.debug_log("PLAY")
        requests.post("http://localhost:6969/channels/main/play")

    def load_queue_to_buffer(self) -> None:
        self.list_buffer = requests.get(
            "http://localhost:6969/channels/main/queue"
        ).json()["songs"]

    def load_albums_to_buffer(self) -> None:
        self.list_buffer = requests.get("http://localhost:6969/albums").json()["albums"]
        self.list_buffer_type = BUFFER_TYPES.ALBUM
        self.refresh_screen()

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

                case "KEY_LEFT" | "h":
                    self.back()

                case "\n":
                    self.action()

                case " ":
                    self.play()
