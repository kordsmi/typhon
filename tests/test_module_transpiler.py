import ast
import copy

from typhon import js_ast
from typhon.module_transpiler import ModuleTranspiler
from typhon.object_collector import ObjectModule, ObjectCollector
from typhon.transpiler import convert_ast
from typhon.types import ModulePath


class TestModuleTranspiler:
    def setup_method(self, test_method):
        self.root_object = ObjectModule(ModulePath('__main__'))

    def transform(self, source: str):
        transpiler = ModuleTranspiler(source, self.root_object, ModulePath('__main__'))
        transpiler.module_object = self.root_object
        transpiler.py_tree = ast.parse(source)
        transpiler.js_tree = convert_ast(transpiler.py_tree)

        collector = ObjectCollector(self.root_object)
        collector.visit(transpiler.py_tree)

        transpiler.transform()
        return transpiler.js_tree

    def test_base(self):
        ModuleTranspiler('', self.root_object, ModulePath('__main__'))
        special_info = self.root_object.objects['__special__']
        assert isinstance(special_info, ObjectModule)
        assert special_info.module_path.full_path == '__special__'

    def test_transform(self):
        source = "a=100\nb='test'\ndef foo(): pass"

        js_module = self.transform(source)

        assert js_module.export == js_ast.JSExport(['a', 'b', 'foo'])

    def test_transform__insert_let(self):
        original_body = [
            js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
            js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant('test')),
        ]
        source = "a=100\na='test'"

        js_module = self.transform(source)

        assert js_module.export == js_ast.JSExport(['a'])
        assert js_module.body[0] == js_ast.JSLet(original_body[0])
        assert js_module.body[1] == original_body[1]

    def test_transform__export_imports(self):
        source = 'from test import a as var_a, foo'

        js_module = self.transform(source)

        assert js_module.export == js_ast.JSExport(['var_a', 'foo'])
        assert list(self.root_object.objects.keys()) == [
            '__special__', 'var_a', 'foo',
        ]

    def test_transform__export_imports__all(self):
        source = 'import test'
        js_module = self.transform(source)
        assert js_module.export == js_ast.JSExport(['test'])
        assert list(self.root_object.objects.keys()) == [
            '__special__', 'test',
        ]

    def test_transform__export_class_names(self):
        source = 'class TestClass: pass'
        js_module = self.transform(source)
        assert js_module.export == js_ast.JSExport(['TestClass'])

    def test_special_module(self):
        """ Для модуля __special__ не нужно подключать модуль __special__ (самого себя) """
        self.transform('')
        assert self.root_object.objects['__special__'].objects == {}
