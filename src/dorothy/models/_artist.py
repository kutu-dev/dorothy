from abc import ABC, abstractmethod
from ._resource_id import ResourceId
from dataclasses import dataclass, field
from ._album import Album
from typing import TYPE_CHECKING, Any, Type


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
            "albums": [album.dict() for album in self.albums] if self.albums else None,
        }
