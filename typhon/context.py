from typing import List, Optional

from typhon.object_info import ObjectInfo, ReferenceObjectInfo


class Context:
    def __init__(self, module_objects: dict = None):
        self.module_objects = module_objects or {}


class ContextPathError(Exception):
    pass


def get_context_object(root_object: ObjectInfo, context_path: List[str]) -> ObjectInfo:
    result = root_object
    for path_item in context_path:
        if path_item not in result.object_dict:
            raise ContextPathError(context_path)
        result = result.object_dict[path_item]

    return result


def get_object(
        from_object: ObjectInfo,
        context_path: List[str],
        object_name: Optional[str] = None
) -> Optional[ObjectInfo]:
    result = None
    current_object: ObjectInfo = from_object

    def search_and_add_result(obj: ObjectInfo):
        nonlocal result
        if object_name is None:
            return

        if object_name in obj.object_dict:
            result = obj.object_dict[object_name]

    search_and_add_result(current_object)

    for path_item in context_path:
        if path_item not in current_object.object_dict:
            raise ContextPathError(context_path)
        current_object = current_object.object_dict[path_item]
        if isinstance(current_object, ReferenceObjectInfo):
            current_object = current_object.reference
        search_and_add_result(current_object)

    if object_name is None:
        result = current_object

    if result and isinstance(result, ReferenceObjectInfo):
        return result.reference

    return result
