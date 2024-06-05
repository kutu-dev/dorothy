from dataclasses import dataclass, field
from ..exceptions import NodeFailureException
from typing import Any, TypeVar
from abc import ABC, abstractmethod
from logging import getLogger


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

        Args:
            string: The string to sanitize

        Returns:
            The sanitized string.
        """

        return string.replace("&", "&&").replace(">", "&>")

    def __str__(self) -> str:
        """Generates a string representation of the node instance path.

        Returns:
            The string representation of the node instance path.
        """

        return (
            f"{self._sanitize(self.plugin_name)}"
            + f">{self._sanitize(self.node_type)}"
            + f">{self._sanitize(self.node_name)}"
            + f">{self._sanitize(self.instance_name)}"
        )


@dataclass
class NodeManifest:
    """A dataclass that holds all the relevant data that a node can give
    before its instantiation."""

    name: str
    default_config: dict[str, Any] = field(default_factory=lambda: {})


class Node(ABC):
    """Abstract class that holds the implementation schema that all nodes should
    inherit from."""

    def __init__(
        self, config: dict[str, Any], node_instance_path: NodeInstancePath
    ) -> None:
        """The node constructor method.

        Args:
            config: A dictionary that holds all the config of the instance.
            node_instance_path: The unique path of the node instance.
        """

        self.config = config
        self.node_instance_path = node_instance_path
        self._logger = getLogger(str(self.node_instance_path))

    @staticmethod
    @abstractmethod
    def get_node_manifest() -> NodeManifest:
        """A function that returns the node manifest of the node.

        Returns:
            The NodeManifest of the node.
        """

        ...

    @staticmethod
    def extra_node_default_configs() -> dict[str, Any]:
        """An overrideable function that returns extra parameters to be added
        to the default config that it defined by the type of node.

        Returns:
            Extra config to be added to the default config of the node.
        """

        return {}

    def raise_failure_node_exception(
        self, message: str, exception: type[NodeFailureException] = NodeFailureException
    ) -> None:
        """Wrapper to raise a node failure and notify it in the log.

        Args:
            message: The message to be attach to the exception.
            exception: The exception child of the generic
                `NodeFailureException` exception.

        Raises:
            exception: Raises the given exception.
        """

        self._logger.error(
            f'Node "{self.node_instance_path}" has raised a'
            + f' "{exception.__name__}" exception with '
            + f"the message: {message}"
        )
        raise exception()


NODE_SUBCLASS = TypeVar("NODE_SUBCLASS", bound=Node)
