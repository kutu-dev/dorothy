from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Type
from . import Colors
from .config import ConfigSchema, ConfigManager
from .logging import get_logger
import pkgutil
import importlib
import sys
from .models import Song, Provider, Listener, ExtensionManifesto, Controller

# This import is needed by iter_modules to detect the extensions
import dorothy.ext


@dataclass
class Extensions:
    controllers: list[Controller] = field(default_factory=lambda: [])
    providers: list[Provider] = field(default_factory=lambda: [])
    listeners: list[Listener] = field(default_factory=lambda: [])


# TODO This should be refactor to be less ugly
def load_extensions(config_manager: ConfigManager) -> Extensions:
    extensions = Extensions()
    logger = get_logger(__name__)

    extension_modules = list(pkgutil.iter_modules(dorothy.ext.__path__, dorothy.ext.__name__ + "."))
    logger.info(f"Found {len(extension_modules)} extension(s), loading them...")

    for _, name, _ in extension_modules:
        importlib.import_module(name)
        manifesto: ExtensionManifesto = sys.modules[name].Manifesto()

        logger.info(f'Loading extension {Colors.dim}"{manifesto.extension_id}"{Colors.reset}...')

        for controller in manifesto.get_controllers():
            logger.info(f'Loading controller {Colors.dim}"{controller.config_schema.node_id}"{Colors.reset}...')

            extensions.controllers.extend(config_manager.node_factory(manifesto.extension_id, controller))

        for provider in manifesto.get_providers():
            logger.info(f'Loading provider {Colors.dim}"{provider.config_schema.node_id}"{Colors.reset}...')

            extensions.providers.extend(config_manager.node_factory(manifesto.extension_id, provider))

        for listener in manifesto.get_listeners():
            logger.info(f'Loading listener {Colors.dim}"{listener.config_schema.node_id}"{Colors.reset}...')
            extensions.listeners.extend(config_manager.node_factory(manifesto.extension_id, listener))

    return extensions
