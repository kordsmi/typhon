import datetime

from typhon import js_ast
from typhon.identifires import ObjectInfo, ID_VAR
from typhon.module_info import ModuleInfo, serialize_module_info


def test_serialize_module_info():
    node = js_ast.JSName('a')
    objects = {
        'a': ObjectInfo('a', node, ID_VAR),
    }
    module_info = ModuleInfo(objects=objects, js_tree=node)

    result = serialize_module_info(module_info)

    expected = {
        'updated': datetime.datetime.fromisoformat(result['updated']).isoformat(),
        'objects': [{'name': 'a', 'node': id(node)}],
        'nodes': {'id': id(node), 'class': 'JSName', 'fields': {'id': 'a'}},
    }
    assert result == expected
