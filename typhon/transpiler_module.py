import ast
import os.path

from typhon.transpiler import Transpiler


class Module:
    def __init__(self, source_file_path: str, source_path: str = None):
        self.source_file_path = source_file_path
        file_name, ext = os.path.splitext(source_file_path)
        self.target_file_name = f'{file_name}.js'
        self.ast_dump_name = f'{file_name}_ast.txt'
        self.source_path = source_path

    def transpile(self):
        transpiler = Transpiler(self.get_source())

        try:
            target_code = transpiler.transpile()
        finally:
            if transpiler.py_tree:
                ast_dump_file = os.path.join(self.source_path, self.ast_dump_name)
                with open(ast_dump_file, 'w') as f:
                    f.write(ast.dump(transpiler.py_tree, indent=2))

        target_file_name = os.path.join(self.source_path, self.target_file_name)
        with open(target_file_name, 'w') as f:
            f.write(target_code)

        return self.target_file_name

    def get_source(self):
        source_file_path = os.path.join(self.source_path, self.source_file_path)
        with open(source_file_path, 'r') as f:
            source_code = f.read()
        return source_code
