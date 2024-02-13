from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Any, Protocol, Type, Callable

import requests
from requests import Response

from ..exceptions import UnsuccessfulRequest


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
        print_topbar: Callable[[str], None],
        **kwargs,
    ) -> None:
        self.list_buffer: list[ListElement] = []
        self.list_index = 0

        self.channel = channel

        self.change_state = change_state
        self.update_list = update_list
        self.notification = notification
        self.print_topbar = print_topbar

    def current(self) -> ListElement:
        return self.list_buffer[self.list_index]

    def request(self, verb: str, path: str, json: dict[str, Any] | None = None) -> Response:
        try:
            response = requests.request(verb, f"http://localhost:6969/{path}", json=json)
        except requests.exceptions.ConnectionError:
            self.notification("ERROR: Connection to Dorothy refused")
            raise UnsuccessfulRequest

        if response.status_code != 200:
            self.notification(f"ERROR {response.status_code}: {response.reason}")
            raise UnsuccessfulRequest

        return response

    def channel_request(self, verb: str, path: str, json: dict[str, Any] | None = None):
        return self.request(verb, f"channels/{self.channel}/{path}", json)

    @abstractmethod
    def action(self) -> None:
        ...

    @abstractmethod
    def enter(self) -> None:
        ...

    @abstractmethod
    def delete(self) -> None:
        ...

    @abstractmethod
    def back(self) -> None:
        ...
