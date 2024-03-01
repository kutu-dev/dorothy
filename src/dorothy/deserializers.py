from typing import Type

from dorothy.models import Resource, ResourceId, Song, Album, NodeInstancePath


def deserialize_node_instance_path(
    serialized_node_instance_path: str,
) -> NodeInstancePath:
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


def deserialize_resource_id(serialized_resource: str) -> ResourceId:
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

    resource_type: Type[Resource]
    match deserialized_data[0]:
        case "song":
            resource_type = Song
        case "album":
            resource_type = Album
        case _:
            raise ValueError(f"Unknown resource type: {deserialized_data[0]}")

    return ResourceId(
        resource_type,
        deserialize_node_instance_path(deserialized_data[1]),
        deserialized_data[2],
    )
