import importlib
import pkgutil
import sys
from dataclasses import dataclass, field

# This import is needed by iter_modules to detect the plugins
import dorothy.plugins

from . import Colors
from .config import ConfigManager
from .logging import get_logger
from .models import Controller, Listener, PluginManifesto, Provider


@dataclass
class Plugins:
    controllers: list[Controller] = field(default_factory=lambda: [])
    providers: dict[str, Provider] = field(default_factory=lambda: {})
    listeners: list[Listener] = field(default_factory=lambda: [])


# TODO This should be refactor to be less ugly
def load_plugins(config_manager: ConfigManager) -> Plugins:
    plugins = Plugins()
    logger = get_logger(__name__)

    plugin_modules = list(
        pkgutil.iter_modules(dorothy.plugins.__path__, dorothy.plugins.__name__ + ".")
    )
    logger.info(f"Found {len(plugin_modules)} plugin(s), loading them...")

    for _, name, _ in plugin_modules:
        importlib.import_module(name)
        manifesto: PluginManifesto = sys.modules[name].Manifesto()

        logger.info(
            f'Loading plugin {Colors.dim}"{manifesto.extension_id}"{Colors.reset}...'
        )

        for controller in manifesto.get_controllers():
            if not controller.config_schema:
                logger.error(
                    f'Unknown controller from extension {Colors.dim}"{manifesto.extension_id}"{Colors.reset} is missing its config schema, {Colors.purple}skipping{Colors.reset} it...'
                )
                continue

            logger.info(
                f'Loading controller {Colors.dim}"{controller.config_schema.node_id}"{Colors.reset}...'
            )

            plugins.controllers.extend(
                config_manager.node_factory(manifesto.extension_id, controller)
            )

        for provider in manifesto.get_providers():
            if not provider.config_schema:
                logger.error(
                    f'Unknown provider from extension {Colors.dim}"{manifesto.extension_id}"{Colors.reset} is missing its config schema, {Colors.purple}skipping{Colors.reset} it...'
                )
                continue

            logger.info(
                f'Loading provider {Colors.dim}"{provider.config_schema.node_id}"{Colors.reset}...'
            )

            new_providers = config_manager.node_factory(
                manifesto.extension_id, provider
            )

            for provider_instance in new_providers:
                plugins.providers[provider_instance.instance_id] = provider_instance

        for listener in manifesto.get_listeners():
            if not listener.config_schema:
                logger.error(
                    f'Unknown listener from extension {Colors.dim}"{manifesto.extension_id}"{Colors.reset} is missing its config schema, {Colors.purple}skipping{Colors.reset} it...'
                )
                continue

            logger.info(
                f'Loading listener {Colors.dim}"{listener.config_schema.node_id}"{Colors.reset}...'
            )
            plugins.listeners.extend(
                config_manager.node_factory(manifesto.extension_id, listener)
            )

    return plugins
