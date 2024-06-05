from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Type, TypeVar, Callable
from typing_extensions import override
from logging import getLogger

from ..exceptions import NodeFailureException

if TYPE_CHECKING:
    from .._orchestrator import Orchestrator

from ._node import NodeInstancePath, Node
from ._album import Album
from ._artist import Artist
from ._song import Song


class Listener(Node, ABC):
    """A node that plays URIs provided by Dorothy."""

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The listener node constructor method.

        Args:
            config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
            node_instance_path: The unique path of the node instance.
        """

        super().__init__(config, node_instance_path)

    @staticmethod
    @override
    def extra_node_default_configs() -> dict[str, Any]:
        return {"channels": ["main"]}

    def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        Returns:
            None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    def play(self, song: Song) -> None:
        """Start playing the current song.

        Args:
            song: The song to play.
        """

        ...

    @abstractmethod
    def pause(self) -> None:
        """Pause the current playing song if there is any."""

        ...

    @abstractmethod
    def stop(self) -> None:
        """Stops the current playing song if there is any."""

        ...
