from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import TYPE_CHECKING, Any, Type, TypeVar

from .models import Song

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

from .logging import get_logger


@dataclass
class NodeManifest:
    node_name: str
    default_config: dict[str, Any] = field(default_factory=lambda: {})


@dataclass
class NodeInstancePath:
    plugin_name: str = field(default_factory=lambda: "")
    node_type: str = field(default_factory=lambda: "")
    node_name: str = field(default_factory=lambda: "")
    instance_name: str = field(default_factory=lambda: "")

    def sanitize(self, string: str) -> str:
        return string.replace("&", "&&").replace(">", "&>")

    def __str__(self) -> str:
        return (
            f"{self.sanitize(self.plugin_name)}"
            + f">{self.sanitize(self.node_type)}"
            + f">{self.sanitize(self.node_name)}"
            + f">{self.sanitize(self.instance_name)}"
        )


def deserialize_node_instance_path(
    serialized_node_instance_path: str,
) -> NodeInstancePath:
    deserialized_data = ["", "", "", ""]
    deserialized_index = 0

    escape_next = False
    for character in serialized_node_instance_path:
        if character == "&" and not escape_next:
            escape_next = True
            continue

        if character == ">" and not escape_next:
            deserialized_index += 1
            continue

        deserialized_data[deserialized_index] += character

    return NodeInstancePath(
        plugin_name=deserialized_data[0],
        node_type=deserialized_data[1],
        node_name=deserialized_data[2],
        instance_name=deserialized_data[3],
    )


class Node(ABC):
    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        self.config = config
        self.node_instance_path = node_instance_path

    def get_logger(self) -> Logger:
        return get_logger(str(self.node_instance_path))

    @classmethod
    @abstractmethod
    def get_node_manifest(cls) -> NodeManifest:
        ...

    @staticmethod
    def extra_node_default_configs() -> dict[str, Any]:
        return {}

    def cleanup(self) -> bool:
        return True


NodeSubclass = TypeVar("NodeSubclass", bound=Node)


class Controller(Node, ABC):
    def __init__(
        self,
        config: dict[str, Any],
        node_instance_path: NodeInstancePath,
        orchestrator: "Orchestrator",
    ) -> None:
        super().__init__(config, node_instance_path)

        self.orchestrator = orchestrator

    @abstractmethod
    def start(self) -> None:
        ...


class Provider(Node, ABC):
    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        super().__init__(config, node_instance_path)

    @abstractmethod
    def get_all_songs(self) -> list[Song]:
        ...

    @abstractmethod
    def get_song(self, serialized_song_id: str) -> Song | None:
        ...


class Listener(Node, ABC):
    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        super().__init__(config, node_instance_path)

    @staticmethod
    def extra_node_default_configs() -> dict[str, Any]:
        return {"channels": ["main"]}

    @abstractmethod
    def play(self, song: Song) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...


class PluginManifest:
    def __init__(self) -> None:
        self._logger = get_logger(__name__)
        self.controllers: set[Type[Controller]] = set()
        self.providers: set[Type[Provider]] = set()
        self.listeners: set[Type[Listener]] = set()

    def sanity_check(self) -> bool:
        node_names: set[str] = set()

        for node in self.controllers | self.providers | self.listeners:
            node_name = node.get_node_manifest().node_name

            if node_name in node_names:
                self._logger.error(
                    (
                        f"The node {node.__name__} has tried to register"
                        + f" the name {node_name} in its manifest"
                        + "but it has already been registered"
                    )
                )
                return False

            node_names.add(node_name)

        return True
