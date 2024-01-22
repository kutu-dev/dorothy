from abc import ABC, abstractmethod
from typing import Any

from . import Colors
from .logging import get_logger
import pkgutil
import importlib
import dorothy.ext.providers
import sys

from .models import Song


class Provider(ABC):
    def __init__(self, name: str) -> None:
        self.logger = get_logger(name)
        self.logger.info(f"Provider instantiated")

    @abstractmethod
    def list_all_songs(self) -> list[Song]:
        pass

    @abstractmethod
    def get_uri(self, id_: Any) -> str:
        pass


def load_extensions() -> list[Provider]:
    providers: list[Provider] = []
    logger = get_logger(__name__)

    providers_modules = list(pkgutil.iter_modules(dorothy.ext.providers.__path__, dorothy.ext.providers.__name__ + "."))
    logger.info(f"Found {len(providers_modules)} provider(s), loading them...")

    for _, name, _ in providers_modules:
        importlib.import_module(name)

        for provider in sys.modules[name].Manifesto.get_providers():
            logger.info(f'Loading provider {Colors.dim}"{provider.__name__}"{Colors.reset}...')
            providers.append(provider())

    return providers
