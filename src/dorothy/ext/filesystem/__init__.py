from typing import Type

from dorothy.models import Provider, ExtensionManifesto
from .providers import FilesystemProvider


class Manifesto(ExtensionManifesto):
    extension_id = "filesystem"

    def get_providers(self) -> list[Type[Provider]]:
        return [
            FilesystemProvider
        ]
