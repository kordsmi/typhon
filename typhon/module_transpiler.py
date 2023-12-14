import ast
from typing import Dict

from typhon import js_ast
from typhon.generator import generate_js_module
from typhon.js_analyzer import BodyTransformer
from typhon.module_info import ModuleInfo
from typhon.transpiler import transpile_module


class ModuleTranspiler:
    def __init__(self, source: str, related_modules: Dict[str, ModuleInfo] = None):
        self.source = source
        self.related_modules = related_modules or {}
        self.py_tree = None
        self.js_tree = None
        self.globals = {}

    def transpile(self) -> str:
        self.py_tree = ast.parse(self.source)
        self.js_tree = transpile_module(self.py_tree)
        self.transform()
        return generate_js_module(self.js_tree)

    def transform(self):
        body_transformer = BodyTransformer(self.js_tree.body, scope='global', related_modules=self.related_modules)
        new_body = body_transformer.transform()
        self.globals = body_transformer.get_globals()
        export = js_ast.JSExport(list(self.globals.keys()))
        self.js_tree = js_ast.JSModule(body=new_body or self.js_tree.body, export=export)
