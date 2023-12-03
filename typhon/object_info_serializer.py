from typing import Dict

from typhon import js_ast
from typhon.identifires import ObjectInfo, get_object_info


def serialize_object_info(object_info: ObjectInfo) -> dict:
    return {
        'name': object_info.name,
        'node': id(object_info.node),
    }


def deserialize_object_info(data: dict, nodes_by_ids: Dict[str, js_ast.JSNode]) -> ObjectInfo:
    object_id = data.get('node')
    name = data.get('name')
    node = nodes_by_ids.get(object_id)
    if node:
        return get_object_info(node, name)
