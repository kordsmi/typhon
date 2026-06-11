import ast
from typing import Any, Optional

from typhon.types import ModulePath

OT_MODULE = 'module'
OT_REFERENCE = 'reference'
OT_FUNCTION = 'function'
OT_ARGUMENT = 'argument'
OT_CLASS = 'class'

Undefined = object()


class ObjectInfo:

    def __init__(self, object_type: str = '', object_value: Any = Undefined):
        self.objects: dict [str, ObjectInfo] = {}
        self.object_type = object_type
        self.object_value = object_value

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        return (
            self.object_type == other.object_type
            and self.object_value == other.object_value
            and self.objects == other.objects
        )

    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.object_type)}, {repr(self.object_value)})'

    def add_object(self, object_name: str, object_info: 'ObjectInfo'):
        self.objects[object_name] = object_info


class ObjectConstant(ObjectInfo):

    def __init__(self, object_value: Any):
        object_type = type(object_value).__name__
        super().__init__(object_type, object_value=object_value)

    def __repr__(self):
        return str(self.object_value)


class ObjectReference(ObjectInfo):

    def __init__(self, reference: str):
        super().__init__(OT_REFERENCE, reference)

    def __eq__(self, other: 'ObjectReference'):
        if not super().__eq__(other):
            return False
        return self.object_value == other.object_value


class ObjectFunction(ObjectInfo):

    def __init__(self, function_name: str):
        super().__init__(OT_FUNCTION, function_name)
        self.locals = ObjectInfo('', None)

    def __eq__(self, other: 'ObjectFunction'):
        if not super().__eq__(other):
            return False
        res = self.locals == other.locals
        return res

    def __repr__(self):
        return f'<function {self.object_value}>'


class ObjectArgument(ObjectInfo):

    def __init__(self):
        super().__init__(OT_ARGUMENT, None)


class ObjectModule(ObjectInfo):
    def __init__(self, module_path: ModulePath):
        super().__init__(OT_MODULE, module_path.name)
        self.module_path = module_path


class ObjectClass(ObjectInfo):

    def __init__(self, name: str):
        super().__init__(OT_CLASS, name)

    def __repr__(self):
        return f'<class {self.object_value}>'


def dump_object(object_info: ObjectInfo) -> dict:
    if object_info is None:
        return {}

    result = {
        'type': object_info.object_type,
        'value': object_info.object_value,
    }

    objects_info = {}
    for obj_name, obj_info in object_info.objects.items():
        objects_info[obj_name] = dump_object(obj_info)

    result['objects'] = objects_info

    if isinstance(object_info, ObjectFunction):
        result['locals'] = dump_object(object_info.locals)

    return result


class ObjectCollector(ast.NodeVisitor):

    def __init__(self, object_info: ObjectInfo):
        super().__init__()
        self.object_info = object_info

    def visit_body(self, body: list[ast.stmt]):
        for stmt in body:
            self.visit(stmt)

    def visit_Assign(self, node: ast.Assign):
        targets = node.targets

        for target in targets:
            self._add_object_info(target, node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        object_function = ObjectFunction(node.name)
        self.object_info.add_object(node.name, object_function)
        object_function.locals = object_function.locals

        arguments = node.args
        for arg in arguments.args:
            object_function.locals.add_object(arg.arg, ObjectArgument())
        for arg in arguments.kwonlyargs:
            object_function.locals.add_object(arg.arg, ObjectArgument())

        body_collector = ObjectCollector(object_function.locals)
        body_collector.visit_body(node.body)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_name = alias.name
            name = alias.asname or module_name
            self.object_info.add_object(name, ObjectReference(module_name))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module_name = node.module
        for alias in node.names:
            variable_name = alias.name
            variable_alias = alias.asname or variable_name
            reference = f'{module_name}.{variable_name}'
            self.object_info.add_object(variable_alias, ObjectReference(reference))

    def visit_ClassDef(self, node: ast.ClassDef):
        object_class = ObjectClass(node.name)
        self.object_info.add_object(node.name, object_class)

        class_collector = ObjectCollector(object_class)
        class_collector.visit_body(node.body)

    def _add_object_info(self, target: ast.expr, value: ast.expr):
        if isinstance(target, ast.Name):
            object_value = self._get_object_value(value)
            self.object_info.add_object(target.id, object_value)
        elif isinstance(target, ast.Tuple):
            self._assign_to_tuple(target, value)

    def _get_object_value(self, value: ast.expr) -> Optional[ObjectInfo]:
        if isinstance(value, ast.Constant):
            object_value = ObjectConstant(value.value)
        elif isinstance(value, ast.Name):
            object_value = ObjectReference(value.id)
        else:
            object_value = None
        return object_value

    def _assign_to_tuple(self, targets: ast.Tuple, values: ast.expr):
        if isinstance(values, ast.Tuple):
            for target, value in zip(targets.elts, values.elts):
                self._add_object_info(target, value)


def get_object_by_path(root_object: ObjectInfo, path: str) -> ObjectInfo | None:
    path_to_object = root_object
    for path_section in path.split('.'):
        if isinstance(path_to_object, ObjectFunction) and path_section in path_to_object.locals.objects:
            path_to_object = path_to_object.locals.objects[path_section]
            continue
        if not path_section in path_to_object.objects:
            return None
        path_to_object = path_to_object.objects[path_section]
    return path_to_object
