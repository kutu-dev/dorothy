from typing import Type, Callable
from typing_extensions import override
import requests

from .state import State, ListElement
from ..exceptions import UnsuccessfulRequest
from ..player_states import PlayerStates


class SelectChannel(State):
    def __init__(
        self,
        *args,
        back_state: Type[State],
        change_channel: Callable[[str], None],
        change_blocked_state_keys: Callable[[bool], None],
        change_bottombar_state_given_channel_state: Callable[[str], None]
    ) -> None:
        super().__init__(*args)

        self.update_topbar("Select channel")

        self.back_state = back_state
        self.change_channel = change_channel
        self.change_blocked_state_keys = change_blocked_state_keys
        self.change_bottombar_state_given_channel_state = change_bottombar_state_given_channel_state

        try:
            channels = self.request("GET", "channels").json()["channels"]
        except UnsuccessfulRequest:
            return

        for channel in channels:
            self.list_buffer.append(ListElement(channel))

    @override
    def action(self) -> None:
        channel_name = self.current().text

        self.channel = channel_name
        self.change_channel(channel_name)
        self.change_blocked_state_keys(False)

        try:
            channel_state = self.channel_request("GET", "").json()
        except UnsuccessfulRequest:
            return

        self.change_bottombar_state_given_channel_state(channel_state)

        self.change_state(self.back_state)
