import copy

from typhon import js_ast
from typhon.identifires import ID_VAR
from typhon.module_info import ModuleInfo
from typhon.module_transpiler import ModuleTranspiler


class TestTranspiler:
    @staticmethod
    def transform(js_tree: js_ast.JSModule):
        transpiler = ModuleTranspiler(None)
        transpiler.js_tree = js_tree
        transpiler.transform()
        return transpiler.js_tree

    def test_transform(self):
        js_module = js_ast.JSModule(body=[
            js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
            js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant('test')),
            js_ast.JSFunctionDef('foo', js_ast.JSArguments(), []),
        ])

        js_module = self.transform(js_module)

        assert js_module.export == js_ast.JSExport(['a', 'b', 'foo'])

    def test_transform__insert_let(self):
        original_body = [
            js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
            js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant('test')),
        ]
        js_module = js_ast.JSModule(body=copy.deepcopy(original_body))

        js_module = self.transform(js_module)

        assert js_module.export == js_ast.JSExport(['a'])
        assert js_module.body[0] == js_ast.JSLet(original_body[0])
        assert js_module.body[1] == original_body[1]

    def test_transform__export_imports(self):
        js_module = js_ast.JSModule(body=[
            js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')]),
        ])

        js_module = self.transform(js_module)

        assert js_module.export == js_ast.JSExport(['var_a', 'foo'])

    def test_transform__export_imports__all(self):
        js_module = js_ast.JSModule(body=[js_ast.JSImport('test', names=[])])
        js_module = self.transform(js_module)
        assert js_module.export == js_ast.JSExport(['test'])

    def test_transform__export_class_names(self):
        js_module = js_ast.JSModule(body=[js_ast.JSClassDef(name='TestClass', body=[])])
        js_module = self.transform(js_module)
        assert js_module.export == js_ast.JSExport(['TestClass'])

    def test_import_object_to_globals(self, temp_dir):
        source_1 = 'from test import a'
        source_2 = 'a = 123'

        transpiler = ModuleTranspiler(source_2)
        transpiler.transpile()
        module_info_2 = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)

        transpiler = ModuleTranspiler(source_1, related_modules={'test': module_info_2})
        transpiler.transpile()

        assert list(transpiler.globals.keys()) == ['a']
        object_info = transpiler.globals['a']
        assert object_info.name == 'a'
        assert object_info.object_type == ID_VAR
