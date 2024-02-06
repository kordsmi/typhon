import datetime

from typhon import js_ast
from typhon.object_info import ObjectInfo
from typhon.module_info import ModuleInfo, serialize_module_info


def test_serialize_module_info():
    node = js_ast.JSName('a')
    objects = ObjectInfo(['a'])
    module_info = ModuleInfo(objects=objects, js_tree=node)

    result = serialize_module_info(module_info)

    expected = {
        'updated': datetime.datetime.fromisoformat(result['updated']).isoformat(),
        'objects': {
            'class': 'ObjectInfo',
            'context_path': ['a'],
            'object_class': None,
            'object_dict': {},
        },
        'nodes': {'id': id(node), 'class': 'JSName', 'fields': {'id': 'a'}},
    }
    assert result == expected
