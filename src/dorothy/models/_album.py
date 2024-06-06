from abc import ABC, abstractmethod
from ._resource_id import ResourceId
from ._song import Song
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type


class AlbumResourceId(ResourceId):
    """The resource id of an album."""

    def resource_name(self) -> str:
        return "album"


@dataclass
class Album:
    """Dataclass that holds all the relevant information of a album."""

    resource_id: AlbumResourceId
    title: str | None = field(default_factory=lambda: None)
    songs: list[Song] | None = field(default_factory=lambda: None)

    def dict(self) -> dict[str, Any]:
        """Function that returns a dictionary representation of an album."""

        return {
            "resource_id": str(self.resource_id),
            "title": self.title,
            "songs": [song.dict() for song in self.songs] if self.songs else None,
        }
