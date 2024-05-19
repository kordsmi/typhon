import ast
from _ast import Import, AST
from typing import Any

from typhon.exceptions import TyphonImportError
from typhon.module import Module
from typhon.source_manager import SourceManager
from typhon.types import ModulePath


class ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.imports = []

    def visit_Import(self, node: Import) -> Any:
        names: [ast.alias] = node.names
        for name in names:
            self.imports.append(ModulePath('', name.name))

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
    def __init__(self, source: str, source_manager: SourceManager):
        self.source = source
        self.graph = {}
        self.queue = []
        self.source_manager = source_manager

    def get_graph(self) -> dict:
        self.graph = {}
        self.queue = []
        self.get_imports_and_add_to_queue(ModulePath('', '__main__'), self.source)

        while self.queue:
            module_path = self.queue.pop(0)
            if module_path in self.graph:
                continue

            source = self.get_module_source(module_path)
            self.get_imports_and_add_to_queue(module_path, source)

        self.detect_loop()

        return self.graph

    def get_module_source(self, module_path: ModulePath):
        module = Module(module_path, self.source_manager)
        return module.get_source()

    def get_imports_and_add_to_queue(self, module_path: ModulePath, source):
        imports = self.get_imports(source)
        self.graph[module_path] = imports
        self.queue.extend(imports)

    def get_imports(self, source) -> [str]:
        py_ast = ast.parse(source)
        import_collector = ImportCollector()
        import_collector.visit(py_ast)
        return import_collector.imports

    def detect_loop(self):
        graph_stack = []
        checked_modules = []

        def check_loop(module_path: ModulePath):
            if module_path in checked_modules:
                return

            if module_path in graph_stack:
                modules_chain = [f'{module.package}.{module.name}' for module in graph_stack + [module_path]]
                raise TyphonImportError(
                    f'There is circular imports detected: {" -> ".join(modules_chain)}'
                )

            graph_stack.append(module_path)
            modules = self.graph[module_path]
            for imported_module_path in modules:
                check_loop(imported_module_path)
            graph_stack.pop()

        check_loop(ModulePath('', '__main__'))
