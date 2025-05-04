import datetime
import json
import os.path
from tempfile import TemporaryDirectory

import pytest

from tests.helpers import make_package, source_file
from typhon.object_info import ObjectInfo
from typhon.js_node_serializer import serialize_js_node
from typhon.module_info import ModuleInfo
from typhon.module import Module
from typhon.source_manager import SourceManager
from typhon.types import ModulePath
from typhon.object_info_serializer import serialize_object_info
from typhon.module_transpiler import ModuleTranspiler


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir


class TestModule:
    def test_cache_directory(self, temp_dir):
        source = 'print(a)'
        module = Module(source_manager=SourceManager(temp_dir))
        root_object = ObjectInfo([])
        transpiler = ModuleTranspiler(source, root_object, 'test')
        transpiler.transpile()
        module_info = ModuleInfo(objects=root_object, js_tree=transpiler.js_tree)
        module.save_info(module_info)

        cache_directory = os.path.join(temp_dir, '.ty_cache')
        gitignore_file = os.path.join(cache_directory, '.gitignore')
        with open(gitignore_file, 'r') as f:
            gitignore_content = f.read()
            assert gitignore_content == '*'

    def test_save_module_info(self, temp_dir):
        source = 'a = 123'
        module = Module(ModulePath('', 'a'), SourceManager(temp_dir))

        root_object = ObjectInfo(None)
        transpiler = ModuleTranspiler(source, root_object, 'test')
        transpiler.transpile()
        module_info = ModuleInfo(objects=root_object, js_tree=transpiler.js_tree)
        module.save_info(module_info)

        cache_directory = os.path.join(temp_dir, '.ty_cache')
        info_file = os.path.join(cache_directory, 'a.json')
        with open(info_file, 'r') as f:
            info_json_data = f.read()

        info_data = json.loads(info_json_data)
        expected = {
            'updated': info_data['updated'],
            'objects': serialize_object_info(module_info.objects),
            'nodes': serialize_js_node(module_info.js_tree),
        }
        now = datetime.datetime.now()
        updated = datetime.datetime.fromisoformat(info_data['updated'])
        assert (now - updated).seconds == 0
        assert info_data == expected

    def test_load_info(self, temp_dir):
        source = 'a = 123'
        module = Module(ModulePath('', 'a'), SourceManager(temp_dir))

        root_object = ObjectInfo(None)
        transpiler = ModuleTranspiler(source, root_object, 'test')
        transpiler.transpile()
        module_info = ModuleInfo(objects=root_object, js_tree=transpiler.js_tree)
        module.save_info(module_info)

        loaded_module = Module(ModulePath('', 'a'), SourceManager(temp_dir))
        loaded_module_info = loaded_module.load_info(root_object)

        assert loaded_module_info.objects == module_info.objects
        assert loaded_module_info.js_tree == module_info.js_tree

    def test_module_path(self, temp_dir):
        module = Module(ModulePath('', 'a'), SourceManager(temp_dir))
        assert module.source_path == os.path.join(temp_dir, '')

    def test_get_source(self, temp_dir):
        module = Module(ModulePath('a', 'b'), SourceManager(temp_dir))
        with make_package('a', temp_dir) as package_path, source_file('b.py', 'test file', package_path):
            source = module.get_source()
        assert source == 'test file'
