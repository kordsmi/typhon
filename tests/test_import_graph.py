import pytest

from tests.helpers import source_file
from typhon.exceptions import TyphonImportError
from typhon.import_graph import ImportGraph
from typhon.source_manager import SourceManager
from typhon.types import ModulePath


class TestImportGraph:
    def test_graph__no_imports(self):
        source = 'print("test")'
        import_graph = ImportGraph(source, SourceManager())
        assert import_graph.get_graph() == {ModulePath('', '__main__'): []}

    def test_graph__with_import(self, temp_dir):
        source_1 = 'import a\nprint("test")'
        source_2 = 'print("Hello!")'

        import_graph = ImportGraph(source_1, SourceManager(temp_dir))
        with source_file('a.py', source_2, temp_dir):
            graph = import_graph.get_graph()

        assert graph == {ModulePath('', '__main__'): [ModulePath('', 'a')], ModulePath('', 'a'): []}

    def test_graph__with_inner_import(self):
        source_1 = 'while True:\n    import a'
        import_graph = ImportGraph(source_1, SourceManager())

        graph = import_graph.get_graph()

        assert graph == {ModulePath('', '__main__'): []}

    def test_graph__loop(self, temp_dir):
        source_1 = 'import a'
        source_2 = 'import b'
        import_graph = ImportGraph(source_1, SourceManager(temp_dir))

        with pytest.raises(TyphonImportError) as exc,\
                source_file('a.py', source_2, temp_dir), source_file('b.py', source_1, temp_dir):
            import_graph.get_graph()
        assert str(exc.value) == 'There is circular imports detected: .__main__ -> .a -> .b -> .a'
