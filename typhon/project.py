import os

from typhon.object_info import ObjectInfo
from typhon.import_graph import ImportGraph
from typhon.module_info import ModuleInfo
from typhon.module import Module, get_module_from_file
from typhon.source_manager import SourceManager
from typhon.types import ModulePath
from typhon.module_transpiler import ModuleTranspiler


class Project:
    def __init__(self, source_path: str = None):
        self.import_graph = {}
        self.source_manager = SourceManager(source_path)
        self.module_info_list = {}
        self.root_object = ObjectInfo(None)

    def transpile_source(self, source: str) -> str:
        """
        Транспиляция переданного исходного кода. В ответе возвращается js-код.
        """
        self.transpile_related_modules(source)
        module = Module(source_manager=self.source_manager)
        return self.transpile_module(module, source)

    def transpile_related_modules(self, source: str):
        self.get_import_graph(source)
        modules = self.get_sorted_modules_from_graph()
        for module_path in modules:
            if module_path.package == '' and module_path.name == '__main__':
                continue
            module = Module(module_path, self.source_manager)
            self.transpile_module(module)

    def get_import_graph(self, source: str):
        import_graph = ImportGraph(source, source_manager=self.source_manager)
        self.import_graph = import_graph.get_graph()

    def transpile_file(self, source_file_path: str) -> str:
        """
        Транспиляция файла с исходным кодом. В ответ возвращается путь к оттранспилированному js-файлу.
        """
        source_file_path = os.path.join(self.source_manager.project_path, source_file_path)
        module = get_module_from_file(source_file_path)
        self.transpile_related_modules(module.get_source())
        self.transpile_module(module)
        return module.target_file_name

    def get_sorted_modules_from_graph(self):
        result = []

        def add_modules(module_path: ModulePath):
            if module_path in result:
                return

            modules = self.import_graph.get(module_path, [])
            for module in modules:
                add_modules(module)
            result.append(module_path)

        add_modules(ModulePath('', '__main__'))
        return result

    def transpile_module(self, module: Module, source: str = None):
        module_name = module.module_name
        if module_name == '__init__':
            module_name = module.module_path.package
        transpiler = ModuleTranspiler(source or module.get_source(), self.root_object, module_name)
        try:
            target_code = transpiler.transpile()
        finally:
            module.dump_ast(transpiler.py_tree)

        module_info = ModuleInfo(objects=transpiler.module_object, js_tree=transpiler.js_tree)
        module.save_js(target_code)
        module.save_info(module_info)

        self.module_info_list[module.module_name] = module_info
        return target_code

    def get_related_modules(self, module_name):
        related_modules = {}
        module_imports = self.import_graph.get(module_name, [])
        for imported_module_name in module_imports:
            related_modules[imported_module_name] = self.module_info_list[imported_module_name]
        return related_modules
