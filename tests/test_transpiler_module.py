import copy
import datetime
import json
import os.path
import zoneinfo
from tempfile import TemporaryDirectory

from tests.helpers import source_file
from typhon import js_ast
from typhon.transpiler_module import ModuleTranspiler, ModuleSource, ModuleFile


class TestModuleTranspiler:
    @staticmethod
    def transform(js_tree: js_ast.JSModule):
        module_transpiler = ModuleTranspiler(None)
        module_transpiler.js_tree = js_tree
        module_transpiler.transform()
        return module_transpiler.js_tree

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

    def test_cache_directory(self):
        source = 'print(a)'
        with TemporaryDirectory() as temp_dir:
            module_transpiler = ModuleSource(source, temp_dir)
            module_transpiler.transpile()

            cache_directory = os.path.join(temp_dir, '.ty_cache')
            gitignore_file = os.path.join(cache_directory, '.gitignore')
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
                assert gitignore_content == '*'

    def test_save_module_info(self):
        source = 'a = 123'
        with TemporaryDirectory() as temp_dir:
            source_filename = os.path.join(temp_dir, 'a.py')
            with source_file(source_filename, source):
                module_transpiler = ModuleFile(source_filename, temp_dir)
                module_transpiler.transpile()

                cache_directory = os.path.join(temp_dir, '.ty_cache')
                info_file = os.path.join(cache_directory, 'a.json')
                with open(info_file, 'r') as f:
                    info_json_data = f.read()

        info_data = json.loads(info_json_data)
        expected = {
            'updated': info_data['updated'],
            'objects': [
                {
                    'id': 'a',
                    'module': 'a',
                    'type': 'object',
                    'features': [],
                }
            ]
        }
        now = datetime.datetime.now()
        updated = datetime.datetime.fromisoformat(info_data['updated'])
        assert (now - updated).seconds == 0
        assert info_data == expected
