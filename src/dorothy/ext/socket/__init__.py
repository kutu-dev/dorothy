from typing import Type

from dorothy.ext.socket.controllers import SocketController
from dorothy.models import ExtensionManifesto, Controller


class Manifesto(ExtensionManifesto):
    extension_id = "socket"

    def get_controllers(self) -> list[Type[Controller]]:
        return [
            SocketController
        ]
