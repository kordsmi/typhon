import ast
import os.path
from tempfile import TemporaryDirectory
from unittest import mock

from tests.helpers import source_file
from typhon.import_graph import ImportGraph
from typhon.object_collector import ObjectModule, ObjectCollector, ObjectConstant, ObjectClass
from typhon.types import ModulePath
from typhon.project import Project


class TestProject:
    def test_transpile_source(self, temp_dir):
        py_str = 'print(1 + 2)'
        js_str = 'export {};\n\nprint(1 + 2);'

        project = Project(temp_dir)
        result = project.transpile_source(py_str)

        assert result == js_str

    def test_transpile_file(self):
        py_str = 'print(1 + 2)'
        js_str = 'export {};\n\nprint(1 + 2);'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(temp_dir_path)
            file_path = os.path.join(temp_dir_path, 'test.py')
            js_path = os.path.join(temp_dir_path, 'test.js')
            with open(file_path, 'w') as f:
                f.write(py_str)
            filename = project.transpile_file(file_path)
            with open(js_path, 'r') as f:
                js_code = f.read()

            assert filename == js_path

        assert js_code == js_str

    def test_get_sorted_modules_from_graph(self, temp_dir):
        graph = {
            ('__main__',): [
                ModulePath('a'),
                ModulePath('b'),
                ModulePath('c'),
                ModulePath('e'),
            ],
            ('a',): [],
            ('b',): [ModulePath('c')],
            ('c',): [ModulePath('d')],
            ('e',): [ModulePath('a')],
        }
        project = Project(temp_dir)

        with mock.patch.object(ImportGraph, 'get_graph') as get_graph_mock:
            get_graph_mock.return_value = graph
            project.get_sorted_modules_from_source('', '__main__')

        assert project.modules == [
            ModulePath('a'),
            ModulePath('d'),
            ModulePath('c'),
            ModulePath('b'),
            ModulePath('e'),
            ModulePath('__main__'),
        ]

    def test_transpile_importing_modules(self):
        source_1 = 'import test\nprint("test")'
        source_2 = 'print("Hello!")'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(temp_dir_path)
            js_path = os.path.join(temp_dir_path, 'test.js')
            with source_file('test.py', source_2, temp_dir_path):
                result = project.transpile_source(source_1)
            with open(js_path, 'r') as f:
                js_code = f.read()

        assert result == "export {test};\n\nimport * as test from './test.js';\nprint('test');"
        assert js_code == "export {};\n\nprint('Hello!');"

    def test_transpile_importing_modules_from_file(self):
        source_1 = 'import test\nprint("test")'
        source_2 = 'print("Hello!")'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(temp_dir_path)
            source_file_1 = 'main.py'
            source_file_2 = 'test.py'
            test_js_path = os.path.join(temp_dir_path, 'test.js')
            with (
                source_file(source_file_1, source_1, temp_dir_path),
                source_file(source_file_2, source_2, temp_dir_path)
            ):
                main_js_path = project.transpile_file(source_file_1)
            with open(main_js_path, 'r') as f:
                main_js_code = f.read()
            with open(test_js_path, 'r') as f:
                test_js_code = f.read()

        assert main_js_path == os.path.join(temp_dir_path, 'main.js')
        assert main_js_code == "export {test};\n\nimport * as test from './test.js';\nprint('test');"
        assert test_js_code == "export {};\n\nprint('Hello!');"

    def test_collect_module_info_on_transpile_importing_modules(self, temp_dir):
        source_1 = 'import test\nprint("test")'
        source_2 = 'import foo\nprint("Hello!")'
        source_3 = 'print("Foo!")'

        project = Project(temp_dir)
        with source_file('test.py', source_2, temp_dir), source_file('foo.py', source_3, temp_dir):
            project.transpile_source(source_1)

        assert list(sorted(project.module_info_list.keys())) == ['__main__', 'foo', 'test']
        assert list(project.module_info_list['foo'].objects.objects.keys()) == ['__special__']
        assert set(project.module_info_list['test'].objects.objects.keys()) == {'__special__', 'foo'}

    @staticmethod
    def _collect_objects(source: str, module_name: str) -> ObjectModule:
        py_tree = ast.parse(source)
        module_object = ObjectModule(ModulePath(module_name))

        collector = ObjectCollector(module_object)
        collector.visit(py_tree)

        return module_object

    def test_import_object_to_globals(self, temp_dir):
        # Константы импортируются как константы
        source_1 = 'from test import a'
        source_2 = 'a = 123'

        module_object1 = self._collect_objects(source_1, '__main__')
        module_object2 = self._collect_objects(source_2, 'test')

        project = Project()
        project.root_object.objects['__main__'] = module_object1
        project.root_object.objects['test'] = module_object2
        project.replace_references_to_objects(module_object1)

        assert list(module_object1.objects.keys()) == ['a']
        object_info = module_object1.objects['a']
        assert isinstance(object_info, ObjectConstant)
        assert object_info.object_value == 123

    def test_import_class_to_globals(self, temp_dir):
        # Всё что не относится к константам, импортируются как ссылки
        source_1 = 'from test import A'
        source_2 = 'class A: pass'

        module_object1 = self._collect_objects(source_1, '__main__')
        module_object2 = self._collect_objects(source_2, 'test')

        project = Project()
        project.root_object.objects['__main__'] = module_object1
        project.root_object.objects['test'] = module_object2
        project.replace_references_to_objects(module_object1)

        assert list(module_object1.objects.keys()) == ['A']
        object_info = module_object1.objects['A']
        assert isinstance(object_info, ObjectClass)
        assert object_info.object_value == 'A'
