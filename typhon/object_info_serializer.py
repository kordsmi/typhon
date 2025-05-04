import copy
from typing import List

from typhon.context import get_context_object
from typhon.object_info import ObjectInfo, registry


def serialize_object_info(root_object: ObjectInfo, context_path: List[str] = None) -> dict:
    context_path = context_path or []
    object_info = get_context_object(root_object, context_path)

    data = {
        'class': object_info.__class__.__name__,
    }

    for field_key in object_info._fields:
        if field_key == 'node':
            continue
        data[field_key] = getattr(object_info, field_key)

    data['object_dict'] = {}
    for key in object_info.object_dict:
        data['object_dict'][key] = serialize_object_info(root_object, context_path + [key])

    return data


def deserialize_object_info(data: dict, root_object: ObjectInfo = None) -> ObjectInfo:
    data = copy.copy(data)
    class_name = data.pop('class')
    cls = registry[class_name]
    object_class = data.pop('object_class')
    object_dict_data = data.pop('object_dict')

    if hasattr(cls, 'deserialize'):
        object_info = cls.deserialize(root_object, **data)
    else:
        object_info: ObjectInfo = cls(**data)

    if root_object is None:
        root_object = object_info

    object_info.object_class = object_class

    object_dict = object_info.object_dict
    for key, data in object_dict_data.items():
        object_dict[key] = deserialize_object_info(data, root_object)

    return object_info
