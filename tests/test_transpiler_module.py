import copy
import datetime
import json
import os.path
from tempfile import TemporaryDirectory

from typhon import js_ast
from typhon.identifires import ID_VAR
from typhon.js_node_serializer import serialize_js_node
from typhon.module_info import ModuleInfo
from typhon.object_info_serializer import serialize_object_info
from typhon.transpiler_module import ModuleSource, ModuleFile, Transpiler


class TestTranspiler:
    @staticmethod
    def transform(js_tree: js_ast.JSModule):
        transpiler = Transpiler(None)
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

        transpiler = Transpiler(source_2)
        transpiler.transpile()
        module_info_2 = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)

        transpiler = Transpiler(source_1, related_modules={'test': module_info_2})
        transpiler.transpile()

        assert list(transpiler.globals.keys()) == ['a']
        object_info = transpiler.globals['a']
        assert object_info.name == 'a'
        assert object_info.object_type == ID_VAR


class TestModuleTranspiler:
    def test_cache_directory(self):
        source = 'print(a)'
        with TemporaryDirectory() as temp_dir:
            module = ModuleSource(source, temp_dir)
            transpiler = Transpiler(source)
            transpiler.transpile()
            module_info = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)
            module.save_info(module_info)

            cache_directory = os.path.join(temp_dir, '.ty_cache')
            gitignore_file = os.path.join(cache_directory, '.gitignore')
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
                assert gitignore_content == '*'

    def test_save_module_info(self):
        source = 'a = 123'
        with TemporaryDirectory() as temp_dir:
            source_filename = os.path.join(temp_dir, 'a.py')
            module = ModuleFile(source_filename, temp_dir)

            transpiler = Transpiler(source)
            transpiler.transpile()
            module_info = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)
            module.save_info(module_info)

            cache_directory = os.path.join(temp_dir, '.ty_cache')
            info_file = os.path.join(cache_directory, 'a.json')
            with open(info_file, 'r') as f:
                info_json_data = f.read()

        info_data = json.loads(info_json_data)
        expected = {
            'updated': info_data['updated'],
            'objects': [
                serialize_object_info(object_info)
                for object_info in module_info.objects.values()
            ],
            'nodes': serialize_js_node(module_info.js_tree),
        }
        now = datetime.datetime.now()
        updated = datetime.datetime.fromisoformat(info_data['updated'])
        assert (now - updated).seconds == 0
        assert info_data == expected

    def test_load_info(self):
        source = 'a = 123'
        with TemporaryDirectory() as temp_dir:
            source_filename = os.path.join(temp_dir, 'a.py')
            module = ModuleFile(source_filename, temp_dir)

            transpiler = Transpiler(source)
            transpiler.transpile()
            module_info = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)
            module.save_info(module_info)

            loaded_module = ModuleFile(source_filename, temp_dir)
            loaded_module_info = loaded_module.load_info()

        assert loaded_module_info.objects == module_info.objects
        assert loaded_module_info.js_tree == module_info.js_tree
