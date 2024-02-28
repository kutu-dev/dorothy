from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type


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


class Resource(ABC):
    @staticmethod
    @abstractmethod
    def resource_name() -> str:
        ...


@dataclass
class ResourceId:
    resource_type: Type[Resource]
    node_instance_path: NodeInstancePath
    unique_id: str

    def sanitize(self, string: str) -> str:
        return string.replace("&", "&&").replace("@", "&@")

    def __str__(self) -> str:
        return (
            f"{self.sanitize(self.resource_type.resource_name())}"
            + f"@{self.sanitize(str(self.node_instance_path))}"
            + f"@{self.sanitize(self.unique_id)}"
        )


class Song(Resource):
    def __init__(
        self, resource_id: ResourceId, uri: str, duration: int, title: str | None = None, album_name: str | None = None, artist_name: str | None = None
    ) -> None:
        self.resource_id = resource_id
        self.uri = uri
        self.duration = duration
        self.title = title
        self.album_name = album_name
        self.artist_name = artist_name

    def dict(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "uri": self.uri,
            "duration": self.duration,
            "title": self.title,
            "album_name": self.album_name,
            "artist_name": self.artist_name
        }

    @staticmethod
    def resource_name() -> str:
        return "song"


class Album(Resource):
    def __init__(
        self,
        resource_id: ResourceId,
        title: str | None = None,
        song_list: list[Song] | None = None
    ) -> None:
        self.resource_id = resource_id
        self.title = title
        self.song_list = song_list

    def dict(self) -> dict[str, Any]:
        return {
            "resource_id": str(self.resource_id),
            "title": self.title,
            "song_list": [song.dict() for song in self.song_list]
        }

    @staticmethod
    def resource_name() -> str:
        return "album"


def deserialize_resource_id(serialized_resource: str) -> ResourceId:
    deserialized_data = ["", "", ""]
    deserialized_index = 0

    escape_next = False
    for character in serialized_resource:
        if character == "&" and not escape_next:
            escape_next = True
            continue

        if character == "@" and not escape_next:
            if deserialized_index < 2:
                deserialized_index += 1
            continue

        deserialized_data[deserialized_index] += character

    resource_type: Type[Resource]
    match deserialized_data[0]:
        case "song":
            resource_type = Song
        case "album":
            resource_type = Album
        case _:
            raise ValueError(f"Unknown resource type: {deserialized_data[0]}")

    return ResourceId(
        resource_type,
        nodes.deserialize_node_instance_path(deserialized_data[1]),
        deserialized_data[2],
    )
