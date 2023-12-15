import ast
import os.path
from _ast import Import, AST
from typing import Any

from typhon.exceptions import TyphonImportError
from typhon.module_tools import get_module_from_file


class ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.imports = []

    def visit_Import(self, node: Import) -> Any:
        names: [ast.alias] = node.names
        for name in names:
            self.imports.append(name.name)

    def generic_visit(self, node: AST) -> Any:
        for field, value in ast.iter_fields(node):
            if field == 'body' and not isinstance(node, ast.Module):
                continue

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item)
            elif isinstance(value, AST):
                self.visit(value)


class ImportGraph:
    def __init__(self, source: str, source_path: str = None):
        self.source = source
        self.graph = {}
        self.queue = []
        self.source_path = source_path or '.'

    def get_graph(self) -> dict:
        self.graph = {}
        self.queue = []
        self.get_imports_and_add_to_queue('__main__', self.source)

        while self.queue:
            module_name = self.queue.pop(0)
            if module_name in self.graph:
                continue

            source = self.get_module_source(module_name)
            self.get_imports_and_add_to_queue(module_name, source)

        self.detect_loop()

        return self.graph

    def get_module_source(self, module_name):
        module_path = module_name + '.py'
        module = get_module_from_file(os.path.join(self.source_path, module_path))
        source = module.get_source()
        return source

    def get_imports_and_add_to_queue(self, module_name, source):
        imports = self.get_imports(source)
        self.graph[module_name] = imports
        self.queue.extend(imports)

    def get_imports(self, source) -> [str]:
        py_ast = ast.parse(source)
        import_collector = ImportCollector()
        import_collector.visit(py_ast)
        return import_collector.imports

    def detect_loop(self):
        graph_stack = []
        checked_modules = []

        def check_loop(module_name):
            if module_name in checked_modules:
                return

            if module_name in graph_stack:
                raise TyphonImportError(
                    f'There is circular imports detected: {" -> ".join(graph_stack + [module_name])}'
                )

            graph_stack.append(module_name)
            modules = self.graph[module_name]
            for imported_module_name in modules:
                check_loop(imported_module_name)
            graph_stack.pop()

        check_loop('__main__')
