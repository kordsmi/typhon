from typhon import js_ast
from typhon.js_node_serializer import serialize_js_node, deserialize_js_node


class TestSerializeJSNode:
    def test_node(self):
        a = js_ast.JSNode()
        result = serialize_js_node(a)
        assert result == {'class': 'JSNode'}

    def test_name(self):
        node = js_ast.JSName(id='var_a')
        result = serialize_js_node(node)
        assert result == {'class': 'JSName', 'fields': {'id': 'var_a'}}

    def test_list(self):
        node = js_ast.JSList(
            elts=[
                js_ast.JSName(id='a'),
                js_ast.JSName(id='b'),
            ],
        )

        result = serialize_js_node(node)

        expected = {
            'class': 'JSList',
            'fields': {
                'elts': [
                    {'class': 'JSName', 'fields': {'id': 'a'}},
                    {'class': 'JSName', 'fields': {'id': 'b'}},
                ]
            },
        }
        assert result == expected

    def test_assign(self):
        node = js_ast.JSAssign(target=js_ast.JSName('test'), value=js_ast.JSConstant(123))

        result = serialize_js_node(node)

        expected = {
            'class': 'JSAssign',
            'fields': {
                'target': {'class': 'JSName', 'fields': {'id': 'test'}},
                'value': {'class': 'JSConstant', 'fields': {'value': 123}},
            },
        }
        assert result == expected


class TestDeserializeJSNode:
    def test_node(self):
        a = js_ast.JSNode()
        data = serialize_js_node(a)

        result = deserialize_js_node(data)

        assert result == a

    def test_name(self):
        node = js_ast.JSName(id='var_a')
        data = serialize_js_node(node)

        result = deserialize_js_node(data)

        assert result == node

    def test_list(self):
        node = js_ast.JSList(
            elts=[
                js_ast.JSName(id='a'),
                js_ast.JSName(id='b'),
            ],
        )
        data = serialize_js_node(node)

        result = deserialize_js_node(data)

        assert result == node

    def test_assign(self):
        node = js_ast.JSAssign(target=js_ast.JSName('test'), value=js_ast.JSConstant(123))
        data = serialize_js_node(node)

        result = deserialize_js_node(data)

        assert result == node
