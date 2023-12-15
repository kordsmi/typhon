import datetime
import json
import os.path
from tempfile import TemporaryDirectory

from typhon.js_node_serializer import serialize_js_node
from typhon.module_info import ModuleInfo
from typhon.module_tools import Module
from typhon.object_info_serializer import serialize_object_info
from typhon.module_transpiler import ModuleTranspiler


class TestModule:
    def test_cache_directory(self):
        source = 'print(a)'
        with TemporaryDirectory() as temp_dir:
            module = Module(source_path=temp_dir)
            transpiler = ModuleTranspiler(source)
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
            module = Module('a', source_path=temp_dir)

            transpiler = ModuleTranspiler(source)
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
            module = Module('a', source_path=temp_dir)

            transpiler = ModuleTranspiler(source)
            transpiler.transpile()
            module_info = ModuleInfo(objects=transpiler.globals, js_tree=transpiler.js_tree)
            module.save_info(module_info)

            loaded_module = Module('a', source_path=temp_dir)
            loaded_module_info = loaded_module.load_info()

        assert loaded_module_info.objects == module_info.objects
        assert loaded_module_info.js_tree == module_info.js_tree
