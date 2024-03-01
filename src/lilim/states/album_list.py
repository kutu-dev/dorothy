import requests
from typing_extensions import override

from .state import State, ListElement
from .song_list import SongList
from ..exceptions import UnsuccessfulRequest


class AlbumList(State):
    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.update_topbar("Albums")

        try:
            albums = self.request("GET", "albums").json()["albums"]
        except UnsuccessfulRequest:
            return

        for album in albums:
            self.list_buffer.append(ListElement(album["title"], album))

    @override
    def action(self) -> None:
        selected_album = self.current()

        try:
            response = self.channel_request(
                "PUT", "queue", {"resource_id": selected_album.internal["resource_id"]}
            )
        except UnsuccessfulRequest:
            return

        number_of_songs_text = f'({len(selected_album.internal["song_list"])} songs)'

        self.notification(
            f"Added album {selected_album.text} {number_of_songs_text} to the queue"
        )

    @override
    def enter(self) -> None:
        selected_album = self.current()

        try:
            song_list = self.request(
                "GET", f'albums/{selected_album.internal["resource_id"]}'
            ).json()["song_list"]
        except UnsuccessfulRequest:
            song_list = []

        self.change_state(
            SongList, topbar_title=selected_album.text, song_list=song_list
        )
