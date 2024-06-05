import importlib
import pkgutil
import sys
from dataclasses import dataclass, field
from logging import getLogger
from typing import Type, Tuple

# This import is needed by iter_modules to detect the plugins
import dorothy.plugins

from ._channel import Channel
from ._config import ConfigManager
from .models._node import NodeInstancePath
from .models._plugin_manifest import PluginManifest
from .models._controller import Controller
from .models._provider import Provider
from .models._listener import Listener
from ._orchestrator import Orchestrator


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
        self._logger.info(
            f"Found {len(plugins_modules)} plugin(s), loading them...")

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
        """Set up all the nodes declared in its pluins.

        Args:
            plugins_data: List with all the data of all the plugins
                to initialize its nodes.

        Raises:
            ValueError: Raised when an unknown node type is found.

        Returns:
            An orchestrator that holds all the providers and listeners.
            A list of controllers that have control of the orchestrator.
        """

        orchestrator = Orchestrator()
        controllers: list[Controller] = []

        for plugin in plugins_data:
            for node in plugin.controllers | plugin.providers | plugin.listeners:
                node_manifest = node.get_node_manifest()
                node_config = self._config_manager.handle_node_config(
                    plugin.name, node)

                self._logger.info(
                    f'Loading node "{node_manifest.name}" from '
                    + f'plugin "{plugin.name}"'
                )

                for instance_name, instance_config in node_config.items():
                    if instance_config["disabled"]:
                        self._logger.info(
                            f'The instance "{instance_name}" is '
                            + "disabled, skipping it..."
                        )
                        continue

                    node_instance_path = NodeInstancePath(
                        plugin_name=plugin.name,
                        node_name=node_manifest.name,
                        instance_name=instance_name,
                    )

                    if issubclass(node, Controller):
                        node_instance_path.node_type = "controller"

                        controllers.append(
                            node(instance_config, node_instance_path, orchestrator)
                        )

                    elif issubclass(node, Provider):
                        node_instance_path.node_type = "provider"

                        if plugin.name not in orchestrator._providers:
                            orchestrator._providers[plugin.name] = {}

                        if (
                            node_manifest.name
                            not in orchestrator._providers[plugin.name]
                        ):
                            orchestrator._providers[plugin.name][
                                node_manifest.name
                            ] = {}

                        orchestrator._providers[plugin.name][node_manifest.name][
                            instance_name
                        ] = node(instance_config, node_instance_path)

                    elif issubclass(node, Listener):
                        node_instance_path.node_type = "listener"

                        for channel in instance_config["channels"]:
                            if channel not in orchestrator._channels:
                                orchestrator._channels[channel] = Channel(
                                    channel)

                            orchestrator._channels[channel]._listeners.append(
                                node(
                                    instance_config,
                                    node_instance_path,
                                )
                            )

                    else:
                        raise ValueError(f'Unknown node type of node "{node}"')

        return orchestrator, controllers
