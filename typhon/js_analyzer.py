from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from typhon import js_ast
from typhon.js_visitor import JSNodeVisitor


def transform_module(js_module: js_ast.JSModule):
    body_transformer = BodyTransformer(js_module.body)
    new_body = body_transformer.transform()
    info = body_transformer.get_identifies()
    export = js_ast.JSExport(info)

    return js_ast.JSModule(body=new_body or js_module.body, export=export)


@dataclass
class NodeInfo:
    node: js_ast.JSNode
    index: int


class BodyTransformer(JSNodeVisitor):
    def __init__(self, body: [js_ast.JSStatement]):
        self.body = body
        self.var_list = defaultdict(list)
        self.class_def_list = defaultdict(list)
        self.func_def_list = defaultdict(list)
        self.import_list = defaultdict(list)
        self.call_list = defaultdict(list)
        self.alias_list = defaultdict(list)

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
        new_body = self.visit(self.body)
        if new_body:
            self.body = new_body
        self.transform_classes()
        self.transform_calls_to_new()

        if new_body:
            return new_body

    def transform_classes(self):
        for class_name, info_list in self.class_def_list.items():
            info: NodeInfo = info_list[0]
            transform_class(info.node)

    def transform_calls_to_new(self):
        for name, info_list in self.call_list.items():
            if name in self.class_def_list:
                for info in info_list:
                    self.body[info.index] = transform_call_to_new(info.node)

    def visit_JSAssign(self, node: js_ast.JSAssign) -> Optional[js_ast.JSAssign]:
        visited_node = super().visit_JSAssign(node)
        node = visited_node or node
        target = node.target
        if isinstance(target, js_ast.JSName):
            name = target.id
            if not self.var_list[name]:
                visited_node = js_ast.JSLet(node)
            self.var_list[name].append(visited_node)
        elif isinstance(target, js_ast.JSAttribute):
            if isinstance(target.value, js_ast.JSName):
                value_name = target.value.id
                if target.attr == '__ty_alias__':
                    self.alias_list[value_name].append(NodeInfo(node, -1))
                    visited_node = js_ast.JSNop()
        return visited_node

    def visit_JSName(self, node: js_ast.JSName) -> Optional[js_ast.JSName]:
        var_name = node.id
        if self.alias_list[var_name]:
            alias_info = self.alias_list[var_name][0]
            assign_node: js_ast.JSAssign = alias_info.node
            value: js_ast.JSConstant = assign_node.value
            return js_ast.JSName(id=value.value)

    def visit_JSCall(self, node: js_ast.JSCall) -> Optional[js_ast.JSCall]:
        visited_node = super().visit_JSCall(node)
        self._add_call_info(visited_node or node)
        return visited_node

    def visit_JSClassDef(self, node: js_ast.JSClassDef) -> Optional['js_ast.JSClassDef']:
        visited_node = super().visit_JSClassDef(node)
        self._add_class_def_info(visited_node or node)
        return visited_node

    def visit_JSImport(self, node: js_ast.JSImport) -> Optional[js_ast.JSImport]:
        visited_node = super().visit_JSImport(node)
        self._add_import_info(visited_node or node)
        return visited_node

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        visited_node = super().visit_JSFunctionDef(node)
        self._add_func_def_info(visited_node or node)
        return visited_node

    def _add_call_info(self, node: js_ast.JSCall):
        func: js_ast.JSExpression = node.func
        if isinstance(func, js_ast.JSName):
            self.call_list[func.id].append(NodeInfo(node, -1))

    def _add_class_def_info(self, node: js_ast.JSClassDef):
        self.class_def_list[node.name].append(NodeInfo(node, -1))

    def _add_import_info(self, node: js_ast.JSImport):
        if node.names:
            for alias in node.names:
                object_name = alias.asname or alias.name
                self.import_list[object_name].append(NodeInfo(node, -1))
        else:
            object_name = node.alias or node.module
            self.import_list[object_name].append(NodeInfo(node, -1))

    def _add_func_def_info(self, node: js_ast.JSFunctionDef):
        self.func_def_list[node.name].append(NodeInfo(node, -1))


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
    return js_ast.JSNew(class_=node.func, args=node.args, keywords=node.keywords)


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
