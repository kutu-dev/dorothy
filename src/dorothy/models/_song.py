from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type
from ._resource_id import ResourceId


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
