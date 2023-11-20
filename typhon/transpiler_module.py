import ast
import os.path

from typhon.transpiler import Transpiler


class Module:
    def __init__(self, source_file_path: str):
        self.source_file_path = source_file_path
        file_name, ext = os.path.splitext(source_file_path)
        self.target_file_name = f'{file_name}.js'
        self.ast_dump_name = f'{file_name}_ast.txt'

    def transpile(self):
        transpiler = Transpiler(self.get_source())

        try:
            target_code = transpiler.transpile()
        finally:
            if transpiler.py_tree:
                with open(self.ast_dump_name, 'w') as f:
                    f.write(ast.dump(transpiler.py_tree, indent=2))

        with open(self.target_file_name, 'w') as f:
            f.write(target_code)

        return self.target_file_name

    def get_source(self):
        with open(self.source_file_path, 'r') as f:
            source_code = f.read()
        return source_code
