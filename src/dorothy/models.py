from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Type

import dorothy.nodes as nodes

if TYPE_CHECKING:
    from .nodes import NodeInstancePath


class Resource(ABC):
    @staticmethod
    @abstractmethod
    def resource_name() -> str:
        ...


@dataclass
class ResourceId:
    resource_type: Type[Resource]
    node_instance_path: "NodeInstancePath"
    unique_id: str

    def sanitize(self, string: str) -> str:
        return string.replace("&", "&&").replace("#", "&#")

    def __str__(self) -> str:
        return (
            f"{self.sanitize(self.resource_type.resource_name())}"
            + f"#{self.sanitize(str(self.node_instance_path))}"
            + f"#{self.sanitize(self.unique_id)}"
        )


class Song(Resource):
    def __init__(
        self, resource_id: ResourceId, uri: str | None = None, title: str | None = None
    ) -> None:
        self.resource_id = resource_id
        self.uri = uri
        self.title = title

    @property
    def __dict__(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "uri": self.uri,
            "title": self.title,
        }

    @__dict__.setter
    def __dict__(self, value: dict[str, Any]) -> None:
        self.dict = value

    @staticmethod
    def resource_name() -> str:
        return "song"


def deserialize_resource_id(serialized_resource: str) -> ResourceId:
    deserialized_data = ["", "", ""]
    deserialized_index = 0

    escape_next = False
    for character in serialized_resource:
        if character == "&" and not escape_next:
            escape_next = True
            continue

        if character == "#" and not escape_next:
            if deserialized_index < 2:
                deserialized_index += 1
            continue

        deserialized_data[deserialized_index] += character

    return ResourceId(
        Song,
        nodes.deserialize_node_instance_path(deserialized_data[1]),
        deserialized_data[2],
    )
