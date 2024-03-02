from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Protocol, Type, Callable

import requests
from requests import Response

from ..exceptions import UnsuccessfulRequest
from ..player_states import PlayerStates


@dataclass
class ListElement:
    text: str
    internal: dict[str, Any] = field(default_factory=lambda: "")


class ChangeState(Protocol):
    def __call__(self, state: Type["State"], **kwargs) -> None:
        ...


class State(ABC):
    def __init__(
        self,
        channel: str,
        change_state: ChangeState,
        update_list: Callable[[], None],
        notification: Callable[[str], None],
        update_topbar: Callable[[str], None],
        change_bottombar_state: Callable[[str | None, PlayerStates | None], None],
        **kwargs,
    ) -> None:
        self.list_buffer: list[ListElement] = []
        self.list_index = 0

        self.channel = channel

        self.change_state = change_state
        self.update_list = update_list
        self.notification = notification
        self.update_topbar = update_topbar
        self.change_bottombar_state = change_bottombar_state

    def current(self) -> ListElement:
        return self.list_buffer[self.list_index]

    def request(
        self, verb: str, path: str, json: dict[str, Any] | None = None
    ) -> Response:
        try:
            response = requests.request(
                verb, f"http://localhost:6969/{path}", json=json
            )
        except requests.exceptions.ConnectionError:
            self.notification("ERROR: Connection to Dorothy refused")
            raise UnsuccessfulRequest

        if response.status_code != 200:
            self.notification(f"ERROR {response.status_code}: {response.reason}")
            raise UnsuccessfulRequest

        return response

    def channel_request(self, verb: str, path: str, json: dict[str, Any] | None = None):
        # Avoid trailing slash bars on the URL
        if path == "":
            route = f"channels/{self.channel}"
        else:
            route = f"channels/{self.channel}/{path}"

        return self.request(verb, route, json)

    def action(self) -> None:
        pass

    def enter(self) -> None:
        pass

    def skip(self) -> None:
        pass

    def delete(self) -> None:
        pass

    def play_pause(self, queue_changed: bool) -> None:
        pass

    def back(self) -> None:
        pass
