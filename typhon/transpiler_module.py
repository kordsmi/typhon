import ast
import datetime
import json
import os.path
from functools import cached_property

from typhon import js_ast
from typhon.generator import generate_js_module
from typhon.js_analyzer import BodyTransformer
from typhon.js_node_serializer import serialize_js_node, JSNodeDeserializer
from typhon.object_info_serializer import serialize_object_info, deserialize_object_info
from typhon.transpiler import transpile_module


class ModuleTranspiler:
    def __init__(self, source_path: str = None):
        self.source_path = source_path
        self.target_file_name = None
        self.ast_dump_name = None
        self.py_tree = None
        self.js_tree = None
        self.globals = {}
        self.module_name = '__main__'
        self.related_modules = {}

    def transpile(self, related_modules: dict = None):
        self.related_modules = related_modules or {}
        try:
            target_code = self.transpile_module()
        finally:
            self.dump_ast()

        self.save_js(target_code)
        self.save_info()
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
        body_transformer = BodyTransformer(self.js_tree.body, scope='global', related_modules=self.related_modules)
        new_body = body_transformer.transform()
        self.globals = body_transformer.get_globals()
        export = js_ast.JSExport(list(self.globals.keys()))
        self.js_tree = js_ast.JSModule(body=new_body or self.js_tree.body, export=export)

    @cached_property
    def cache_directory(self):
        cache_directory = os.path.join(self.source_path, '.ty_cache')
        if not os.path.exists(cache_directory):
            os.mkdir(cache_directory)

        gitignore_file = os.path.join(cache_directory, '.gitignore')
        with open(gitignore_file, 'w') as f:
            f.write('*')

        return cache_directory

    def save_info(self):
        json_info_file = os.path.join(self.cache_directory, f'{self.module_name}.json')
        info = self.get_module_info()
        with open(json_info_file, 'w') as f:
            json.dump(info, f)

    def get_module_info(self) -> dict:
        objects = []
        for name, object_info in self.globals.items():
            objects.append(serialize_object_info(object_info))
        return {
            'updated': datetime.datetime.now().isoformat(),
            'objects': objects,
            'nodes': serialize_js_node(self.js_tree),
        }

    def load_info(self):
        json_info_file = os.path.join(self.cache_directory, f'{self.module_name}.json')
        with open(json_info_file, 'r') as f:
            info_data = json.load(f)

        self.update_from_loaded_info(info_data)

    def update_from_loaded_info(self, info_data: dict):
        objects = info_data.get('objects')
        nodes_info = info_data.get('nodes', {})
        node_deserializer = JSNodeDeserializer(nodes_info)
        self.js_tree = node_deserializer.deserialize()

        self.globals = {}
        for object_data in objects:
            object_info = deserialize_object_info(object_data, node_deserializer.nodes_by_ids)
            self.globals[object_info.name] = object_info


class ModuleFile(ModuleTranspiler):
    def __init__(self, source_file_path: str, source_path: str = None):
        super().__init__(source_path)
        self.source_file_path = source_file_path
        file_name, ext = os.path.splitext(source_file_path)
        self.target_file_name = f'{file_name}.js'
        self.ast_dump_name = f'{file_name}_ast.txt'
        self.module_name = os.path.basename(file_name)

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
