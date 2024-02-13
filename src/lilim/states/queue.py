import requests

from .state import State, ListElement
from ..exceptions import UnsuccessfulRequest


class Queue(State):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.print_topbar("Queue")

        try:
            songs = self.channel_request("GET", "queue").json()["songs"]
        except UnsuccessfulRequest:
            return

        for song in songs:
            self.list_buffer.append(ListElement(song["title"]))

    def action(self) -> None:
        try:
            self.channel_request("POST", f"queue/{self.list_index}/play")
        except UnsuccessfulRequest:
            return

    def enter(self) -> None:
        pass

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

    def back(self) -> None:
        pass
