from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type


@dataclass
class NodeInstancePath:
    """A class that represent the unique path of a node."""

    plugin_name: str = field(default_factory=lambda: "")
    node_type: str = field(default_factory=lambda: "")
    node_name: str = field(default_factory=lambda: "")
    instance_name: str = field(default_factory=lambda: "")

    @staticmethod
    def _sanitize(string: str) -> str:
        """Escapes any conflict character from the given string.

        :param string: The string to sanitize.
        :return: The sanitized string.
        """

        return string.replace("&", "&&").replace(">", "&>")

    def __str__(self) -> str:
        """Generates a string representation of the node instance path.

        :return: The string representation of the node instance path.
        """

        return (
            f"{self._sanitize(self.plugin_name)}"
            + f">{self._sanitize(self.node_type)}"
            + f">{self._sanitize(self.node_name)}"
            + f">{self._sanitize(self.instance_name)}"
        )


@dataclass
class ResourceId(ABC):
    """Dummy base class for all the resource id classes."""

    node_instance_path: NodeInstancePath
    unique_id: str

    @staticmethod
    def _sanitize(string: str) -> str:
        """Escapes any conflict character from the given string.

        :param string: The string to sanitize.
        :return: The sanitized string.
        """

        return string.replace("&", "&&").replace("@", "&@")

    @abstractmethod
    def resource_name(self) -> str:
        """Function that returns the string representation of the resource type."""
        
        ...

    def __str__(self) -> str:
        """Generates a string representation of the resource id.

        :return: The string representation of the resource id.
        """

        return (
            f"{self._sanitize(self.resource_name())}"
            + f"@{self._sanitize(str(self.node_instance_path))}"
            + f"@{self._sanitize(self.unique_id)}"
        )


class SongResourceId(ResourceId):
    """The resource id of a song."""
    
    def resource_name(self) -> str:
        return "song"


@dataclass
class Song:
    """Dataclass that holds all the relevant information of a song."""
    
    resource_id: SongResourceId
    uri: str
    duration: int
    title: str | None = field(default_factory=lambda: None)
    album_name: str | None = field(default_factory=lambda: None)
    artist_name: str | None = field(default_factory=lambda: None)

    def dict(self) -> dict[str, Any]:
        """Function that returns a dictionary representation of a song."""
        
        return {
            "resource_id": str(self.resource_id),
            "uri": self.uri,
            "duration": self.duration,
            "title": self.title,
            "album_name": self.album_name,
            "artist_name": self.artist_name,
        }


class AlbumResourceId(ResourceId):
    """The resource id of an album."""

    def resource_name(self) -> str:
        return "album"


class Album:
    """Dataclass that holds all the relevant information of a album."""
    
    resource_id: AlbumResourceId
    title: str | None = field(default_factory=lambda: None)
    song_list: list[Song] | None = field(default_factory=lambda: None)

    def dict(self) -> dict[str, Any]:
        """Function that returns a dictionary representation of an album."""
        
        return {
            "resource_id": str(self.resource_id),
            "title": self.title,
            "song_list": [song.dict() for song in self.song_list],
        }


class ArtistResourceId(ResourceId):
    """The resource id of an artist."""

    def resource_name(self) -> str:
        return "artist"


class Artist:
    """Dataclass that holds all the relevant information of a artist."""
    
    resource_id: ArtistResourceId
    name: str | None = field(default_factory=lambda: None)
    albums: list[Album] | None = field(default_factory=lambda: None)

    def dict(self) -> dict[str, Any]:
        """Function that returns a dictionary representation of an artist."""
        
        return {
            "resource_id": self.resource_id,
            "name": self.name,
            "albums": [album.dict() for album in self.albums],
        }
