from typhon import js_ast
from typhon.js_node_serializer import serialize_js_node, JSNodeDeserializer


class TestSerializeJSNode:
    def test_node(self):
        node = js_ast.JSNode()
        result = serialize_js_node(node)
        assert result == {'class': 'JSNode', 'id': id(node)}

    def test_name(self):
        node = js_ast.JSName(id='var_a')
        result = serialize_js_node(node)
        assert result == {'id': id(node), 'class': 'JSName', 'fields': {'id': 'var_a'}}

    def test_list(self):
        node = js_ast.JSList(
            elts=[
                js_ast.JSName(id='a'),
                js_ast.JSName(id='b'),
            ],
        )

        result = serialize_js_node(node)

        expected = {
            'id': id(node),
            'class': 'JSList',
            'fields': {
                'elts': [
                    {'id': id(node.elts[0]), 'class': 'JSName', 'fields': {'id': 'a'}},
                    {'id': id(node.elts[1]), 'class': 'JSName', 'fields': {'id': 'b'}},
                ]
            },
        }
        assert result == expected

    def test_assign(self):
        node = js_ast.JSAssign(target=js_ast.JSName('test'), value=js_ast.JSConstant(123))

        result = serialize_js_node(node)

        expected = {
            'id': id(node),
            'class': 'JSAssign',
            'fields': {
                'target': {'id': id(node.target), 'class': 'JSName', 'fields': {'id': 'test'}},
                'value': {'id': id(node.value), 'class': 'JSConstant', 'fields': {'value': 123}},
            },
        }
        assert result == expected


class TestDeserializeJSNode:
    def test_node(self):
        node = js_ast.JSNode()
        data = serialize_js_node(node)

        deserializer = JSNodeDeserializer(data)
        result = deserializer.deserialize()

        assert result == node
        assert deserializer.nodes_by_id == {id(node): node}

    def test_name(self):
        node = js_ast.JSName(id='var_a')
        data = serialize_js_node(node)

        deserializer = JSNodeDeserializer(data)
        result = deserializer.deserialize()

        assert result == node
        assert deserializer.nodes_by_id == {id(node): node}

    def test_list(self):
        node = js_ast.JSList(
            elts=[
                js_ast.JSName(id='a'),
                js_ast.JSName(id='b'),
            ],
        )
        data = serialize_js_node(node)

        deserializer = JSNodeDeserializer(data)
        result = deserializer.deserialize()

        assert result == node
        nodes_by_id = {id(node): node, id(node.elts[0]): node.elts[0], id(node.elts[1]): node.elts[1]}
        assert deserializer.nodes_by_id == nodes_by_id

    def test_assign(self):
        node = js_ast.JSAssign(target=js_ast.JSName('test'), value=js_ast.JSConstant(123))
        data = serialize_js_node(node)

        deserializer = JSNodeDeserializer(data)
        result = deserializer.deserialize()

        assert result == node
        nodes_by_id = {id(node): node, id(node.target): node.target, id(node.value): node.value}
        assert deserializer.nodes_by_id == nodes_by_id
