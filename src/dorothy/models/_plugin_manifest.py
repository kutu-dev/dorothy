from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Type, TypeVar, Callable
from typing_extensions import override
from logging import getLogger
from dataclasses import dataclass, field

from ..exceptions import NodeFailureException

if TYPE_CHECKING:
    from .._orchestrator import Orchestrator

from ._node import NodeInstancePath, Node
from ._controller import Controller
from ._album import Album
from ._provider import Provider
from ._listener import Listener
from ._artist import Artist


@dataclass
class PluginManifest:
    """A class that holds all the nodes provided by a plugin."""

    controllers: set[Type[Controller]] = field(default_factory=lambda: set())
    providers: set[Type[Provider]] = field(default_factory=lambda: set())
    listeners: set[Type[Listener]] = field(default_factory=lambda: set())

    def sanity_check(self) -> bool:
        """Check if the unique names assigned for each node are in fact unique.

        Returns:
            Returns true if the unique names have been assigned uniquely and false otherwise.
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
