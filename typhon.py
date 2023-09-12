import ast
import os.path
import sys

from typhon.transpiler import Transpiler


def main():
    source_name = sys.argv[1]
    file_name, ext = os.path.splitext(source_name)
    target_name = f'{file_name}.js'
    dump_name = f'{file_name}_ast.txt'

    with open(source_name, 'r') as f:
        source_code = f.read()

    transpiler = Transpiler(source_code)

    try:
        target_code = transpiler.transpile()
    finally:
        if transpiler.py_tree:
            with open(dump_name, 'w') as f:
                f.write(ast.dump(transpiler.py_tree, indent=2))

    with open(target_name, 'w') as f:
        f.write(target_code)


if __name__ == '__main__':
    main()
