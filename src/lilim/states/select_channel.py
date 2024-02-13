from typing import Type, Callable

import requests

from .state import State, ListElement
from ..exceptions import UnsuccessfulRequest


class SelectChannel(State):
    def __init__(
        self,
        *args,
        back_state: Type[State],
        change_channel_callback: Callable[[str], None],
        change_blocked_state_keys_callback: Callable[[bool], None]
    ) -> None:
        super().__init__(*args)

        self.print_topbar("Select channel")

        self.back_state = back_state
        self.change_channel_callback = change_channel_callback
        self.change_blocked_state_keys_callback = change_blocked_state_keys_callback

        try:
            channels = self.request("GET", "channels").json()["channels"]
        except UnsuccessfulRequest:
            return

        for channel in channels:
            self.list_buffer.append(ListElement(channel))

    def action(self) -> None:
        self.change_channel_callback(self.list_buffer[self.list_index].text)
        self.change_blocked_state_keys_callback(False)
        self.change_state(self.back_state)

    def enter(self) -> None:
        pass

    def delete(self) -> None:
        pass

    def back(self) -> None:
        pass
