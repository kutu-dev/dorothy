from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Type

import toml

from .logging import get_logger
from .nodes import Node, NodeSubclass


@dataclass
class ConfigSchema:
    node_id: str
    node_type: Type[Node]
    default_config: dict[Any, Any] = field(default_factory=lambda: {})


class ConfigManager:
    def __init__(self) -> None:
        self._logger = get_logger(__name__)
        self.base_config_path = self.get_base_config_path()

    def get_base_config_path(self) -> Path:
        fake_path = Path("/users/kutu/documents/dev/projects/dorothy/CONFIG")

        fake_path.mkdir(parents=True, exist_ok=True)
        return fake_path

    def handle_node_config(
        self, plugin_name: str, node: Type[NodeSubclass]
    ) -> dict[str, Any]:
        plugin_directory = self.base_config_path / plugin_name
        plugin_directory.mkdir(parents=True, exist_ok=True)

        node_manifest = node.get_node_manifest()
        node_config_file = plugin_directory / f"{node_manifest.node_name}.toml"
        if not node_config_file.is_file():
            node_config_file.touch()

            return self.generate_default_node_config(node_config_file, node)

        with open(node_config_file, "r") as f:
            node_config = toml.load(f)
            return node_config

    @staticmethod
    def generate_default_node_config(
        node_config_file: Path, node: Type[NodeSubclass]
    ) -> dict[str, Any]:
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
