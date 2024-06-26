from typing import Type

from .models._song import SongResourceId, Song
from .models._album import AlbumResourceId, Album
from .models._artist import ArtistResourceId, Artist
from .models._resource_id import ResourceId
from .models._node import NodeInstancePath


def deserialize_node_instance_path(
    serialized_node_instance_path: str,
) -> NodeInstancePath:
    """Deserialize a serialized node instance path.

    Args:
        serialized_node_instance_path: The serialized node instance path.

    Returns:
        The deserialized node instance path.
    """

    deserialized_data = ["", "", "", ""]
    deserialized_index = 0

    escape_next = False
    for character in serialized_node_instance_path:
        if character == "&" and not escape_next:
            escape_next = True
            continue

        if character == ">" and not escape_next:
            deserialized_index += 1
            continue

        deserialized_data[deserialized_index] += character

    return NodeInstancePath(
        plugin_name=deserialized_data[0],
        node_type=deserialized_data[1],
        node_name=deserialized_data[2],
        instance_name=deserialized_data[3],
    )


def deserialize_resource_id(
    serialized_resource: str,
) -> SongResourceId | AlbumResourceId | ArtistResourceId:
    """Deserialize a serialized resource id.

    Args:
        serialized_resource: The serialized resource id.

    Returns:
        A deserialized resource id that matches the serialized id type.
    """

    deserialized_data = ["", "", ""]
    deserialized_index = 0

    escape_next = False
    for character in serialized_resource:
        if character == "&" and not escape_next:
            escape_next = True
            continue

        if character == "@" and not escape_next:
            if deserialized_index < 2:
                deserialized_index += 1
            continue

        deserialized_data[deserialized_index] += character

    resource_id_data = (
        deserialize_node_instance_path(deserialized_data[1]),
        deserialized_data[2],
    )

    match deserialized_data[0]:
        case "song":
            return SongResourceId(*resource_id_data)
        case "album":
            return AlbumResourceId(*resource_id_data)
        case "artist":
            return ArtistResourceId(*resource_id_data)
        case _:
            raise ValueError(f"Unknown resource type: {deserialized_data[0]}")
