import datetime
from dataclasses import dataclass

from typhon import js_ast
from typhon.js_node_serializer import serialize_js_node, JSNodeDeserializer
from typhon.object_info_serializer import serialize_object_info, deserialize_object_info


@dataclass
class ModuleInfo:
    updated: datetime.datetime = None
    objects: dict = None
    js_tree: js_ast.JSNode = None


def serialize_module_info(module_info: ModuleInfo) -> dict:
    objects = []
    nodes = {}
    if module_info.objects:
        for name, object_info in module_info.objects.items():
            objects.append(serialize_object_info(object_info))
    if module_info.js_tree:
        nodes = serialize_js_node(module_info.js_tree)

    return {
        'updated': datetime.datetime.now().isoformat(),
        'objects': objects,
        'nodes': nodes,
    }


def deserialize_module_info(data: dict) -> ModuleInfo:
    objects_data = data.get('objects')
    nodes_info = data.get('nodes', {})
    node_deserializer = JSNodeDeserializer(nodes_info)
    js_tree = node_deserializer.deserialize()

    objects = {}
    for object_data in objects_data:
        object_info = deserialize_object_info(object_data, node_deserializer.nodes_by_ids)
        objects[object_info.name] = object_info

    return ModuleInfo(objects=objects, js_tree=js_tree)
