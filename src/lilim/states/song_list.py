from typing import Any

import requests
from ..exceptions import UnsuccessfulRequest

from .state import State, ListElement
import lilim.states.album_list


class SongList(State):
    def __init__(self, *args, topbar_title: str, song_list: list[dict[str, Any]]) -> None:
        super().__init__(*args)

        for song in song_list:
            self.list_buffer.append(ListElement(song["title"], song))

        self.print_topbar(topbar_title)

    def action(self) -> None:
        try:
            self.channel_request("PUT", "queue", json={
                "resource_id": self.list_buffer[self.list_index].internal["resource_id"]
            })
        except UnsuccessfulRequest:
            return

        self.notification(
            f"Added song {self.list_buffer[self.list_index].text} to the queue"
        )

    def enter(self) -> None:
        pass

    def delete(self) -> None:
        pass

    def back(self) -> None:
        self.change_state(lilim.states.album_list.AlbumList)
