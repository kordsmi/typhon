import ast
import os

from typhon.object_collector import ObjectModule, ObjectCollector, ObjectInfo, ObjectReference, \
    ObjectFunction, get_object_by_path
from typhon.import_graph import ImportGraph
from typhon.module_info import ModuleInfo
from typhon.module import Module, get_module_from_file
from typhon.source_manager import SourceManager
from typhon.types import ModulePath
from typhon.module_transpiler import ModuleTranspiler


class Project:
    """Центральный компонент системы транспиляции. Он отвечает за:
        - Управление графом импортов
        - Управление кэшем и исходными файлами
        - Транспиляцию модулей и связанных с ними модулей
        - Управление информацией о модулях
    """
    def __init__(self, source_path: str = None):
        self.source_manager = SourceManager(source_path)
        self.module_info_list = {}
        self.root_object = ObjectModule(ModulePath(''))
        self.modules: list[ModulePath] = []
        self.main_source = ''

    def transpile_source(self, source: str) -> str:
        """
        Транспиляция переданного исходного кода. В ответе возвращается js-код.
        """
        module = Module(source_manager=self.source_manager)
        self.main_source = source
        return self.transpile_main_module(module, '__main__')

    def transpile_file(self, source_file_path: str) -> str:
        """
        Транспиляция файла с исходным кодом. В ответ возвращается путь к оттранспилированному js-файлу.
        """
        source_file_path = os.path.join(self.source_manager.project_path, source_file_path)
        module = get_module_from_file(source_file_path)
        self.main_source = module.get_source()
        self.transpile_main_module(module, module.module_name)
        return module.target_file_name

    def transpile_main_module(self, module, module_name):
        self.get_sorted_modules_from_source(self.main_source, module_name)
        self.collect_project_objects()
        self.transpile_related_modules()
        return self.transpile_module(module, self.main_source)

    def transpile_related_modules(self):
        for module_path in self.modules:
            if module_path.package == '' and module_path.name == '__main__':
                continue
            module = Module(module_path, self.source_manager)
            self.transpile_module(module)

    def get_sorted_modules_from_source(self, source: str, main_module_name: str) -> list[ModulePath]:
        self.modules = []

        import_graph = ImportGraph(source, source_manager=self.source_manager, main_module_name=main_module_name)
        graph = import_graph.get_graph()

        def add_modules(module_path: ModulePath):
            nonlocal graph

            if module_path in self.modules:
                return

            modules = graph.get(module_path.module_path, [])
            for module in modules:
                add_modules(module)
            self.modules.append(module_path)

        add_modules(ModulePath(main_module_name))

    def transpile_module(self, module: Module, source: str = None):
        transpiler = ModuleTranspiler(source or module.get_source(), self.root_object, module.module_path)
        try:
            target_code = transpiler.transpile()
        finally:
            module.dump_ast(transpiler.py_tree)

        module_info = ModuleInfo(objects=transpiler.module_object, js_tree=transpiler.js_tree)
        module.save_js(target_code)
        module.save_info(module_info)

        self.module_info_list[module.module_name] = module_info
        return target_code

    def collect_project_objects(self):
        """Собирает информацию по всем объектам проекта"""

        for module_path in self.modules:
            module = Module(module_path, self.source_manager)
            module_info = self.collect_objects_from_module(module)
            # Обход и замена ссылок на объект в модуле без учёта локальных переменных функций
            self.replace_references_to_objects(module_info)
        # Обход и замена всех остальных ссылок
        self.replace_references_to_objects(self.root_object, with_locals=True)

    def collect_objects_from_module(self, module: Module) -> ObjectModule:
        """Сбор объектов из модуля"""
        module_info = ObjectModule(module.module_path)

        # Получение объекта пакета для текущего пути модуля
        package_module_object = self.root_object
        for package in module.module_path.packages:
            if not package in package_module_object.objects:
                package_module_object.objects[package] = ObjectModule(package_module_object.module_path + [package])
            package_module_object = package_module_object[package]

        package_module_object.objects[module.module_name] = module_info
        collector = ObjectCollector(module_info)

        if module.module_path.name == '__main__':
            source = self.main_source
        else:
            source = module.get_source()
        collector.visit(ast.parse(source))

        return module_info

    def replace_references_to_objects(self, object_info: ObjectInfo, with_locals: bool = False):
        for object_name, object_item in object_info.objects.items():
            if isinstance(object_item, ObjectReference):
                object_ref = self.find_reference(object_item)
                object_info.objects[object_name] = object_ref
            elif with_locals and isinstance(object_item, ObjectFunction):
                self.replace_references_to_objects(object_item.locals, with_locals=with_locals)
            else:
                self.replace_references_to_objects(object_item, with_locals=with_locals)

    def find_reference(self, object_info: ObjectReference) -> ObjectInfo:
        path_to_object = get_object_by_path(self.root_object, object_info.object_value)

        return path_to_object
