from typing import Union

from typhon import js_ast


def serialize_js_node(node: js_ast.JSNode) -> dict:
    fields = {name: serialize_field(getattr(node, name)) for name in node._fields}

    result = {
        'id': id(node),
        'class': node.__class__.__name__,
    }
    if fields:
        result['fields'] = fields

    return result


def serialize_field(field_value: Union[str, int, list, js_ast.JSNode]) -> Union[str, int, list, dict]:
    if isinstance(field_value, list):
        return [serialize_field(item) for item in field_value]
    elif isinstance(field_value, js_ast.JSNode):
        return serialize_js_node(field_value)
    return field_value


class JSNodeDeserializer:
    def __init__(self, data: dict):
        self.data = data
        self.nodes_by_ids = {}

    def deserialize(self):
        self.nodes_by_ids = {}
        class_name = self.data.get('class')
        node_id = self.data.get('id')
        fields_data = self.data.get('fields', {})
        fields = {name: self.deserialize_field(value) for name, value in fields_data.items()}
        node = js_ast.node_factory(class_name, fields)
        self.nodes_by_ids[node_id] = node
        return node

    def deserialize_field(self, value_data: Union[str, int, list, dict]) -> Union[str, int, list, js_ast.JSNode]:
        if isinstance(value_data, dict):
            deserializer = JSNodeDeserializer(value_data)
            node = deserializer.deserialize()
            self.nodes_by_ids.update(deserializer.nodes_by_ids)
            return node
        elif isinstance(value_data, list):
            return [self.deserialize_field(item) for item in value_data]
        return value_data
