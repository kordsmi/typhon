from dataclasses import dataclass
from typing import Optional

from typhon import js_ast
from typhon.exceptions import UnsupportedNode


ID_VAR = 'var'
ID_CLASS = 'class'
ID_FUNCTION = 'function'
ID_IMPORT = 'import'


@dataclass
class IDInfo:
    id: str
    node: js_ast.JSNode
    id_type: str


class Identifiers:
    def __init__(self):
        self.identifiers = {}

    def add(self, node: js_ast.JSNode, name: str = None):
        original_node = node

        if isinstance(node, js_ast.JSLet):
            node = node.assign

        if isinstance(node, js_ast.JSAssign):
            target = node.target
            if not name:
                if not isinstance(target, js_ast.JSName):
                    raise Exception('Invalid assignment operation for collecting information about a variable')
                name = target.id
            id_type = ID_VAR
        elif isinstance(node, js_ast.JSClassDef):
            name = name or node.name
            id_type = ID_CLASS
        elif isinstance(node, js_ast.JSFunctionDef):
            name = name or node.name
            id_type = ID_FUNCTION
        elif isinstance(node, js_ast.JSImport):
            if not name:
                raise Exception('The variable name for this node type was not passed')
            id_type = ID_IMPORT
        else:
            raise UnsupportedNode(f'Cannot add unsupported node {node.__class__} to identifiers')

        self.identifiers[name] = IDInfo(name, original_node, id_type)

    def get_id_info(self, id_name: str) -> Optional[IDInfo]:
        return self.identifiers.get(id_name)

    def get_id_list(self) -> [str]:
        return list(self.identifiers.keys())

    def copy_from(self, other):
        for id_name in other.get_id_list():
            self.identifiers[id_name] = other.get_id_info(id_name)


class ContextIdentifiers:
    def __init__(self, globals: Identifiers = None, context: Identifiers = None):
        self.globals = globals or Identifiers()
        self.context = context or Identifiers()
        self.locals = Identifiers()

    def add(self, node: js_ast.JSNode, name: str = None):
        self.locals.add(node, name)

    def get_id_info(self, id_name: str) -> Optional[IDInfo]:
        id_info = self.locals.get_id_info(id_name)
        if not id_info:
            id_info = self.context.get_id_info(id_name)
        if not id_info:
            id_info = self.globals.get_id_info(id_name)
        return id_info

    def get_id_list(self) -> [str]:
        result = []

        def add_result(id_list: [str]):
            for id_name in id_list:
                if id_name not in result:
                    result.append(id_name)

        add_result(self.globals.get_id_list())
        add_result(self.context.get_id_list())
        add_result(self.locals.get_id_list())

        return result

    def get_local_context_ids(self) -> Identifiers:
        result = Identifiers()
        result.copy_from(self.context)
        result.copy_from(self.locals)
        return result
