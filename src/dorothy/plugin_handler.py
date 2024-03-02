import importlib
import pkgutil
import sys
from dataclasses import dataclass, field
from logging import getLogger
from typing import Type, Tuple

# This import is needed by iter_modules to detect the plugins
import dorothy.plugins

from .channel import Channel
from .config import ConfigManager
from .nodes import Controller, Listener, NodeInstancePath, PluginManifest, Provider
from .orchestrator import Orchestrator


@dataclass
class PluginData:
    name: str = field(default_factory=lambda: "")
    controllers: set[Type[Controller]] = field(default_factory=lambda: set())
    providers: set[Type[Provider]] = field(default_factory=lambda: set())
    listeners: set[Type[Listener]] = field(default_factory=lambda: set())


class PluginHandler:
    """A handled designed to load and start the nodes of the available plugins."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager
        self._logger = getLogger(__name__)

    def load_nodes(self) -> Tuple[Orchestrator, list[Controller]]:
        plugins_node_types = self._get_plugins_data()

        return self._instantiate_nodes(plugins_node_types)

    def _get_plugins_data(self) -> list[PluginData]:
        plugins_data: list[PluginData] = []

        plugins_modules = list(pkgutil.iter_modules(dorothy.plugins.__path__))
        self._logger.info(f"Found {len(plugins_modules)} plugin(s), loading them...")

        for _, name, _ in plugins_modules:
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

            plugins_data.append(
                PluginData(
                    name=name,
                    controllers=manifest.controllers,
                    providers=manifest.providers,
                    listeners=manifest.listeners,
                )
            )

        return plugins_data

    def _instantiate_nodes(
        self, plugins_data: list[PluginData]
    ) -> Tuple[Orchestrator, list[Controller]]:
        """Sets up all the nodes instantiated declared in the plugins

        :param plugins_data: A list of plugins and its declared nodes
        :return: An orchestrator with providers and listeners configured and a list of controllers to control it.
        """

        orchestrator = Orchestrator()
        controllers: list[Controller] = []

        for plugin in plugins_data:
            for node in plugin.controllers | plugin.providers | plugin.listeners:
                node_manifest = node.get_node_manifest()
                node_config = self._config_manager.handle_node_config(plugin.name, node)

                for instance_name, instance_config in node_config:
                    node_instance_path = NodeInstancePath(
                        plugin_name=plugin.name,
                        node_name=node_manifest.name,
                        instance_name=instance_name,
                    )

                    match node:
                        case Controller():
                            node_instance_path.node_type = "controller"

                            controllers.append(
                                node(instance_config, node_instance_path, instance_name)
                            )

                        case Provider():
                            node_instance_path.node_type = "provider"

                            orchestrator.providers[plugin.name][node_manifest.name][
                                instance_name
                            ] = node(instance_config, node_instance_path, instance_name)

                        case Listener():
                            node_instance_path.node_type = "listener"

                            for channel in instance_config["channels"]:
                                if channel not in orchestrator.channels:
                                    orchestrator.channels[channel] = Channel(channel)

                                orchestrator.channels[channel].listeners.append(
                                    node(
                                        instance_config,
                                        node_instance_path,
                                        instance_name,
                                    )
                                )

                        case _:
                            raise ValueError(f'Unknown node type of node "{node}"')

        return orchestrator, controllers
