import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type, TypeVar


if TYPE_CHECKING:
    from .orchestrator import Orchestrator

from .models import NodeInstancePath, Resource, ResourceId, Song, Album

from .logging import get_logger


@dataclass
class NodeManifest:
    node_name: str
    default_config: dict[str, Any] = field(default_factory=lambda: {})




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
        self._logger: logging.Logger | None = None

    @classmethod
    @abstractmethod
    def get_node_manifest(cls) -> NodeManifest:
        ...

    @staticmethod
    def extra_node_default_configs() -> dict[str, Any]:
        return {}

    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = get_logger(str(self.node_instance_path))

        return self._logger

    def create_resource_id(self, resource_type: Type[Resource], unique_id: str) -> ResourceId:
        return ResourceId(resource_type, self.node_instance_path, unique_id)

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
    async def start(self) -> None:
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
    def get_song(self, unique_song_id: str) -> "Song | None":
        ...

    @abstractmethod
    def get_all_albums(self) -> list[Album]:
        ...

    @abstractmethod
    def get_album(self, unique_album_id: str) -> "Song | None":
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
    def pause(self) -> None:
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
