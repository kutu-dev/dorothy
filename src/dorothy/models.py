from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Type

from . import Colors

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

if TYPE_CHECKING:
    from .config import ConfigSchema

from .logging import get_logger


@dataclass
class Id:
    provider_id: str
    item_id: Any


class Song:
    def __init__(
        self, id_: Id, uri: str | None = None, title: str | None = None
    ) -> None:
        self.id = id_
        self.uri = uri
        self.title = title

    @property
    def __dict__(self) -> dict[str, Any]:
        return {"id": vars(self.id), "uri": self.uri, "title": self.title}

    @__dict__.setter
    def __dict__(self, value: dict[str, Any]) -> None:
        self.dict = value


class Node:
    config_schema: "ConfigSchema | None" = None

    def __init__(self) -> None:
        self.instance_id: str = ""

        self.instance_config: dict[Any, Any] = {}

    def setup_instance(self, instance_id: str, instance_config: dict[Any, Any]) -> None:
        self.instance_id = instance_id
        self.logger = get_logger(instance_id)
        self.instance_config = instance_config

        self.logger.info(f'Node {Colors.dim}"{instance_id}"{Colors.reset} instantiated')

    def start(self) -> None:
        ...

    def cleanup(self) -> bool:
        return True


class Controller(Node, ABC):
    def __init__(self) -> None:
        super().__init__()

    def setup_controller(self, orchestrator: "Orchestrator") -> None:
        self.orchestrator = orchestrator
        self.start()


class Provider(Node, ABC):
    @abstractmethod
    def get_all_songs(self) -> list[Song]:
        ...

    @abstractmethod
    def get_song(self, item_id: str) -> Song:
        ...


class Listener(Node, ABC):
    @abstractmethod
    def play(self, song: Song) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class PluginManifesto(ABC):
    @property
    @abstractmethod
    def extension_id(self) -> str:
        ...

    def get_controllers(self) -> list[Type[Controller]]:
        return []

    def get_providers(self) -> list[Type[Provider]]:
        return []

    def get_listeners(self) -> list[Type[Listener]]:
        return []
