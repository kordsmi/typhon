import ast

from typhon import js_ast
from typhon.generator import generate_js_module
from typhon.object_collector import ObjectModule, get_object_by_path
from typhon.js_analyzer import BodyTransformer
from typhon.transpiler import convert_ast
from typhon.types import ModulePath


class ModuleTranspiler:
    """Класс отвечает за процесс транспиляции модуля:
        - Парсинг исходного кода Python в AST
        - Транспиляция AST Python в AST JavaScript
        - Преобразование AST JavaScript через `BodyTransformer`
        - Генерация финального JS-кода
    """
    def __init__(self, source: str, root_object: ObjectModule, module_path: ModulePath):
        self.source = source
        self.py_tree = None
        self.js_tree = None
        self.module_path = module_path
        self.name = module_path.name
        if self.name == '__init__':
            self.name = module_path.module_path[-2]
        self.root_object: ObjectModule = root_object
        if module_path.name == self.root_object.module_path.name:
            self.module_object = self.root_object
        else:
            self.module_object = get_object_by_path(self.root_object, module_path.full_path)
        if self.name != '__special__':
            special_module_info = ObjectModule(ModulePath('__special__'))
            self.module_object.objects['__special__'] = special_module_info

    def transpile(self) -> str:
        self.py_tree = ast.parse(self.source)
        self.js_tree = convert_ast(self.py_tree)
        self.transform()
        return generate_js_module(self.js_tree)

    def transform(self):
        body_transformer = BodyTransformer(self.js_tree.body, [self.name], self.root_object)
        new_body = body_transformer.transform()
        export = js_ast.JSExport([module for module in self.module_object.objects if module != '__special__'])
        self.js_tree = js_ast.JSModule(body=new_body or self.js_tree.body, export=export)
