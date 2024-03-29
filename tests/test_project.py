import os.path
from tempfile import TemporaryDirectory

from tests.helpers import source_file
from typhon.object_info import ModuleObjectInfo
from typhon.project import Project


class TestProject:
    def test_transpile_source(self):
        py_str = 'print(1 + 2)'
        js_str = 'export {};\n\nprint(1 + 2);'

        project = Project()
        result = project.transpile_source(py_str)

        assert result == js_str

    def test_transpile_file(self):
        py_str = 'print(1 + 2)'
        js_str = 'export {};\n\nprint(1 + 2);'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(source_path=temp_dir_path)
            file_path = os.path.join(temp_dir_path, 'test.py')
            js_path = os.path.join(temp_dir_path, 'test.js')
            with open(file_path, 'w') as f:
                f.write(py_str)
            filename = project.transpile_file(file_path)
            with open(js_path, 'r') as f:
                js_code = f.read()

            assert filename == js_path

        assert js_code == js_str

    def test_import_graph_from_source(self):
        source_1 = 'import a\nprint("test")'
        source_2 = 'print("Hello!")'

        project = Project()
        with source_file('a.py', source_2):
            project.transpile_source(source_1)

        assert project.import_graph == {'__main__': ['a'], 'a': []}

    def test_import_graph_from_file(self):
        source_1 = 'import a\nprint("test")'
        source_2 = 'print("Hello!")'
        project = Project()

        with source_file('source.py', source_1), source_file('a.py', source_2):
            project.transpile_file('source.py')

        assert project.import_graph == {'__main__': ['a'], 'a': []}

    def test_get_sorted_modules_from_graph(self):
        graph = {
            '__main__': ['a', 'b', 'c', 'e'],
            'a': [],
            'b': ['c'],
            'c': ['d'],
            'e': ['a'],
        }
        project = Project()
        project.import_graph = graph

        modules = project.get_sorted_modules_from_graph()

        assert modules == ['a', 'd', 'c', 'b', 'e', '__main__']

    def test_transpile_importing_modules(self):
        source_1 = 'import test\nprint("test")'
        source_2 = 'print("Hello!")'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(source_path=temp_dir_path)
            source_file_2 = os.path.join(temp_dir_path, 'test.py')
            js_path = os.path.join(temp_dir_path, 'test.js')
            with source_file(source_file_2, source_2):
                result = project.transpile_source(source_1)
            with open(js_path, 'r') as f:
                js_code = f.read()

        assert result == "export {test};\n\nimport * as test from './test.js';\nprint('test');"
        assert js_code == "export {};\n\nprint('Hello!');"

    def test_transpile_importing_modules_from_file(self):
        source_1 = 'import test\nprint("test")'
        source_2 = 'print("Hello!")'

        with TemporaryDirectory() as temp_dir_path:
            project = Project(source_path=temp_dir_path)
            source_file_1 = os.path.join(temp_dir_path, 'main.py')
            source_file_2 = os.path.join(temp_dir_path, 'test.py')
            test_js_path = os.path.join(temp_dir_path, 'test.js')
            with source_file(source_file_1, source_1), source_file(source_file_2, source_2):
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

        project = Project(source_path=temp_dir)
        source_file_2 = os.path.join(temp_dir, 'test.py')
        source_file_3 = os.path.join(temp_dir, 'foo.py')
        with source_file(source_file_2, source_2), source_file(source_file_3, source_3):
            project.transpile_source(source_1)

        assert list(sorted(project.module_info_list.keys())) == ['__main__', 'foo', 'test']
        assert list(project.module_info_list['foo'].objects.object_dict.keys()) == ['__special__']
        assert list(project.module_info_list['test'].objects.object_dict.keys()) == ['__special__', 'foo']
