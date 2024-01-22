from typing import Type

from dorothy.extensions import Provider
from .providers import FilesystemProvider


class Manifesto:
    @staticmethod
    def get_providers() -> list[Type[Provider]]:
        return [
            FilesystemProvider
        ]
