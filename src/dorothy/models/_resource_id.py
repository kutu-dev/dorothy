from dataclasses import dataclass
from abc import ABC, abstractmethod
from ._node import NodeInstancePath


@dataclass
class ResourceId(ABC):
    """Dummy base class for all the resource id classes."""

    node_instance_path: NodeInstancePath
    unique_id: str

    @staticmethod
    def _sanitize(string: str) -> str:
        """Escapes any conflict character from the given string.

        Args:
            string: The string to sanitize.

        Returns:
            The sanitized string.
        """

        return string.replace("&", "&&").replace("@", "&@")

    @abstractmethod
    def resource_name(self) -> str:
        """Function that returns the string representation of the resource type."""

        ...

    def __str__(self) -> str:
        """Generates a string representation of the resource id.

        Returns:
            The string representation of the resource id.
        """

        return (
            f"{self._sanitize(self.resource_name())}"
            + f"@{self._sanitize(str(self.node_instance_path))}"
            + f"@{self._sanitize(self.unique_id)}"
        )
