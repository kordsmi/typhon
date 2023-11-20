import os.path
from contextlib import contextmanager

import pytest

from typhon.exceptions import TyphonImportError
from typhon.import_graph import ImportGraph


@contextmanager
def source_file(file_name, source=''):
    try:
        with open(file_name, 'w') as f:
            f.write(source)
        yield
    finally:
        os.unlink(file_name)


class TestImportGraph:
    def test_graph__no_imports(self):
        source = 'print("test")'
        import_graph = ImportGraph(source)
        assert import_graph.get_graph() == {'__main__': []}

    def test_graph__with_import(self):
        source_1 = 'import a\nprint("test")'
        source_2 = 'print("Hello!")'

        import_graph = ImportGraph(source_1)
        with source_file('a.py', source_2):
            graph = import_graph.get_graph()

        assert graph == {'__main__': ['a'], 'a': []}

    def test_graph__with_inner_import(self):
        source_1 = 'while True:\n    import a'
        import_graph = ImportGraph(source_1)

        graph = import_graph.get_graph()

        assert graph == {'__main__': []}

    def test_graph__loop(self):
        source_1 = 'import a'
        source_2 = 'import b'
        import_graph = ImportGraph(source_1)

        with pytest.raises(TyphonImportError) as exc,\
                source_file('a.py', source_2), source_file('b.py', source_1):
            import_graph.get_graph()
        assert str(exc.value) == 'There is circular imports detected: __main__ -> a -> b -> a'
