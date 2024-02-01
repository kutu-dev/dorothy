import importlib
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import Type

# This import is needed by iter_modules to detect the plugins
import dorothy.plugins

from .channel import Channel
from .config import ConfigManager
from .logging import get_logger
from .nodes import Controller, Listener, NodeInstancePath, PluginManifest, Provider
from .orchestrator import Orchestrator


@dataclass
class InstanciatedNodes:
    orchestrator: Orchestrator
    controllers: list[Controller] = field(default_factory=lambda: [])


@dataclass
class PluginNodeTypes:
    plugin_name: str = field(default_factory=lambda: "")
    controllers: set[Type[Controller]] = field(default_factory=lambda: set())
    providers: set[Type[Provider]] = field(default_factory=lambda: set())
    listeners: set[Type[Listener]] = field(default_factory=lambda: set())


class PluginHandler:
    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager
        self._logger = get_logger(__name__)

    def load_nodes(self) -> InstanciatedNodes:
        plugins_node_types = self.get_node_types_from_plugins()

        return self.instantiate_nodes(plugins_node_types)

    def get_node_types_from_plugins(self) -> list[PluginNodeTypes]:
        plugins_node_types: list[PluginNodeTypes] = []

        plugin_modules = list(pkgutil.iter_modules(dorothy.plugins.__path__))
        self._logger.info(f"Found {len(plugin_modules)} plugin(s), loading them...")

        for _, name, _ in plugin_modules:
            full_module_name = f"{dorothy.plugins.__name__}.{name}"
            importlib.import_module(full_module_name)
            self._logger.info(f'Loading plugin "{name}"')

            manifest: PluginManifest = sys.modules[
                full_module_name
            ].get_plugin_manifest()

            if not manifest.sanity_check():
                self._logger.error(
                    "Sanity check of the loading plugin has failed, skipping it..."
                )
                continue

            plugins_node_types.append(
                PluginNodeTypes(
                    plugin_name=name,
                    controllers=manifest.controllers,
                    providers=manifest.providers,
                    listeners=manifest.listeners,
                )
            )

        return plugins_node_types

    def instantiate_nodes(
        self, plugins_node_types: list[PluginNodeTypes]
    ) -> InstanciatedNodes:
        orchestrator = Orchestrator()
        controllers: list[Controller] = []

        for plugin in plugins_node_types:
            controllers.extend(
                self.instantiate_controllers(
                    orchestrator, plugin.plugin_name, plugin.controllers
                )
            )

            orchestrator.providers[plugin.plugin_name] = self.instantiate_providers(
                plugin.plugin_name, plugin.providers
            )

            for channel, listeners in self.instantiate_listeners(
                plugin.plugin_name, plugin.listeners
            ).items():
                if channel not in orchestrator.channels:
                    orchestrator.channels[channel] = Channel(channel)

                orchestrator.channels[channel].listeners.extend(listeners)

        return InstanciatedNodes(orchestrator=orchestrator, controllers=controllers)

    def instantiate_controllers(
        self,
        orchestrator: Orchestrator,
        plugin_name: str,
        controllers_types: set[Type[Controller]],
    ) -> list[Controller]:
        controllers: list[Controller] = []

        for controller in controllers_types:
            controller_config = self._config_manager.handle_node_config(
                plugin_name, controller
            )

            for instance_name, instance_config in controller_config.items():
                node_instance_path = NodeInstancePath(
                    plugin_name,
                    "controller",
                    controller.get_node_manifest().node_name,
                    instance_name,
                )

                controllers.append(
                    controller(instance_config, node_instance_path, orchestrator)
                )

        return controllers

    def instantiate_providers(
        self, plugin_name: str, providers_types: set[Type[Provider]]
    ) -> dict[str, dict[str, Provider]]:
        providers: dict[str, dict[str, Provider]] = {}

        for provider in providers_types:
            provider_config = self._config_manager.handle_node_config(
                plugin_name, provider
            )

            provider_name = provider.get_node_manifest().node_name
            providers[provider_name] = {}
            for instance_name, instance_config in provider_config.items():
                node_instance_path = NodeInstancePath(
                    plugin_name, "provider", provider_name, instance_name
                )

                providers[provider_name][instance_name] = provider(
                    instance_config, node_instance_path
                )

        return providers

    def instantiate_listeners(
        self, plugin_name: str, listener_types: set[Type[Listener]]
    ) -> dict[str, list[Listener]]:
        listeners_to_channels: dict[str, list[Listener]] = {}

        for listener in listener_types:
            listener_config = self._config_manager.handle_node_config(
                plugin_name, listener
            )

            listener_name = listener.get_node_manifest().node_name
            for instance_name, instance_config in listener_config.items():
                for channel in instance_config["channels"]:
                    if channel not in listeners_to_channels:
                        listeners_to_channels[channel] = []

                    node_instance_path = NodeInstancePath(
                        plugin_name, "listener", listener_name, instance_name
                    )

                    listeners_to_channels[channel].append(
                        listener(instance_config, node_instance_path)
                    )

        return listeners_to_channels
