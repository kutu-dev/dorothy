from typing import Type

from .listeners import PlaybinListener
from dorothy.models import Listener, ExtensionManifesto


class Manifesto(ExtensionManifesto):
    extension_id = "playbin"

    def get_listeners(self) -> list[Type[Listener]]:
        return [
            PlaybinListener
        ]
