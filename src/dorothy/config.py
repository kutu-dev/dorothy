from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Any, Type
import toml
from platformdirs import user_config_dir

from .nodes import Node, NODE_SUBCLASS


@dataclass
class ConfigSchema:
    node_id: str
    node_type: Type[Node]
    default_config: dict[Any, Any] = field(default_factory=lambda: {})


class ConfigManager:
    """A manager designed to handle configuration related tasks."""

    def __init__(self, custom_config_path: Path | None = None) -> None:
        self._logger = getLogger(__name__)
        self.config_path = (
            custom_config_path
            if custom_config_path is not None
            else user_config_dir("dorothy")
        )

    def handle_node_config(
        self, plugin_name: str, node: Type[NODE_SUBCLASS]
    ) -> dict[str, Any]:
        """Check if the node has a config file and returns its used defined config.

        :param plugin_name: The name of the plugin where the node is located.
        :param node: The node class to access its manifest.
        :return: A dictionary representing the node's config.
        """

        plugin_directory = self.config_path / plugin_name
        plugin_directory.mkdir(parents=True, exist_ok=True)

        node_manifest = node.get_node_manifest()
        node_config_file = plugin_directory / f"{node_manifest.name}.toml"
        if not node_config_file.is_file():
            node_config_file.touch()

            return self.generate_default_node_config(node_config_file, node)

        with open(node_config_file, "r") as f:
            node_config = toml.load(f)
            return node_config

    @staticmethod
    def generate_default_node_config(
        node_config_file: Path, node: Type[NODE_SUBCLASS]
    ) -> dict[str, Any]:
        """Generate a default config file for the given node.

        :param node_config_file: The path to the config of the node it's expected to exist.
        :param node: The node to get its default config values.
        :return: A dictionary representing the default node's config.
        """

        default_config = {
            "default": {
                "disabled": False,
                **node.extra_node_default_configs(),
                **node.get_node_manifest().default_config,
            }
        }

        with open(node_config_file, "w+") as f:
            toml.dump(default_config, f)

        return default_config
