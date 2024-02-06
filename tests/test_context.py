from typhon.context import get_context_object
from typhon.object_info import ObjectInfo, ModuleObjectInfo


class TestGetContextVars:
    def setup_method(self):
        self.obj = ObjectInfo([])
        self.module_info = ModuleObjectInfo(['test'], file='test.py')
        self.obj.object_dict['test'] = self.module_info

    def test_simple(self):
        context_vars = get_context_object(self.obj, ['test'])
        assert context_vars == self.module_info

    def test_complex_path(self):
        self.module_info.object_dict['foo'] = ObjectInfo('test')
        context_vars = get_context_object(self.obj, ['test', 'foo'])
        assert context_vars == self.module_info.object_dict['foo']
