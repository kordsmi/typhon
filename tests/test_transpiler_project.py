import os.path
from tempfile import TemporaryDirectory

from typhon.transpiler_project import Project


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
        project = Project()

        with TemporaryDirectory() as temp_dir_path:
            file_path = os.path.join(temp_dir_path, 'test.py')
            js_path = os.path.join(temp_dir_path, 'test.js')
            with open(file_path, 'w') as f:
                f.write(py_str)
            filename = project.transpile_file(file_path)
            with open(js_path, 'r') as f:
                js_code = f.read()

            assert filename == js_path

        assert js_code == js_str
