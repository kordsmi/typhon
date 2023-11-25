from typhon.import_graph import ImportGraph
from typhon.transpiler_module import ModuleFile, ModuleSource


class Project:
    def __init__(self, source_path: str = None):
        self.import_graph = {}
        self.source_path = source_path or '.'

    def transpile_source(self, source: str) -> str:
        """
        Транспиляция переданного исходного кода. В ответе возвращается js-код.
        """
        module = ModuleSource(source, source_path=self.source_path)
        self.transpile_modules(source)
        return module.transpile()

    def transpile_modules(self, source: str):
        self.get_import_graph(source)
        modules = self.get_sorted_modules_from_graph()
        for module in modules:
            if module == '__main__':
                continue
            self.transpile_module(module)

    def get_import_graph(self, source: str):
        import_graph = ImportGraph(source, source_path=self.source_path)
        self.import_graph = import_graph.get_graph()

    def transpile_file(self, source_file_path: str) -> str:
        """
        Транспиляция файла с исходным кодом. В ответ возвращается путь к оттранспилированному js-файлу.
        """
        module = ModuleFile(source_file_path, source_path=self.source_path)
        self.transpile_modules(module.get_source())
        module.transpile()
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

    def transpile_module(self, module_name):
        module_file = module_name + '.py'
        module = ModuleFile(module_file, source_path=self.source_path)
        return module.transpile()
