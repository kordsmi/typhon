import ast
import os.path

from typhon import js_ast
from typhon.generator import generate_js_module
from typhon.js_analyzer import BodyTransformer
from typhon.transpiler import transpile_module


class ModuleTranspiler:
    def __init__(self, source_path: str = None):
        self.source_path = source_path
        self.target_file_name = None
        self.ast_dump_name = None
        self.py_tree = None
        self.js_tree = None

    def transpile(self):
        try:
            target_code = self.transpile_module()
        finally:
            self.dump_ast()

        self.save_js(target_code)
        return target_code

    def transpile_module(self):
        self.py_tree = ast.parse(self.get_source())
        self.js_tree = transpile_module(self.py_tree)
        self.transform()
        return generate_js_module(self.js_tree)

    def save_js(self, target_code):
        if not self.target_file_name:
            return

        target_file_name = os.path.join(self.source_path, self.target_file_name)
        with open(target_file_name, 'w') as f:
            f.write(target_code)

    def dump_ast(self):
        if not self.py_tree:
            return

        if not self.ast_dump_name:
            return

        ast_dump_file = os.path.join(self.source_path, self.ast_dump_name)
        with open(ast_dump_file, 'w') as f:
            f.write(ast.dump(self.py_tree, indent=2))

    def get_source(self):
        return ''

    def transform(self):
        body_transformer = BodyTransformer(self.js_tree.body)
        new_body = body_transformer.transform()
        info = body_transformer.get_identifies()
        export = js_ast.JSExport(info)
        self.js_tree = js_ast.JSModule(body=new_body or self.js_tree.body, export=export)


class ModuleFile(ModuleTranspiler):
    def __init__(self, source_file_path: str, source_path: str = None):
        super().__init__(source_path)
        self.source_file_path = source_file_path
        file_name, ext = os.path.splitext(source_file_path)
        self.target_file_name = f'{file_name}.js'
        self.ast_dump_name = f'{file_name}_ast.txt'

    def get_source(self):
        source_file_path = os.path.join(self.source_path, self.source_file_path)
        with open(source_file_path, 'r') as f:
            source_code = f.read()
        return source_code


class ModuleSource(ModuleTranspiler):
    def __init__(self, source: str, source_path: str = None):
        super().__init__(source_path)
        self.source = source

    def get_source(self):
        return self.source
