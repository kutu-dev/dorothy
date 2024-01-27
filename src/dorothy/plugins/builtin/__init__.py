from typing import Type

from dorothy.models import PluginManifesto, Provider

from ...models import Controller, Listener
from .controllers import RestController
from .listeners import PlaybinListener
from .providers import FilesystemProvider


class Manifesto(PluginManifesto):
    extension_id = "builtin"

    def get_controllers(self) -> list[type[Controller]]:
        return [RestController]

    def get_providers(self) -> list[Type[Provider]]:
        return [FilesystemProvider]

    def get_listeners(self) -> list[Type[Listener]]:
        return [PlaybinListener]
