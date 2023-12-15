from typhon.import_graph import ImportGraph
from typhon.module_info import ModuleInfo
from typhon.module_tools import Module, get_module_from_file
from typhon.module_transpiler import ModuleTranspiler


class Project:
    def __init__(self, source_path: str = None):
        self.import_graph = {}
        self.source_path = source_path or '.'
        self.module_info_list = {}

    def transpile_source(self, source: str) -> str:
        """
        Транспиляция переданного исходного кода. В ответе возвращается js-код.
        """
        self.transpile_related_modules(source)
        module = Module(source_path=self.source_path)
        return self.transpile_module(module, source)

    def transpile_related_modules(self, source: str):
        self.get_import_graph(source)
        modules = self.get_sorted_modules_from_graph()
        for module_name in modules:
            if module_name == '__main__':
                continue
            module = Module(module_name, self.source_path)
            self.transpile_module(module)

    def get_import_graph(self, source: str):
        import_graph = ImportGraph(source, source_path=self.source_path)
        self.import_graph = import_graph.get_graph()

    def transpile_file(self, source_file_path: str) -> str:
        """
        Транспиляция файла с исходным кодом. В ответ возвращается путь к оттранспилированному js-файлу.
        """
        module = get_module_from_file(source_file_path)
        self.transpile_related_modules(module.get_source())
        self.transpile_module(module)
        return module.target_file_name

    def get_sorted_modules_from_graph(self):
        result = []

        def add_modules(from_module: str):
            if from_module in result:
                return

            modules = self.import_graph.get(from_module, [])
            for module in modules:
                add_modules(module)
            result.append(from_module)

        add_modules('__main__')
        return result

    def transpile_module(self, module: Module, source: str = None):
        related_modules = self.get_related_modules(module.module_name)

        transpiler = ModuleTranspiler(source or module.get_source(), related_modules)
        try:
            target_code = transpiler.transpile()
        finally:
            module.dump_ast(transpiler.py_tree)

        module_info = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)
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
