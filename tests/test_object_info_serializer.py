from typhon import js_ast
from typhon.identifires import ObjectInfo, ID_VAR, get_object_info
from typhon.object_info_serializer import serialize_object_info, deserialize_object_info


def test_serialize_object_info():
    node = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(123))
    object_info = get_object_info(node, 'a')

    result = serialize_object_info(object_info)

    expected = {
        'name': 'a',
        'node': id(node),
    }

    assert result == expected


def test_deserialize_object_info():
    node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(123))
    node_2 = js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant('test'))
    nodes_by_ids = {
        id(node_1): node_1,
        id(node_2): node_2,
    }

    data = {
        'name': 'a',
        'node': id(node_1),
    }
    result = deserialize_object_info(data, nodes_by_ids)

    expected = ObjectInfo('a', node_1, ID_VAR)
    assert result == expected
