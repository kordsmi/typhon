from dataclasses import dataclass
from typing import Optional

from typhon import js_ast
from typhon.exceptions import UnsupportedNode


ID_VAR = 'var'
ID_CLASS = 'class'
ID_FUNCTION = 'function'
ID_IMPORT = 'import'
ID_CALL = 'call'


class NoName:
    pass


@dataclass
class ObjectInfo:
    name: str
    node: js_ast.JSNode
    object_type: str
    attributes = {}


def get_object_name_and_type(node):
    name = None

    if isinstance(node, js_ast.JSLet):
        node = node.assign
    if isinstance(node, js_ast.JSAssign):
        target = node.target
        if isinstance(target, js_ast.JSName):
            name = target.id
        elif isinstance(target, js_ast.JSAttribute):
            name = NoName
        id_type = ID_VAR
    elif isinstance(node, js_ast.JSClassDef):
        name = node.name
        id_type = ID_CLASS
    elif isinstance(node, js_ast.JSFunctionDef):
        name = node.name
        id_type = ID_FUNCTION
    elif isinstance(node, js_ast.JSImport):
        id_type = ID_IMPORT
    elif isinstance(node, js_ast.JSCall):
        name = node.func
        id_type = ID_CALL
    else:
        raise UnsupportedNode(f'Cannot add unsupported node {node.__class__} to identifiers')
    return id_type, name


def get_object_info(node: js_ast.JSNode, name: Optional[str] = None) -> ObjectInfo:
    object_type, object_name = get_object_name_and_type(node)
    if not object_name:
        if not name:
            raise Exception(f'Cannot detect object name for node {node}')
        object_name = name
    return ObjectInfo(object_name, node, object_type)


class ContextObjects:
    def __init__(self, globals: dict = None, context: dict = None, scope: str = 'local'):
        self.globals = globals or {}
        self.context = context or {}
        self.locals = {}
        self.scope = scope

    def add(self, node: js_ast.JSNode, name: str = None):
        object_info = get_object_info(node, name)
        if self.scope == 'global':
            self.globals[object_info.name] = object_info
        else:
            self.locals[object_info.name] = object_info

    def get_id_info(self, object_name: str) -> Optional[ObjectInfo]:
        object_info = self.locals.get(object_name)
        if not object_info:
            object_info = self.context.get(object_name,)
        if not object_info:
            object_info = self.globals.get(object_name)
        return object_info

    def get_id_list(self) -> [str]:
        result = []

        def add_result(id_list: [str]):
            for id_name in id_list:
                if id_name not in result:
                    result.append(id_name)

        add_result(self.globals.keys())
        add_result(self.context.keys())
        add_result(self.locals.keys())

        return result

    def get_local_context_ids(self) -> dict:
        result = {}
        result.update(self.context)
        result.update(self.locals)
        return result
