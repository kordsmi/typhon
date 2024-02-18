import ast

from typhon import js_ast
from typhon.generator import generate_js_module
from typhon.object_info import ObjectInfo, ModuleObjectInfo
from typhon.js_analyzer import BodyTransformer
from typhon.transpiler import transpile_module


class ModuleTranspiler:
    def __init__(self, source: str, root_object: ObjectInfo, module_name: str):
        self.source = source
        self.py_tree = None
        self.js_tree = None
        self.name = module_name
        self.root_object = root_object
        root_object.object_dict[self.name] = ModuleObjectInfo([self.name], self.name)
        self.module_object: ModuleObjectInfo = root_object.object_dict[self.name]
        if self.name != '__special__':
            special_module_info = ModuleObjectInfo([self.name, '__special__'], '__special__.py')
            self.module_object.object_dict['__special__'] = special_module_info

    def transpile(self) -> str:
        self.py_tree = ast.parse(self.source)
        self.js_tree = transpile_module(self.py_tree)
        self.transform()
        return generate_js_module(self.js_tree)

    def transform(self):
        body_transformer = BodyTransformer(self.js_tree.body, [self.name], self.root_object)
        new_body = body_transformer.transform()
        export = js_ast.JSExport([module for module in self.module_object.object_dict if module != '__special__'])
        self.js_tree = js_ast.JSModule(body=new_body or self.js_tree.body, export=export)
