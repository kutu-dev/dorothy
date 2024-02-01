from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self, Type, TypeVar

if TYPE_CHECKING:
    from dorothy.nodes import NodeInstancePath


class Resource(ABC):
    @abstractmethod
    def resource_name(self) -> str:
        ...


ResourceSubclass = TypeVar("ResourceSubclass", bound=Resource)


@dataclass
class ResourceId:
    resource_type: Type[ResourceSubclass]
    node_instance_path: "NodeInstancePath"
    unique_id: str

    @classmethod
    def deserialize(cls, serialized_resource: str) -> Self:
        ...

    def sanitize(self, string: str) -> str:
        return string.replace("&", "&&").replace("#", "&#")

    def __str__(self):
        return f"{self.sanitize(self.resource_type.resource_name())}#{self.sanitize(str(self.node_instance_path))}#{self.sanitize(self.unique_id)}"


class Song:
    def __init__(
        self, resource_id: ResourceId, uri: str | None = None, title: str | None = None
    ) -> None:
        self.resource_id = resource_id
        self.uri = uri
        self.title = title

    @property
    def __dict__(self) -> dict[str, Any]:
        return {"id": vars(self.resource_id), "uri": self.uri, "title": self.title}

    @__dict__.setter
    def __dict__(self, value: dict[str, Any]) -> None:
        self.dict = value

    @classmethod
    def resource_name(cls) -> str:
        return "song"
