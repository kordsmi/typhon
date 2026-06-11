import datetime

from typhon import js_ast
from typhon.module_info import ModuleInfo, serialize_module_info
from typhon.object_collector import ObjectInfo


def test_serialize_module_info():
    node = js_ast.JSName('a')
    objects = ObjectInfo(object_value='a')
    module_info = ModuleInfo(objects=objects, js_tree=node)

    result = serialize_module_info(module_info)

    expected = {
        'updated': datetime.datetime.fromisoformat(result['updated']).isoformat(),
        'nodes': {'id': id(node), 'class': 'JSName', 'fields': {'id': 'a'}},
    }
    assert result == expected
