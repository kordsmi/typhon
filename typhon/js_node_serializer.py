from typing import Union

from typhon import js_ast


def serialize_js_node(node: js_ast.JSNode) -> dict:
    fields = {name: serialize_field(getattr(node, name)) for name in node._fields}

    result = {
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


def deserialize_js_node(data: dict) -> js_ast.JSNode:
    class_name = data.get('class')
    fields_data = data.get('fields', {})
    fields = {name: deserialize_field(value) for name, value in fields_data.items()}
    return js_ast.node_factory(class_name, fields)


def deserialize_field(value_data: Union[str, int, list, dict]) -> Union[str, int, list, js_ast.JSNode]:
    if isinstance(value_data, dict):
        return deserialize_js_node(value_data)
    elif isinstance(value_data, list):
        return [deserialize_field(item) for item in value_data]
    return value_data
