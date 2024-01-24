from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Type, TYPE_CHECKING

from . import Colors

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

if TYPE_CHECKING:
    from .config import ConfigSchema

from .logging import get_logger


class Song:
    def __init__(self, id_: Any, uri: str, title: str | None = None) -> None:
        self.id: Any = id_
        self.uri: str = uri
        self.title = title


class Node:
    @property
    @abstractmethod
    def config_schema(self) -> "ConfigSchema":
        ...

    def __init__(self) -> None:
        self.instance_id: str = ""
        self.logger: Logger | None = None
        self.instance_config: dict = {}

    def set_instance(self, instance_id: str, instance_config: dict) -> None:
        self.instance_id = instance_id
        self.logger = get_logger(instance_id)
        self.instance_config = instance_config

        self.logger.info(f'Node {Colors.dim}"{instance_id}"{Colors.reset} instantiated')

    def cleanup(self) -> bool:
        return True


class Controller(Node, ABC):
    def __init__(self) -> None:
        super().__init__()

        self.orchestrator: "Orchestrator | None" = None

    def setup_controller(self, orchestrator: "Orchestrator") -> None:
        self.orchestrator = orchestrator
        self.start_controller()

    @abstractmethod
    def start_controller(self) -> None:
        ...

class Provider(Node, ABC):
    @abstractmethod
    def get_all_songs(self) -> list[Song]:
        ...


class Listener(Node, ABC):
    @abstractmethod
    def play(self, song: Song) -> None:
        ...


class ExtensionManifesto(ABC):
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
