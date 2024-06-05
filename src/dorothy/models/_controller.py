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


class Controller(Node, ABC):
    """A node that can be used to control Dorothy using an orchestrator object."""

    def __init__(
        self,
        config: dict[str, Any],
        node_instance_path: NodeInstancePath,
        orchestrator: "Orchestrator",
    ) -> None:
        """The controller node constructor method.

        Args:
            config: A dictionary that contains all the configurations defined by the system, the node manifest and the node type.
            node_instance_path: The unique path of the node instance.
            orchestrator: An orchestrator object that can be used to control most of the systems in Dorothy.
        """

        super().__init__(config, node_instance_path)

        self.orchestrator = orchestrator

    async def cleanup(self) -> None | str:
        """An overrideable function that is run when the application is shutting down,
        should return None when the cleanup is successful or an error in a string to notify the user of the incidence.

        Returns:
            None when everything is ok or an error in a string if something gone wrong
        """

        return None

    @abstractmethod
    async def start(self) -> None:
        """An async method that is called when the controller is started in the mainloop.
        This method should avoid be executed for a long time.
        """

        ...
