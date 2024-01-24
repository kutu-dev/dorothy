from typing import Type

from src.dorothy.ext.http.controllers import HttpController
from src.dorothy.models import ExtensionManifesto, Controller


class Manifesto(ExtensionManifesto):
    extension_id = "http"

    def get_controllers(self) -> list[Type[Controller]]:
        return [
            HttpController
        ]
