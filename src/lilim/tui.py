import curses
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Self, Type, Protocol, Any

import requests

from .exceptions import UnsuccessfulRequest
from .player_states import PlayerStates
from .states.state import State
from .states.album_list import AlbumList
from .states.queue import Queue
from .states.select_channel import SelectChannel


@dataclass
class BottombarState:
    current_song: str
    player_state: PlayerStates


class Tui:
    def __init__(self):
        self.window = self.setup_curses()

        self.lines = 0
        self.columns = 0
        self.list_lines = 0

        self.title = ""

        self.list_vertical_top_padding = 2
        self.list_vertical_bottom_padding = 3

        self.channel = None
        self.bottombar_state = BottombarState("N/A", PlayerStates.STOPPED)

        self.update_overlay()
        self.print_bottombar()

        if self.channel is None:
            self.blocked_state_keys = True
            self.change_state(
                SelectChannel,
                back_state=Queue,
                change_channel=self.change_channel,
                change_blocked_state_keys=self.change_blocked_state_keys,
                change_bottombar_state_given_channel_state=self.change_bottombar_state_given_channel_state,
            )

        self.notification_display_timestamp = 0.0

        self.start_mainloop()

    def print_line(self, line: int, text: str, *args, right_text="") -> None:
        empty_space_length = self.columns - len(text) - len(right_text)

        line_text = text + " " * empty_space_length + right_text

        try:
            self.window.addstr(line, 0, line_text, *args)
        # Avoid crash when printing in the last line
        # as it will try to move the cursor out of bounds
        except curses.error:
            pass

    def update_overlay(self) -> None:
        self.lines, self.columns = self.window.getmaxyx()
        self.lines -= 1

        self.list_lines = (
            self.lines
            - self.list_vertical_top_padding
            - self.list_vertical_bottom_padding
        )

        self.print_line(1, "━" * self.columns)
        self.print_line(self.lines - 2, "━" * self.columns)

    def notification(self, message: str) -> None:
        self.print_line(self.lines - 1, message)

        self.notification_display_timestamp = time.time()

    def change_blocked_state_keys(self, blocked_state_keys: bool) -> None:
        self.blocked_state_keys = blocked_state_keys

    def change_channel(self, channel: str) -> None:
        self.channel = channel

    def change_bottombar_state(
        self,
        new_current_song: str | None = None,
        new_player_state: PlayerStates | None = None,
    ) -> None:
        if new_current_song is not None:
            self.bottombar_state.current_song = new_current_song

        if new_player_state is not None:
            self.bottombar_state.player_state = new_player_state

        if new_current_song is not None or new_player_state is not None:
            self.print_bottombar()

    def update_topbar(self, title: str | None = None) -> None:
        if title is not None:
            self.title = title

        channel_name = self.channel if self.channel is not None else "N/A"
        self.print_line(0, self.title, right_text=f"Channel: {channel_name}")

    def print_bottombar(self) -> None:
        self.print_line(
            self.lines - 1,
            self.bottombar_state.current_song,
            right_text=self.bottombar_state.player_state.value,
        )

        self.print_line(self.lines, "")

        # If a notification message overflowed to the last line for some reason
        # printing to the most right character of the line silently fails
        # so a manually repainting is needed
        self.window.addch(self.lines - 1, self.columns - 1, " ")

    def setup_curses(self):
        window = curses.initscr()
        window.keypad(True)
        window.timeout(1)

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
        if self.channel is None:
            return

        try:
            channel_state = self.state.channel_request("POST", "play_pause").json()
        except UnsuccessfulRequest:
            return

        self.change_bottombar_state_given_channel_state(channel_state)
        self.state.play_pause(channel_state["queue_changed"])

    def stop(self):
        try:
            self.state.channel_request("POST", "stop")
        except UnsuccessfulRequest:
            return

        self.change_bottombar_state("N/A", PlayerStates.STOPPED)

    def change_bottombar_state_given_channel_state(self, channel_state: dict[str, Any]):
        match channel_state["player_state"]:
            case "PLAYING":
                player_state = PlayerStates.PLAYING
            case "PAUSED":
                player_state = PlayerStates.PAUSED
            case "STOPPED":
                player_state = PlayerStates.STOPPED
            case _:
                self.notification("ERROR: The received player_state is not valid")
                raise UnsuccessfulRequest()

        self.change_bottombar_state(
            channel_state["current_song"]["title"]
            if channel_state["current_song"] is not None
            else "N/A",
            player_state,
        )

    def change_state(self, state: Type[State], **kwargs) -> None:
        self.state = state(
            self.channel,
            self.change_state,
            self.update_list,
            self.notification,
            self.update_topbar,
            self.change_bottombar_state,
            **kwargs,
        )
        self.update_list()

    def start_mainloop(self):
        while True:
            if (
                self.notification_display_timestamp != 0
                and time.time() - self.notification_display_timestamp > 1
            ):
                self.notification_display_timestamp = 0.0
                self.print_bottombar()

            try:
                key = self.window.getkey()
            # As previously the flag "timeout" was set to 1 miliseccond ncurses usually doesn't wai enough for input
            # and just raises and exception, this flag is set to not attach the mainloop to
            # the user input and reliable run background checks
            except curses.error:
                continue

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

                case "s":
                    self.state.skip()

                case "d":
                    self.state.delete()

                case "x":
                    self.stop()

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
                            change_channel=self.change_channel,
                            change_blocked_state_keys=self.change_blocked_state_keys,
                            change_bottombar_state_given_channel_state=self.change_bottombar_state_given_channel_state,
                        )
                        self.blocked_state_keys = True

                case "KEY_RESIZE":
                    self.update_overlay()
                    self.update_topbar()
                    self.update_list()
