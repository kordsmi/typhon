from typing import Optional, List, Union, Any

from typhon import js_ast
from typhon.object_collector import ObjectInfo, ObjectConstant, get_object_by_path, ObjectClass


def get_attribute_target(from_object: ObjectInfo, node: js_ast.JSAttribute) -> ObjectInfo:
    if isinstance(node.value, js_ast.JSName):
        return from_object.object_dict[node.value.id]
    elif isinstance(node.value, js_ast.JSAttribute):
        return get_attribute_target(from_object, node.value)

    raise Exception(f'Unsupported node type {type(node)}')


def get_object_from_node(
        from_object: ObjectInfo,
        node: js_ast.JSNode,
) -> ObjectInfo:
    if isinstance(node, js_ast.JSName):
        source_object = get_object_by_path(from_object, node.id)
        return source_object
    if isinstance(node, js_ast.JSNew):
        class_ = get_object_from_node(from_object, node.class_)
        object_info = ObjectInfo()
        object_info.object_class = class_
        return object_info
    if isinstance(node, js_ast.JSConstant):
        return ObjectConstant(node.value)
    if isinstance(node, js_ast.JSAttribute):
        object_info = get_object_from_node(from_object, node.value)
        return get_object_by_path(object_info, node.attr)
    if isinstance(node, js_ast.JSArg):
        return ObjectInfo()

    return ObjectInfo()


# def get_object_info_by_node(
#         context_path: List[str],
#         node: js_ast.JSNode,
# ) -> ObjectInfo:
#     if isinstance(node, js_ast.JSName):
#         return NewReferenceObjectInfo(context_path, node.id)
#     if isinstance(node, js_ast.JSNew):
#         class_ = get_object_info_by_node(context_path, node.class_)
#         return ObjectInfo(context_path, object_class=class_)
#     if isinstance(node, js_ast.JSConstant):
#         return ConstantObjectInfo(context_path, node.value)
#     if isinstance(node, js_ast.JSAttribute):
#         return NewReferenceObjectInfo(context_path, node.attr)
#     if isinstance(node, js_ast.JSArg):
#         return NewReferenceObjectInfo(context_path, node.arg)
#
#     return ObjectInfo(context_path)


# class ObjectCollector(JSNodeVisitor):
#     def __init__(self):
#         self.module_info = ObjectInfo([], None)
#
#     # def visit_JSImport(self, node: js_ast.JSImport):
#     #     module_name = node.alias or node.module
#     #     module_path = tuple(module_name.split('.'))
#     #     module_info = self.module_info
#     #     for path_item in module_path:
#     #         module_info = module_info.object_dict[path_item]
#     #
#     #     if node.names:
#     #         # Добавление импортируемых объектов
#     #         for alias in node.names:
#     #             object_name = alias.asname or alias.name
#     #             object_info = module_info.object_dict[alias.name]
#     #             if not isinstance(object_info, ConstantObjectInfo):
#     #                 object_info = ReferenceObjectInfo(module_info.context_path + [object_name], object_info)
#     #             module_info.object_dict[object_name] = object_info
#     #     else:
#     #         # Добавление модуля как объекта
#     #         module_name = module_path[-1]
#     #         object_info = ReferenceObjectInfo(module_info.context_path + [module_name], module_info)
#     #         module_info.context_vars.object_dict[module_name] = object_info
#
#     # def visit_JSCall(self, node: js_ast.JSCall):
#     #     func: js_ast.JSExpression = node.func
#     #     id_info = None
#     #     if isinstance(func, js_ast.JSName):
#     #         # Вызов функции
#     #         id_info = get_object_from_node(self.module_info, self.module_info.context_path, func)
#     #     elif isinstance(func, js_ast.JSAttribute):
#     #         # Вызов метода
#     #         node_attr: js_ast.JSAttribute = func
#     #         if isinstance(node_attr.value, js_ast.JSName):
#     #             id_info = get_object_from_node(self.module_info, self.module_info.context_path, node_attr)
#
#     def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef):
#         func_name = node.name
#
#         function_context = self.module_info.context_path + [func_name]
#         function_info = FunctionObjectInfo(function_context)
#         self.module_info.object_dict[func_name] = function_info
#
#         new_args = self.visit(node.args) or node.args
#         # original_context_path = self.module_info.context_path
#         # self.context_path = function_context
#         # try:
#         # for arg in chain(new_args.args or [], new_args.kwonlyargs or []):
#         #     arg_name = arg.arg
#         #     self._set_context_variable(function_info, arg_name, arg)
#         # finally:
#         #     self.context_path = original_context_path
#
#         body_transformer = BodyTransformer(node.body, function_context, self.root_object)
#         new_body = body_transformer.transform()
#         if new_args or new_body:
#             return js_ast.JSFunctionDef(node.name, new_args or node.args, new_body or node.body)
#         return None
#
#     # def _set_context_variable(
#     #         self,
#     #         target_context: ObjectInfo,
#     #         target_name: str,
#     #         node: js_ast.JSNode,
#     # ) -> ObjectInfo:
#         # value_context = get_object_from_node(self.module_info, target_context.context_path, node)
#         # if value_context.context_path:
#         #     if isinstance(value_context, ConstantObjectInfo):
#         #         value_context = ConstantObjectInfo(target_context.context_path + [target_name], value_context.value)
#         #     else:
#         #         value_context = ReferenceObjectInfo(target_context.context_path + [target_name], value_context)
#         # else:
#         #     value_context.context_path = target_context.context_path + [target_name]
#         # target_context.object_dict[target_name] = value_context
#         # return value_context
#         # object_info = get_object_info_by_node(target_context.context_path, node)
#         # target_context.object_dict[target_name] = object_info
#         # return object_info


def _one_of(*args):
    for item in args:
        if item is not None:
            return True
    return False


def _or(item1, item2) -> Any:
    if item1 is not None:
        return item1
    return item2


class Transformer:
    """Базовый класс для преобразования AST JavaScript"""
    def __init__(self, context_path: List[str], root_object: ObjectInfo):
        self.context_path = context_path
        self.root_object = root_object
        self.context_vars: ObjectInfo = get_object_by_path(root_object, '.'.join(context_path))
        if self.context_vars is None:
            self.context_vars = self.root_object


    """Базовый класс для посещения узлов AST JavaScript"""
    def visit(self, node: js_ast.JSNode | List[js_ast.JSStatement]) \
            -> Optional[Union[js_ast.JSNode, List[js_ast.JSNode]]]:
        if isinstance(node, list):
            return self.visit_list(node)

        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name)
        return method(node)

    def visit_list(self, node_list: list[js_ast.JSStatement]) -> Optional[List[js_ast.JSStatement]]:
        new_list = []
        modified = False
        for item in node_list:
            new_item = self.visit(item)
            if new_item:
                modified = True
                if isinstance(new_item, js_ast.JSNop):
                    continue
                new_list.append(new_item)
            else:
                new_list.append(item)

        if modified:
            return new_list

        return None

    def visit_JSLet(self, node: js_ast.JSLet) -> Optional[js_ast.JSLet]:
        new_assign: js_ast.JSAssign | None = self.visit(node.assign)
        if new_assign:
            return js_ast.JSLet(new_assign)
        return None

    def visit_JSConstant(self, node: js_ast.JSConstant) -> Optional[js_ast.JSConstant]:
        pass

    def visit_JSArguments(self, node: js_ast.JSArguments) -> Optional['js_ast.JSArguments']:
        args = node.args
        new_args = self.visit(args) if args else None
        defaults = node.defaults
        new_defaults = self.visit(defaults) if defaults else None
        vararg = node.vararg
        new_vararg = self.visit(vararg) if vararg else None
        kwonlyargs = node.kwonlyargs
        new_kwonlyargs = self.visit(kwonlyargs) if kwonlyargs else None
        kw_defaults = node.kw_defaults
        new_kw_defaults = self.visit(kw_defaults) if kw_defaults else None
        kwarg = node.kwarg
        new_kwarg = self.visit(kwarg) if kwarg else None

        if _one_of(new_args, new_defaults, new_vararg, new_kwonlyargs, new_kw_defaults, new_kwarg):
            return js_ast.JSArguments(_or(new_args, args), _or(new_defaults, defaults), _or(new_vararg, vararg),
                                      _or(new_kwonlyargs, kwonlyargs), _or(new_kw_defaults, kw_defaults),
                                      _or(new_kwarg, kwarg))
        return None

    def visit_JSAlias(self, node: js_ast.JSAlias) -> Optional[js_ast.JSAlias]:
        pass

    def visit_JSArg(self, node: js_ast.JSArg) -> Optional[js_ast.JSArg]:
        if node.arg == 'self':
            return js_ast.JSNop()
        return None

    def visit_JSNop(self, node: js_ast.JSNop) -> Optional[js_ast.JSNop]:
        pass

    def visit_JSCodeExpression(self, node: js_ast.JSCodeExpression) -> Optional[js_ast.JSCodeExpression]:
        new_value = self.visit(node.value)
        if not new_value:
            return None

        assert isinstance(new_value, (js_ast.JSExpression, js_ast.JSStatement))
        return js_ast.JSCodeExpression(new_value)

    def visit_JSStatement(self, node: js_ast.JSStatement) -> Optional[js_ast.JSStatement]:
        return None

    def visit_JSExpression(self, node: js_ast.JSExpression) -> Optional[js_ast.JSExpression]:
        return None

    def visit_JSBinOp(self, node: js_ast.JSBinOp) -> Optional[js_ast.JSBinOp]:
        pass

    def visit_JSAttribute(self, node: js_ast.JSAttribute) -> Optional[js_ast.JSAttribute]:
        new_value = self.visit(node.value)
        if new_value:
            return js_ast.JSAttribute(new_value or node.value, node.attr)
        return None

    def visit_JSKeyWord(self, node: js_ast.JSKeyWord) -> Optional[js_ast.JSKeyWord]:
        new_value = self.visit(node.value)
        if new_value:
            return js_ast.JSKeyWord(arg=node.arg, value=_or(new_value, node.value))
        return None

    def visit_JSReturn(self, node: js_ast.JSReturn) -> Optional[js_ast.JSReturn]:
        new_value = self.visit_JSExpression(node.value)
        if new_value:
            return js_ast.JSReturn(new_value)
        return None

    def visit_JSAssign(self, node: js_ast.JSAssign) -> Optional[js_ast.JSAssign]:
        new_target = self.visit(node.target)
        new_value = self.visit(node.value)
        visited_node = None
        if new_target or new_value:
            visited_node = js_ast.JSAssign(new_target or node.target, new_value or node.value)

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
            node: js_ast.JSNode,
    ) -> Optional[ObjectInfo]:
        value_context = get_object_from_node(target_context, node)
        target_context.objects[target_name] = value_context
        return value_context

    def _visit_js_assign_to_name(self, node: js_ast.JSAssign) -> Optional[js_ast.JSLet]:
        pass

    def _visit_js_assign_to_attribute(self, node: js_ast.JSAssign) -> Optional[js_ast.JSNop]:
        result = None
        target_name = node.target.attr

        target_object = get_object_from_node(self.context_vars, node.target.value)
        value_object = get_object_from_node(self.context_vars, node.value)
        if target_name == '__ty_alias__':
            result = js_ast.JSNop()
        target_object.objects[target_name] = value_object

        return result

    def visit_JSName(self, node: js_ast.JSName) -> Optional[js_ast.JSName]:
        object_info = get_object_from_node(self.context_vars, node)
        if object_info and '__ty_alias__' in object_info.objects:
            target_object_name = object_info.objects['__ty_alias__'].object_value
            if not target_object_name in self.context_vars.objects:
                self.context_vars.objects[target_object_name] = object_info
            return js_ast.JSName(target_object_name)
        return None

    def visit_JSCall(self, node: js_ast.JSCall) -> Optional[js_ast.JSCall or js_ast.JSNew]:
        new_func = self.visit(node.func)
        new_args = self.visit(node.args) if node.args else None
        new_keywords = self.visit(node.keywords) if node.keywords else None
        visited_node = None
        if new_func or new_args or new_keywords:
            visited_node = js_ast.JSCall(new_func or node.func, new_args or node.args, new_keywords or node.keywords)
        node = visited_node or node

        new_node = self._check_and_transform_call_to_new(node)
        if new_node:
            return new_node

        return visited_node

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        func_name = node.name

        function_context = self.context_path + [func_name]

        new_args = self.visit(node.args) or node.args

        body_transformer = BodyTransformer(node.body, function_context, self.root_object)
        new_body = body_transformer.transform()
        if new_args or new_body:
            return js_ast.JSFunctionDef(node.name, new_args or node.args, new_body or node.body)
        return None

    def visit_JSList(self, node: js_ast.JSList):
        return node

    def visit_JSIf(self, node: js_ast.JSIf):
        return None

    def _check_and_transform_call_to_new(self, node: js_ast.JSCall) -> Optional[js_ast.JSNew]:
        id_info = get_object_from_node(self.context_vars, node.func)
        if isinstance(id_info, ObjectClass):
            return js_ast.JSNew(class_=node.func, args=node.args, keywords=node.keywords)
        return None


class BodyTransformer(Transformer):
    """Класс преобразует тело модуля"""
    def __init__(
            self,
            body: List[js_ast.JSStatement],
            context_path: List[str],
            root_object: ObjectInfo,
    ):
        super().__init__(context_path, root_object)
        self.body = body
        self.body_vars = set()

    def transform(self):
        new_body = self.visit(self.body)
        if new_body:
            self.body = new_body
            return new_body
        return None

    def _visit_js_assign_to_name(self, node: js_ast.JSAssign) -> Optional[js_ast.JSLet]:
        name = node.target.id
        new_node = None
        if not name in self.body_vars:
            new_node = js_ast.JSLet(node)
            self.body_vars.add(name)

        value_object = get_object_from_node(self.context_vars, node.value)
        self.context_vars.objects[node.target.id] = value_object
        return new_node

    def visit_JSClassDef(self, node: js_ast.JSClassDef) -> Optional['js_ast.JSClassDef']:
        class_context = self.context_path + [node.name]
        class_transformer = ClassTransformer(node, class_context, self.root_object)
        new_class_def = class_transformer.transform()
        return new_class_def

    def visit_JSImport(self, node: js_ast.JSImport) -> Optional[js_ast.JSImport]:
        names = []
        for name in node.names:
            new_name = self.visit_JSAlias(name)
            if new_name:
                names.append(new_name)
            else:
                names.append(name)

        visited_node = None
        if names:
            visited_node = js_ast.JSImport(node.module, names, node.alias)

        return visited_node


class ClassTransformer(Transformer):
    """Класс трансформирует объявления класса в объекте"""
    def __init__(self, class_def: js_ast.JSClassDef, context_path: List[str], root_object: ObjectInfo):
        super().__init__(context_path, root_object)
        self.class_def = class_def

    def transform(self) -> Optional[js_ast.JSClassDef]:
        new_body = self.visit_list(self.class_def.body)
        if new_body:
            return js_ast.JSClassDef(self.class_def.name, new_body)
        return None

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        method_name = node.name
        if method_name == '__init__':
            method_name = 'constructor'

        new_args = self.visit(node.args) or node.args
        method_context = self.context_path + [method_name]

        body_transformer = BodyTransformer(node.body, method_context, self.root_object)
        new_body = body_transformer.transform()
        return js_ast.JSMethodDef(name=method_name, args=new_args, body=new_body or node.body)
