import copy

from typhon import js_ast
from typhon.object_info import ObjectInfo, ModuleObjectInfo, ConstantObjectInfo
from typhon.module_transpiler import ModuleTranspiler


class TestTranspiler:
    def setup_method(self, test_method):
        self.root_object = ObjectInfo(None)

    def transform(self, js_tree: js_ast.JSModule):
        transpiler = ModuleTranspiler(None, self.root_object, '__main__')
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
        module_object = ModuleObjectInfo('test', 'test')
        module_object.object_dict['a'] = ObjectInfo(None)
        module_object.object_dict['foo'] = ObjectInfo(None)
        self.root_object.object_dict['test'] = module_object
        js_module = js_ast.JSModule(body=[
            js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')]),
        ])

        js_module = self.transform(js_module)

        assert js_module.export == js_ast.JSExport(['var_a', 'foo'])
        assert self.root_object.object_dict['__main__'].object_dict == {
            'var_a': module_object.object_dict['a'],
            'foo': module_object.object_dict['foo'],
        }

    def test_transform__export_imports__all(self):
        module_object = ModuleObjectInfo('test', 'test')
        self.root_object.object_dict['test'] = module_object
        js_module = js_ast.JSModule(body=[js_ast.JSImport('test', names=[])])
        js_module = self.transform(js_module)
        assert js_module.export == js_ast.JSExport(['test'])
        assert self.root_object.object_dict['__main__'].object_dict == {
            'test': module_object,
        }

    def test_transform__export_class_names(self):
        js_module = js_ast.JSModule(body=[js_ast.JSClassDef(name='TestClass', body=[])])
        js_module = self.transform(js_module)
        assert js_module.export == js_ast.JSExport(['TestClass'])

    def test_import_object_to_globals(self, temp_dir):
        source_1 = 'from test import a'
        source_2 = 'a = 123'

        transpiler = ModuleTranspiler(source_2, self.root_object, 'test')
        transpiler.transpile()

        transpiler = ModuleTranspiler(source_1, self.root_object, '__main__')
        transpiler.transpile()

        assert list(transpiler.module_object.object_dict.keys()) == ['a']
        object_info = transpiler.module_object.object_dict['a']
        assert isinstance(object_info, ConstantObjectInfo)
        assert object_info.value == 123
