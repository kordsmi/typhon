from typhon.object_info import ObjectInfo, FunctionObjectInfo, ReferenceObjectInfo
from typhon.object_info_serializer import serialize_object_info, deserialize_object_info


class TestSerializeDeserializeObjectInfo:
    def test_base(self):
        object_info = ObjectInfo(['a'])

        result = serialize_object_info(object_info)

        expected = {
            'class': 'ObjectInfo',
            'object_class': None,
            'object_dict': {},
            'context_path': ['a'],
        }
        assert result == expected

        deserialized_object = deserialize_object_info(result)
        assert deserialized_object == object_info

    def test_serialize_context_path(self):
        object_info = FunctionObjectInfo(['a', 'test'])

        result = serialize_object_info(object_info)

        expected = {
            'class': 'FunctionObjectInfo',
            'context_path': ['a', 'test'],
            'object_class': None,
            'object_dict': {},
        }
        assert result == expected

        deserialized_object = deserialize_object_info(result)
        assert deserialized_object == object_info

    def test_reference(self):
        root_object = ObjectInfo(None)
        var_1 = ObjectInfo(['var_1'])
        var_2 = ReferenceObjectInfo(['test', 'var_2'], ['var_1'])
        test_func = FunctionObjectInfo(['test'])
        test_func.object_dict = {
            'var_2': var_2,
        }
        root_object.object_dict = {
            'var_1': var_1,
            'test': test_func,
        }

        result = serialize_object_info(root_object)

        expected = {
            'class': 'ObjectInfo',
            'context_path': [],
            'object_class': None,
            'object_dict': {
                'var_1': {
                    'class': 'ObjectInfo',
                    'context_path': ['var_1'],
                    'object_class': None,
                    'object_dict': {},
                },
                'test': {
                    'class': 'FunctionObjectInfo',
                    'context_path': ['test'],
                    'object_class': None,
                    'object_dict': {
                        'var_2': {
                            'class': 'ReferenceObjectInfo',
                            'context_path': ['test', 'var_2'],
                            'object_class': None,
                            'ref': ['var_1'],
                            'object_dict': {},
                        }
                    },
                }
            }
        }
        assert result == expected

        deserialized_object = deserialize_object_info(result)
        assert deserialized_object == root_object
