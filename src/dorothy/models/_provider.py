from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Type, TypeVar, Callable
from typing_extensions import override
from logging import getLogger

from ..exceptions import NodeFailureException

if TYPE_CHECKING:
    from .._orchestrator import Orchestrator

from ._node import NodeInstancePath, Node
from ._song import Song
from ._album import Album
from ._artist import Artist


class Provider(Node, ABC):
    """A node that provides all the resources consumed by the rest of Dorothy.

    Internally you will be given with unique ids which are open for be implemented as desired,
    depending on the node functionalities.
    """

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The provider node constructor method.

        Args:
            config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
            node_instance_path: The unique path of the node instance.
        """

        super().__init__(config, node_instance_path)

    def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        Returns:
            None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    def get_song(self, unique_song_id: str) -> Song | None:
        """Gets a song by its unique id.

        Args:
            unique_song_id: The given unique id.

        Returns:
            An object of the requested song.
        """

        ...

    @abstractmethod
    def get_all_songs(self) -> list[Song]:
        """Returns a list of all the songs available by the provider.

        Returns:
            The list of available songs.
        """

        ...

    @abstractmethod
    def get_album(self, unique_album_id: str) -> Album | None:
        """Gets an album by its unique id.

        Args:
            unique_album_id: The given unique id.

        Returns:
            An object of the requested album.
        """

        ...

    @abstractmethod
    def get_all_albums(self) -> list[Album]:
        """Returns a list of all the albums available by the provider.

        Returns:
            The list of available albums.
        """

        ...

    @abstractmethod
    def get_artist(self, unique_artist_id: str) -> Artist | None:
        """Gets an artist by its unique id.

        Args:
            unique_artist_id: The given unique id.

        Returns:
            An object of the requested artist.
        """

        ...

    @abstractmethod
    def get_all_artists(self) -> list[Artist]:
        """Returns a list of all the artists available by the provider.

        Returns:
            The list of available artists.
        """

        ...
