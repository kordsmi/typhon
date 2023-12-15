import ast
import json
import os.path
from functools import cached_property

from typhon.module_info import ModuleInfo, serialize_module_info, deserialize_module_info


class Module:
    def __init__(self, module_name: str = None, source_path: str = None):
        self.source_path = source_path or '.'
        self.module_name = module_name or '__main__'

    def save_js(self, target_code):
        with open(self.target_file_name, 'w') as f:
            f.write(target_code)

    def dump_ast(self, py_tree: ast.AST):
        if not py_tree:
            return

        with open(self.ast_dump_file_name, 'w') as f:
            f.write(ast.dump(py_tree, indent=2))

    def get_source(self):
        filename = os.path.join(self.source_path, f'{self.module_name}.py')
        with open(filename, 'r') as f:
            source_code = f.read()
        return source_code

    @cached_property
    def cache_directory(self):
        cache_directory = os.path.join(self.source_path, '.ty_cache')
        if not os.path.exists(cache_directory):
            os.mkdir(cache_directory)

        gitignore_file = os.path.join(cache_directory, '.gitignore')
        with open(gitignore_file, 'w') as f:
            f.write('*')

        return cache_directory

    @property
    def target_file_name(self):
        return os.path.join(self.source_path, f'{self.module_name}.js')

    @property
    def ast_dump_file_name(self):
        return os.path.join(self.cache_directory, f'{self.module_name}_ast.txt')

    def save_info(self, module_info: ModuleInfo):
        json_info_file = os.path.join(self.cache_directory, f'{self.module_name}.json')
        module_info_data = serialize_module_info(module_info)
        with open(json_info_file, 'w') as f:
            json.dump(module_info_data, f)

    def load_info(self):
        json_info_file = os.path.join(self.cache_directory, f'{self.module_name}.json')
        with open(json_info_file, 'r') as f:
            info_data = json.load(f)

        return deserialize_module_info(info_data)


def get_module_from_file(source_file_path: str) -> Module:
    source_path, filename = os.path.split(source_file_path)
    filename, ext = os.path.splitext(filename)
    module = Module(module_name=filename, source_path=source_path)
    return module
