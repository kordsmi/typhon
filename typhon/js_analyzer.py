from itertools import chain
from typing import Optional, List

from typhon import js_ast
from typhon.context import get_context_object, get_object
from typhon.object_info import ObjectInfo, TypeObjectInfo, FunctionObjectInfo, ConstantObjectInfo, ReferenceObjectInfo
from typhon.js_visitor import JSNodeVisitor


def get_attribute_target(from_object: ObjectInfo, node: js_ast.JSAttribute) -> ObjectInfo:
    if isinstance(node.value, js_ast.JSName):
        return from_object.object_dict[node.value.id]
    elif isinstance(node.value, js_ast.JSAttribute):
        return get_attribute_target(from_object, node.value)

    raise Exception(f'Unsupported node type {type(node)}')


def get_object_from_expression(
        from_object: ObjectInfo,
        context_path: List[str],
        node: js_ast.JSExpression,
) -> ObjectInfo:
    if isinstance(node, js_ast.JSName):
        source_object = get_object(from_object, context_path, node.id)
        return source_object
    if isinstance(node, js_ast.JSNew):
        class_ = get_object_from_expression(from_object, context_path, node.class_)
        object_info = ObjectInfo(None)
        object_info.object_class = class_
        return object_info
    if isinstance(node, js_ast.JSConstant):
        return ConstantObjectInfo(None, node.value)
    if isinstance(node, js_ast.JSAttribute):
        object_info = get_object_from_expression(from_object, context_path, node.value)
        return get_object(from_object, object_info.context_path, node.attr)
    if isinstance(node, js_ast.JSArg):
        return ObjectInfo(None)

    return ObjectInfo(None)


class Tranformer(JSNodeVisitor):
    def __init__(self, context_path: List[str], root_object: ObjectInfo):
        self.context_path = context_path
        self.root_object = root_object
        self.context_vars: ObjectInfo = get_context_object(root_object, context_path)

    def visit_JSAssign(self, node: js_ast.JSAssign) -> Optional[js_ast.JSAssign]:
        visited_node = super().visit_JSAssign(node)
        node = visited_node or node
        new_node = None
        if isinstance(node.target, js_ast.JSName):
            new_node = self._visit_js_assign_to_name(node)
        elif isinstance(node.target, js_ast.JSAttribute):
            new_node = self._visit_js_assign_to_attribute(node)
        return new_node or visited_node

    def _set_context_variable(
            self,
            target_context: ObjectInfo,
            target_name: str,
            node: js_ast.JSExpression,
    ) -> Optional[ObjectInfo]:
        if target_context:
            value_context = get_object_from_expression(self.root_object, target_context.context_path, node)
            if value_context.context_path:
                value_context = ReferenceObjectInfo(None, value_context.context_path)
            value_context.context_path = target_context.context_path + [target_name]
            target_context.object_dict[target_name] = value_context
            return value_context

    def _visit_js_assign_to_name(self, node: js_ast.JSAssign) -> Optional[js_ast.JSLet]:
        self._set_context_variable(self.context_vars, node.target.id, node.value)

    def _visit_js_assign_to_attribute(self, node: js_ast.JSAssign) -> Optional[js_ast.JSNop]:
        result = None
        target_name = node.target.attr

        if target_name == '__ty_alias__':
            result = js_ast.JSNop()
            target_context = self._set_context_variable(self.root_object, node.target.value.id, node)
            self._set_context_variable(target_context, target_name, node)
        else:
            target_context = get_attribute_target(self.context_vars, node.target)
        self._set_context_variable(target_context, target_name, node.value)

        return result

    def visit_JSName(self, node: js_ast.JSName) -> Optional[js_ast.JSName]:
        var_name = node.id
        object_info = get_object(self.root_object, self.context_path, var_name)
        if object_info and '__ty_alias__' in object_info.object_dict:
            return js_ast.JSName(object_info.object_dict['__ty_alias__'].value)

    def visit_JSCall(self, node: js_ast.JSCall) -> Optional[js_ast.JSCall or js_ast.JSNew]:
        visited_node = super().visit_JSCall(node)
        node = visited_node or node

        new_node = self._check_and_transform_call_to_new(node)
        if new_node:
            return new_node

        return visited_node

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        func_name = node.name

        function_context = self.context_path + [func_name]
        function_info = FunctionObjectInfo(function_context)
        self.context_vars.object_dict[func_name] = function_info

        new_args = self.visit(node.args) or node.args
        original_context_path = self.context_path
        self.context_path = function_context
        try:
            for arg in chain(new_args.args or [], new_args.kwonlyargs or []):
                arg_name = arg.arg
                self._set_context_variable(function_info, arg_name, arg)
        finally:
            self.context_path = original_context_path

        body_transformer = BodyTransformer(node.body, function_context, self.root_object)
        new_body = body_transformer.transform()
        if new_args or new_body:
            return js_ast.JSFunctionDef(node.name, new_args or node.args, new_body or node.body)

    def _check_and_transform_call_to_new(self, node: js_ast.JSCall) -> Optional[js_ast.JSNew]:
        id_info = self._get_node_info(node.func)
        if isinstance(id_info, TypeObjectInfo):
            return js_ast.JSNew(class_=node.func, args=node.args, keywords=node.keywords)

    def _get_node_info(self, node: js_ast.JSNode) -> Optional[ObjectInfo]:
        if isinstance(node, js_ast.JSName):
            return get_object_from_expression(self.root_object, self.context_path, node)
        if isinstance(node, js_ast.JSAttribute):
            return self._get_attribute_info(node)

    def _get_attribute_info(self, node: js_ast.JSAttribute) -> Optional[ObjectInfo]:
        if not isinstance(node.value, js_ast.JSName):
            return

        return get_object_from_expression(self.root_object, self.context_path, node)


class BodyTransformer(Tranformer):
    def __init__(
            self,
            body: [js_ast.JSStatement],
            context_path: [str],
            root_object: ObjectInfo,
    ):
        super().__init__(context_path, root_object)
        self.body = body

    def transform(self):
        new_body = self.visit(self.body)
        if new_body:
            self.body = new_body
            return new_body

    def _visit_js_assign_to_name(self, node: js_ast.JSAssign) -> Optional[js_ast.JSLet]:
        name = node.target.id
        new_node = None
        if not name in self.context_vars.object_dict:
            new_node = js_ast.JSLet(node)

        self._set_context_variable(self.context_vars, node.target.id, node.value)
        return new_node

    def visit_JSClassDef(self, node: js_ast.JSClassDef) -> Optional['js_ast.JSClassDef']:
        class_context = self.context_path + [node.name]
        class_object = TypeObjectInfo(class_context)
        self.context_vars.object_dict[node.name] = class_object
        class_transformer = ClassTransformer(node, class_context, self.root_object)
        new_class_def = class_transformer.transform()
        class_object.node = new_class_def
        return new_class_def

    def visit_JSImport(self, node: js_ast.JSImport) -> Optional[js_ast.JSImport]:
        visited_node = super().visit_JSImport(node)
        self._add_import_info(visited_node or node)
        return visited_node

    def _add_import_info(self, node: js_ast.JSImport):
        module_name = node.alias or node.module
        module_info = self.root_object.object_dict[module_name]

        if node.names:
            # Добавление импортируемых объектов
            for alias in node.names:
                object_name = alias.asname or alias.name
                self.context_vars.object_dict[object_name] = module_info.object_dict[alias.name]
        else:
            # Добавление модуля как объекта
            self.context_vars.object_dict[module_name] = module_info


class ClassTransformer(Tranformer):
    def __init__(self, class_def: js_ast.JSClassDef, context_path: List[str], root_object: ObjectInfo):
        super().__init__(context_path, root_object)
        self.class_def = class_def

    def transform(self) -> Optional[js_ast.JSClassDef]:
        new_body = self.visit(self.class_def.body)
        if new_body:
            return js_ast.JSClassDef(self.class_def.name, new_body)

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        method_name = node.name
        if method_name == '__init__':
            method_name = 'constructor'

        new_args = self.visit(node.args) or node.args
        method_context = self.context_path + [method_name]
        function_info = FunctionObjectInfo(method_context)
        self.context_vars.object_dict[method_name] = function_info

        original_context_path = self.context_path
        self.context_path = method_context
        try:
            for arg in chain(new_args.args or [], new_args.kwonlyargs or []):
                arg_name = arg.arg
                self._set_context_variable(function_info, arg_name, arg)

            if new_args.args:
                instance_arg = new_args.args[0]
                new_args = js_ast.JSArguments(new_args.args[1:], new_args.defaults, new_args.vararg, new_args.kwonlyargs,
                                              new_args.kw_defaults, new_args.kwarg)
                self._set_context_variable(function_info.object_dict[instance_arg.arg], '__ty_alias__',
                                           js_ast.JSConstant('this'))
                self._set_context_variable(function_info, 'this', instance_arg)
        finally:
            self.context_path = original_context_path

        body_transformer = BodyTransformer(node.body, method_context, self.root_object)
        new_body = body_transformer.transform()
        return js_ast.JSMethodDef(name=method_name, args=new_args, body=new_body or node.body)
