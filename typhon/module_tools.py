import ast
import json
import os.path
from functools import cached_property

from typhon.module_info import ModuleInfo, serialize_module_info, deserialize_module_info


class Module:
    def __init__(self, source_path: str = None):
        self.source_path = source_path
        self.target_file_name = None
        self.ast_dump_name = None
        self.module_name = '__main__'

    def save_js(self, target_code):
        if not self.target_file_name:
            return

        target_file_name = os.path.join(self.source_path, self.target_file_name)
        with open(target_file_name, 'w') as f:
            f.write(target_code)

    def dump_ast(self, py_tree: ast.AST):
        if not py_tree:
            return

        if not self.ast_dump_name:
            return

        ast_dump_file = os.path.join(self.source_path, self.ast_dump_name)
        with open(ast_dump_file, 'w') as f:
            f.write(ast.dump(py_tree, indent=2))

    def get_source(self):
        return ''

    @cached_property
    def cache_directory(self):
        cache_directory = os.path.join(self.source_path, '.ty_cache')
        if not os.path.exists(cache_directory):
            os.mkdir(cache_directory)

        gitignore_file = os.path.join(cache_directory, '.gitignore')
        with open(gitignore_file, 'w') as f:
            f.write('*')

        return cache_directory

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


class ModuleFile(Module):
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


class ModuleSource(Module):
    def __init__(self, source: str, source_path: str = None):
        super().__init__(source_path)
        self.source = source

    def get_source(self):
        return self.source
