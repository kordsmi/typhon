import datetime
from dataclasses import dataclass

from typhon import js_ast
from typhon.js_node_serializer import serialize_js_node, JSNodeDeserializer
from typhon.object_info import ObjectInfo
from typhon.object_info_serializer import serialize_object_info, deserialize_object_info


@dataclass
class ModuleInfo:
    updated: datetime.datetime = None
    objects: ObjectInfo = None
    js_tree: js_ast.JSNode = None


def serialize_module_info(module_info: ModuleInfo) -> dict:
    module_object = module_info.objects or ObjectInfo([])
    nodes = {}
    if module_info.js_tree:
        nodes = serialize_js_node(module_info.js_tree)

    return {
        'updated': datetime.datetime.now().isoformat(),
        'objects': serialize_object_info(module_object),
        'nodes': nodes,
    }


def deserialize_module_info(data: dict, root_object: ObjectInfo) -> ModuleInfo:
    objects_data = data.get('objects')
    nodes_info = data.get('nodes', {})
    node_deserializer = JSNodeDeserializer(nodes_info)
    js_tree = node_deserializer.deserialize()
    objects = deserialize_object_info(objects_data, root_object)
    return ModuleInfo(objects=objects, js_tree=js_tree)
