from typing_extensions import override

import requests

from .state import State, ListElement
from ..exceptions import UnsuccessfulRequest
from ..player_states import PlayerStates


class Queue(State):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.update_topbar("Queue")

        try:
            songs = self.channel_request("GET", "queue").json()["songs"]
        except UnsuccessfulRequest:
            return

        for song in songs:
            self.list_buffer.append(ListElement(song["title"]))

    @override
    def action(self) -> None:
        try:
            self.channel_request("POST", f"queue/{self.list_index}/play")
        except UnsuccessfulRequest:
            return

        self.change_bottombar_state(self.current().text, PlayerStates.PLAYING)

        self.list_buffer = self.list_buffer[self.list_index + 1:]
        self.list_index = 0
        self.update_list()

    @override
    def skip(self) -> None:
        try:
            self.channel_request("POST", "skip")
        except UnsuccessfulRequest:
            return

        self.change_bottombar_state(self.list_buffer[0].text, PlayerStates.PLAYING)
        self.list_buffer = self.list_buffer[1:]
        self.update_list()

    @override
    def delete(self) -> None:
        if len(self.list_buffer) <= 0:
            self.notification("There are no songs to delete")
            return

        response = requests.delete(
            f"http://localhost:6969/channels/main/queue/{self.list_index}"
        )

        try:
            self.channel_request("DELETE", f"queue/{self.list_index}")
        except UnsuccessfulRequest:
            return

        self.list_buffer.pop(self.list_index)
        self.update_list()

    @override
    def play_pause(self, queue_changed: bool) -> None:
        try:
            channel_state = self.channel_request("GET", "").json()
        except UnsuccessfulRequest:
            return

        if queue_changed:
            self.list_buffer = self.list_buffer[1:]
            self.update_list()
