import curses
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Self, Type, Protocol, Any

import requests

from .states.state import State
from .states.album_list import AlbumList
from .states.queue import Queue
from .states.select_channel import SelectChannel


class Tui:
    def __init__(self):
        self.window = self.setup_curses()

        self.lines = curses.LINES
        self.columns = curses.COLS

        self.print_line(1, "━" * self.columns)

        self.list_vertical_top_padding = 2
        self.list_vertical_bottom_padding = 2

        self.list_lines = (
            curses.LINES
            - 1
            - self.list_vertical_top_padding
            - self.list_vertical_bottom_padding
        )

        self.channel = ""
        self.blocked_state_keys = True

        if self.channel == "":
            self.change_state(
                SelectChannel,
                back_state=Queue,
                change_channel_callback=self.change_channel,
                change_blocked_state_keys_callback=self.change_blocked_state_keys,
            )

        self.start_mainloop()

    def print_line(self, line: int, text: str, *args, right_text: str = "") -> None:
        empty_space_length = self.columns - len(text)

        line_text = text + " " * (empty_space_length - len(right_text)) + right_text

        self.window.addstr(line, 0, line_text, *args)

    def notification(self, message: str) -> None:
        self.print_line(self.lines, message)

    def change_blocked_state_keys(self, blocked_state_keys: bool) -> None:
        self.blocked_state_keys = blocked_state_keys

    def change_channel(self, channel: str) -> None:
        self.channel = channel

    def print_topbar(self, title: str) -> None:
        channel_name = self.channel if self.channel != "" else "N/A"
        self.print_line(0, title, right_text=f"Channel: {channel_name}")

    def setup_curses(self):
        window = curses.initscr()
        window.keypad(True)

        curses.noecho()
        curses.cbreak()

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLUE, -1)

        curses.curs_set(0)

        return window

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
                    list_segment[line].text,
                    curses.color_pair(1) | curses.A_BOLD,
                )
                continue

            self.print_line(
                line + self.list_vertical_top_padding, list_segment[line].text
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

    def change_state(self, state: Type[State], **kwargs) -> None:
        self.state = state(
            self.channel, self.change_state, self.update_list, self.notification, self.print_topbar, **kwargs
        )
        self.update_list()

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
                    self.state.back()

                case "KEY_RIGHT" | "l":
                    self.state.enter()

                case "\n":
                    self.state.action()

                case " ":
                    self.play_pause()

                case "d":
                    self.state.delete()

                case "1":
                    if not self.blocked_state_keys:
                        self.change_state(Queue)

                case "2":
                    if not self.blocked_state_keys:
                        self.change_state(AlbumList)

                case "c":
                    if not self.blocked_state_keys:
                        self.change_state(
                            SelectChannel,
                            back_state=type(self.state),
                            change_channel_callback=self.change_channel,
                            change_blocked_state_keys_callback=self.change_blocked_state_keys,
                        )
                        self.blocked_state_keys = True
