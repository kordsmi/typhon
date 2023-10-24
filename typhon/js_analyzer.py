from collections import defaultdict
from dataclasses import dataclass

from typhon import js_ast


def transform_module(js_module: js_ast.JSModule):
    body_transformer = BodyTransformer(js_module.body)
    body_transformer.transform()
    info = body_transformer.get_identifies()
    js_module.export = js_ast.JSExport(info)


@dataclass
class NodeInfo:
    node: js_ast.JSNode
    index: int


class BodyTransformer:
    def __init__(self, body: [js_ast.JSStatement]):
        self.body = body
        self.var_list = defaultdict(list)
        self.class_def_list = defaultdict(list)
        self.func_def_list = defaultdict(list)
        self.import_list = defaultdict(list)
        self.call_list = defaultdict(list)
        self.alias_list = defaultdict(list)

    def collect_objects_info(self):
        for i in range(len(self.body)):
            node = self.body[i]
            if isinstance(node, js_ast.JSAssign):
                self.collect_assign_info(node, i)
            elif isinstance(node, js_ast.JSFunctionDef):
                self.func_def_list[node.name].append(NodeInfo(node, i))
            elif isinstance(node, js_ast.JSImport):
                if node.names:
                    for alias in node.names:
                        object_name = alias.asname or alias.name
                        self.import_list[object_name].append(NodeInfo(node, i))
                else:
                    object_name = node.alias or node.module
                    self.import_list[object_name].append(NodeInfo(node, i))
            elif isinstance(node, js_ast.JSClassDef):
                self.class_def_list[node.name].append(NodeInfo(node, i))
            elif isinstance(node, js_ast.JSCall):
                self.call_list[node.func].append(NodeInfo(node, i))

    def collect_assign_info(self, node: js_ast.JSAssign, index: int):
        target: js_ast.JSExpression = node.target
        if isinstance(target, js_ast.JSName):
            self.var_list[target.id].append(NodeInfo(node, index))
        elif isinstance(target, js_ast.JSAttribute):
            if not isinstance(target.value, js_ast.JSName):
                return
            value_name = target.value.id
            if target.attr == '__ty_alias__':
                self.alias_list[value_name].append(NodeInfo(node, index))
                self.body[index] = js_ast.JSNop()

    def get_identifies(self):
        info = []

        def add_name(name: str):
            if name not in info:
                info.append(name)

        def add_names(info_dict: {}):
            for item in info_dict.keys():
                add_name(item)

        add_names(self.var_list)
        add_names(self.func_def_list)
        add_names(self.class_def_list)
        add_names(self.import_list)

        return info

    def transform(self):
        self.collect_objects_info()
        self.replace_variables_to_aliases()
        self.insert_let()
        self.transform_classes()
        self.transform_calls_to_new()

    def insert_let(self):
        for var_name, info_list in self.var_list.items():
            info: NodeInfo = info_list[0]
            info.node = js_ast.JSLet(info.node)
            self.body[info.index] = info.node

    def transform_classes(self):
        for class_name, info_list in self.class_def_list.items():
            info: NodeInfo = info_list[0]
            transform_class(info.node)

    def transform_calls_to_new(self):
        for name, info_list in self.call_list.items():
            if name in self.class_def_list:
                for info in info_list:
                    self.body[info.index] = transform_call_to_new(info.node)

    def replace_variables_to_aliases(self):
        for var_name, node_info_list in self.alias_list.items():
            find = js_ast.JSName(id=var_name)
            assign_node: js_ast.JSAssign = node_info_list[0].node
            value: js_ast.JSConstant = assign_node.value
            replace = js_ast.JSName(id=value.value)
            self.body = replace_in_body(self.body, find, replace)


def transform_class(class_def: js_ast.JSClassDef):
    class_body = class_def.body
    for i in range(len(class_body)):
        node = class_body[i]

        if isinstance(node, js_ast.JSFunctionDef):
            class_body[i] = transform_function_to_method(node)


def transform_function_to_method(func_def: js_ast.JSFunctionDef) -> js_ast.JSMethodDef:
    method_def = js_ast.JSMethodDef(name=func_def.name, args=func_def.args, body=func_def.body)
    transform_method_args(method_def)
    replace_in_body(method_def.body, js_ast.JSName('self'), js_ast.JSName('this'))
    if method_def.name == '__init__':
        method_def.name = 'constructor'
    return method_def


def transform_method_args(method_def: js_ast.JSMethodDef):
    if not method_def.args.args:
        return

    for arg in method_def.args.args:
        if arg.arg == 'self':
            method_def.args.args.remove(arg)
            break


def transform_call_to_new(node: js_ast.JSCall) -> js_ast.JSNew:
    return js_ast.JSNew(class_=js_ast.JSName(node.func), args=node.args, keywords=node.keywords)


def replace_in_body(body: [js_ast.JSStatement], find: js_ast.JSNode, replace: js_ast.JSNode) -> [js_ast.JSStatement]:
    for statement in body:
        if isinstance(statement, js_ast.JSAssign):
            replace_in_assign(statement, find, replace)
        elif isinstance(statement, js_ast.JSCodeExpression):
            replace_in_code_expression(statement, find, replace)
    return body


def replace_in_assign(node: js_ast.JSAssign, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSAssign:
    node.target = replace_in_expression(node.target, find, replace)
    node.value = replace_in_expression(node.value, find, replace)
    return node


def replace_in_code_expression(
        node: js_ast.JSCodeExpression, find: js_ast.JSNode, replace: js_ast.JSNode
) -> js_ast.JSCodeExpression:
    new_value = replace_in_expression(node.value, find, replace)
    if new_value != node.value:
        node.value = new_value
    return node


def replace_in_expression(
        expr: js_ast.JSExpression, find: js_ast.JSNode, replace: js_ast.JSNode
) -> js_ast.JSExpression:
    if expr == find:
        return replace

    if isinstance(expr, js_ast.JSAttribute):
        return replace_in_attribute(expr, find, replace)
    elif isinstance(expr, js_ast.JSCall):
        return replace_in_call(expr, find, replace)

    return expr


def replace_in_attribute(attr: js_ast.JSAttribute, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSAttribute:
    attr.value = replace_in_expression(attr.value, find, replace)
    return attr


def replace_in_call(node: js_ast.JSCall, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSCall:
    node.func = replace_in_expression(node.func, find, replace)

    if node.args:
        for i in range(len(node.args)):
            arg = node.args[i]
            new_arg = replace_in_expression(arg, find, replace)
            if new_arg != arg:
                node.args[i] = new_arg

    if node.keywords:
        for keyword in node.keywords:
            new_value = replace_in_expression(keyword.value, find, replace)
            if new_value != keyword.value:
                keyword.value = new_value

    return node
