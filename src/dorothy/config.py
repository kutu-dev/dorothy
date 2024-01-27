from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, TypeVar, Any

import toml

from . import Colors
from .logging import get_logger
from .models import Listener, Node


@dataclass
class ConfigSchema:
    node_id: str
    node_type: Type[Node]
    default_config: dict[Any, Any] = field(default_factory=lambda: {})


NodeDerivated = TypeVar("NodeDerivated", bound=Node)


class ConfigManager:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.base_config_path: Path = Path(
            "/home/kutu/documents/dev/projects/dorothy/CONFIG"
        )

        # Ensure the global config directory is available
        self.base_config_path.mkdir(parents=True, exist_ok=True)

    # TODO Simplify and reduce nesting in this function.
    #  Only God really knows the code flow here. Good luck, stay safe.
    def node_factory(
        self, extension_id: str, node: Type[NodeDerivated]
    ) -> list[NodeDerivated]:
        if not node.config_schema:
            self.logger.error(
                f'Unknown node from extension {Colors.dim}"{extension_id}"{Colors.reset} is missing its config schema, {Colors.purple}skipping{Colors.reset} it...'
            )
            return []

        extension_config_path = self.base_config_path / extension_id
        node_id = node.config_schema.node_id
        node_config_path = extension_config_path / f"{node_id}.toml"

        if not extension_config_path.is_dir():
            self.logger.info("Extension directory is missing, creating one...")
            extension_config_path.mkdir()

        if not node_config_path.is_file():
            self.logger.info(
                f'Node {Colors.dim}"{node_id}"{Colors.reset} doesn\'t have a config file, generating one now and {Colors.purple}skipping{Colors.reset} the node...'
            )
            self.generate_config(node_config_path, node.config_schema)

            # Just return as the default config have the node always disabled
            return []

        nodes: list[NodeDerivated] = []
        with open(node_config_path, "r") as f:
            node_config = toml.load(f)

            self.logger.info(
                f'Loading instances of node {Colors.dim}"{node_id}"{Colors.reset}...'
            )
            for instance_name, instance_config in node_config.items():
                if not instance_config["enabled"]:
                    self.logger.info(
                        f'Node instance {Colors.dim}"{instance_name}"{Colors.reset} is {Colors.red}disabled{Colors.reset}, skipping...'
                    )
                    continue

                self.logger.info(
                    f'Node instance {Colors.dim}"{instance_name}"{Colors.reset} {Colors.blue}loaded{Colors.reset}'
                )

                if not (
                    "channels" in instance_config
                    and len(instance_config["channels"]) > 1
                ):
                    new_instance = node()
                    new_instance.setup_instance(
                        f"{node_id}-instance-{instance_name}", instance_config
                    )
                    nodes.append(new_instance)

                    continue

                self.logger.info(
                    f'Detected multiple channels targeted for instance {Colors.dim}"{instance_name}"{Colors.reset}, loading each one...'
                )

                already_used_channels: dict[str, int] = {}
                for channel in instance_config["channels"]:
                    self.logger.info(
                        f'Assigned instance {Colors.dim}"{instance_name}"{Colors.reset} to channel {Colors.dim}"{channel}"{Colors.reset}'
                    )

                    if channel not in already_used_channels:
                        already_used_channels[channel] = 1
                    else:
                        already_used_channels[channel] += 1

                    new_instance = node()

                    # Make another copy as dicts works by reference
                    # and remove the others channels from the instance config
                    modified_instance_config = dict(node_config)
                    modified_instance_config["channel"] = [channel]

                    new_instance.setup_instance(
                        f"{node_id}-instance-{instance_name}-{str(channel)}-{already_used_channels[channel]}",
                        modified_instance_config,
                    )
                    nodes.append(new_instance)

            return nodes

    @staticmethod
    def generate_config(node_config_path: Path, config_schema: ConfigSchema) -> None:
        node_config_path.touch()
        default_config = {"default": {"enabled": False, **config_schema.default_config}}

        if config_schema.node_type is Listener:
            default_config["default"]["channels"] = []

        with open(node_config_path, "w+") as f:
            toml.dump(default_config, f)
