from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Type, TYPE_CHECKING

from . import Colors

if TYPE_CHECKING:
    from .config import ConfigSchema

from .logging import get_logger


class Song:
    def __init__(self, id_: Any, uri: str, title: str | None = None) -> None:
        self.id: Any = id_
        self.uri: str = uri
        self.title = title


class Provider(ABC):
    def __init__(self) -> None:
        self.logger: Logger | None = None
        self.instance_config: dict = {}

    def set_instance(self, instance_id: str) -> None:
        self.logger = get_logger(instance_id)
        self.logger.info(f'Listener {Colors.dim}"{instance_id}"{Colors.reset} instantiated')

    @property
    @abstractmethod
    def config_schema(self) -> "ConfigSchema":
        ...

    @abstractmethod
    def list_all_songs(self) -> list[Song]:
        ...

    def cleanup(self) -> bool:
        return True


class Listener(ABC):
    def __init__(self) -> None:
        self.logger: Logger | None = None
        self.instance_config: dict = {}

    def set_instance(self, instance_id: str, instance_config: dict) -> None:
        self.logger = get_logger(instance_id)
        self.instance_config = instance_config

        self.logger.info(f'Listener {Colors.dim}"{instance_id}"{Colors.reset} instantiated')

    @property
    @abstractmethod
    def config_schema(self) -> "ConfigSchema":
        ...

    @abstractmethod
    def play(self, song: Song) -> None:
        ...

    def cleanup(self) -> bool:
        return True


class ExtensionManifesto(ABC):
    @property
    @abstractmethod
    def extension_id(self) -> str:
        ...

    def get_providers(self) -> list[Type[Provider]]:
        return []

    def get_listeners(self) -> list[Type[Listener]]:
        return []