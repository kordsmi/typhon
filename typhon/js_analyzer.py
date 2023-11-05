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
            return new_body

    def visit_JSAssign(self, node: js_ast.JSAssign) -> Optional[js_ast.JSAssign]:
        visited_node = super().visit_JSAssign(node)
        node = visited_node or node
        new_node = None
        if isinstance(node.target, js_ast.JSName):
            new_node = self._visit_js_assign_to_name(node)
        elif isinstance(node.target, js_ast.JSAttribute):
            new_node = self._visit_js_assign_to_attribute(node)
        return new_node or visited_node

    def _visit_js_assign_to_name(self, node: js_ast.JSAssign) -> Optional[js_ast.JSLet]:
        name = node.target.id
        new_node = None
        if name not in self.var_list:
            new_node = js_ast.JSLet(node)
        self.var_list[name].append(new_node or node)
        return new_node

    def _visit_js_assign_to_attribute(self, node: js_ast.JSAssign) -> Optional[js_ast.JSNop]:
        target = node.target
        if not isinstance(target.value, js_ast.JSName):
            return

        if target.attr == '__ty_alias__':
            self.alias_list[target.value.id].append(NodeInfo(node, -1))
            return js_ast.JSNop()

    def visit_JSName(self, node: js_ast.JSName) -> Optional[js_ast.JSName]:
        var_name = node.id
        if var_name in self.alias_list:
            alias_info = self.alias_list[var_name][0]
            assign_node: js_ast.JSAssign = alias_info.node
            value: js_ast.JSConstant = assign_node.value
            return js_ast.JSName(id=value.value)

    def visit_JSCall(self, node: js_ast.JSCall) -> Optional[js_ast.JSCall or js_ast.JSNew]:
        visited_node = super().visit_JSCall(node)
        node = visited_node or node

        new_node = self._check_and_transform_call_to_new(node)
        if new_node:
            return new_node

        self._add_call_info(node)
        return visited_node

    def visit_JSClassDef(self, node: js_ast.JSClassDef) -> Optional['js_ast.JSClassDef']:
        class_transformer = ClassTransformer(node)
        new_class_def = class_transformer.transform()
        self._add_class_def_info(new_class_def or node)
        return new_class_def

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

    def _check_and_transform_call_to_new(self, node: js_ast.JSCall) -> Optional[js_ast.JSNew]:
        func = node.func
        if not isinstance(func, js_ast.JSName):
            return

        func_name = func.id
        if func_name in self.class_def_list:
            return js_ast.JSNew(class_=node.func, args=node.args, keywords=node.keywords)


class ClassTransformer(JSNodeVisitor):
    def __init__(self, class_def: js_ast.JSClassDef):
        self.class_def = class_def

    def transform(self) -> Optional[js_ast.JSClassDef]:
        new_body = self.visit(self.class_def.body)
        if new_body:
            return js_ast.JSClassDef(self.class_def.name, new_body)

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        method_name = node.name
        if method_name == '__init__':
            method_name = 'constructor'

        new_args = self.visit(node.args)
        body_transformer = BodyTransformer(node.body)
        body_transformer.alias_list['self'].append(
            NodeInfo(js_ast.JSAssign(js_ast.JSName('self'), js_ast.JSConstant('this')), -1)
        )
        new_body = body_transformer.transform()
        return js_ast.JSMethodDef(name=method_name, args=new_args or node.args, body=new_body or node.body)

    def visit_JSArg(self, node: js_ast.JSArg) -> Optional[js_ast.JSArg]:
        if node.arg == 'self':
            return js_ast.JSNop()
        return super().visit_JSArg(node)
