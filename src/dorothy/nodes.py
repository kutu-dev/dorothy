from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type, TypeVar, Callable
from typing_extensions import override
from logging import getLogger

from .exceptions import NodeFailureException

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

from .models import NodeInstancePath, Song, Album, Artist


@dataclass
class NodeManifest:
    """A dataclass that holds all the relevant data that a node can give before its instantiation."""

    name: str
    default_config: dict[str, Any] = field(default_factory=lambda: {})


class Node(ABC):
    """Abstract class that holds the implementation that all nodes should inherit from."""

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The node constructor method.

        :param config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
        :param node_instance_path: The unique path of the node instance.
        """

        self.config = config
        self.node_instance_path = node_instance_path
        self._logger = getLogger(str(self.node_instance_path))

    @staticmethod
    @abstractmethod
    def get_node_manifest() -> NodeManifest:
        """A function that returns a NodeManifest containing all relevant data that a node can give.

        :return: A node manifest instance.
        """

        ...

    @staticmethod
    def extra_node_default_configs() -> dict[str, Any]:
        """An overrideable function that returns extra parameters to be added to the default config that was given
        by the base node and the node implementation.

        :return: The extra config to be added to the default config of the node.
        """

        return {}

    def raise_failure_node_exception(self, message: str, exception: type[NodeFailureException] = NodeFailureException) -> None:
        """

        :param message:
        :param exception:
        :return:
        """

        self._logger.error(
            f'Node "{self.node_instance_path}" has raised a "{exception.__name__}" exception with the message: {message}'
        )
        raise exception()


NODE_SUBCLASS = TypeVar("NODE_SUBCLASS", bound=Node)


class Controller(Node, ABC):
    """A node that can be used to control Dorothy using an orchestrator object."""

    def __init__(
        self,
        config: dict[str, Any],
        node_instance_path: NodeInstancePath,
        orchestrator: "Orchestrator",
    ) -> None:
        """The controller node constructor method.

        :param config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
        :param node_instance_path: The unique path of the node instance.
        :param orchestrator: An orchestrator object that can be used to control most of the systems in Dorothy.
        """

        super().__init__(config, node_instance_path)

        self.orchestrator = orchestrator

    async def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        :return: None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    async def start(self) -> None:
        """An async method that is called when the controller is started in the mainloop.
        This method should avoid be executed for a long time.
        """

        ...


class Provider(Node, ABC):
    """A node that provides all the resources consumed by the rest of Dorothy.

    Internally you will be given with unique ids which are open for be implemented as desired,
    depending on the node functionalities.
    """

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The provider node constructor method.

        :param config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
        :param node_instance_path: The unique path of the node instance.
        """

        super().__init__(config, node_instance_path)

    def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        :return: None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    def get_song(self, unique_song_id: str) -> Song | None:
        """Gets a song by its unique id.

        :param unique_song_id: The given unique id.
        :return: An object of the requested song.
        """

        ...

    @abstractmethod
    def get_all_songs(self) -> list[Song]:
        """Returns a list of all the songs available by the provider.

        :return: The list of available songs.
        """

        ...

    @abstractmethod
    def get_album(self, unique_album_id: str) -> Album | None:
        """Gets an album by its unique id.

        :param unique_album_id: The given unique id.
        :return: An object of the requested album.
        """

        ...

    @abstractmethod
    def get_all_albums(self) -> list[Album]:
        """Returns a list of all the albums available by the provider.

        :return: The list of available albums.
        """

        ...

    @abstractmethod
    def get_artist(self, unique_artist_id: str) -> Artist | None:
        """Gets an artist by its unique id.

        :param unique_artist_id: The given unique id.
        :return: An object of the requested artist.
        """

        ...

    @abstractmethod
    def get_all_artists(self) -> list[Artist]:
        """Returns a list of all the artists available by the provider.

        :return: The list of available artists.
        """

        ...


class Listener(Node, ABC):
    """A node that plays URIs provided by Dorothy."""

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The listener node constructor method.

        :param config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
        :param node_instance_path: The unique path of the node instance.
        """

        super().__init__(config, node_instance_path)

    @staticmethod
    @override
    def extra_node_default_configs() -> dict[str, Any]:
        return {"channels": ["main"]}

    def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        :return: None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    def play(self, song: Song) -> None:
        """Start playing the current song.

        :param song: The song to play.
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


@dataclass
class PluginManifest:
    """A class that holds all the nodes provided by a plugin."""

    controllers: set[Type[Controller]] = field(default_factory=lambda: set())
    providers: set[Type[Provider]] = field(default_factory=lambda: set())
    listeners: set[Type[Listener]] = field(default_factory=lambda: set())

    def sanity_check(self) -> bool:
        """Check if the unique names assigned for each node are in fact unique.

        :return: Returns true if the unique names have been assigned uniquely and false otherwise.
        """

        node_names: set[str] = set()

        for node in self.controllers | self.providers | self.listeners:
            node_name = node.get_node_manifest().name

            if node_name in node_names:
                _logger = getLogger(__name__)
                _logger.error(
                    (
                        f"The node {node.__name__} has tried to register"
                        + f" the name {node_name} in its manifest"
                        + "but it has already been registered"
                    )
                )
                return False

            node_names.add(node_name)

        return True
