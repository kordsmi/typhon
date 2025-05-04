from typing import Union, List


registry = {}


class ObjectInfoMeta(type):
    def __init__(self, name, *args) -> None:
        super().__init__(name, *args)
        registry[name] = self


class ObjectInfo(metaclass=ObjectInfoMeta):
    _fields = (
        'context_path',
        'object_class',
    )

    def __init__(self, context_path: List[str], object_class: List[str] = None):
        self.context_path = context_path or []
        self.object_class = object_class
        self.object_dict = {}

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        for field_name in self._fields:
            if getattr(self, field_name) != getattr(other, field_name):
                return False

        return self.object_dict == other.object_dict

    def __repr__(self):
        args = []
        for key in self._fields:
            value = getattr(self, key)
            if isinstance(value, str):
                value_str = f'"{value}"'
            else:
                value_str = str(value)
            args.append(f'{key}={value_str}')
        return f'{type(self).__name__}({", ".join(args)})'


class TypeObjectInfo(ObjectInfo):
    pass


class ModuleObjectInfo(ObjectInfo):
    _fields = ObjectInfo._fields + ('file', )

    def __init__(self, context_path: List[str], file: str):
        super().__init__(context_path)
        self.file = file


class FunctionObjectInfo(TypeObjectInfo):
    pass


class ConstantObjectInfo(ObjectInfo):
    _fields = ObjectInfo._fields + ('value',)

    def __init__(self, context_path: List[str], value: Union[str, int]):
        super().__init__(context_path)
        self.value = value


class ReferenceObjectInfo(ObjectInfo):
    _fields = ObjectInfo._fields + ('ref', )

    def __init__(self, context_path: List[str], reference: ObjectInfo):
            super().__init__(context_path)
            self.reference = reference

    @classmethod
    def deserialize(cls, root_object: ObjectInfo, context_path: List[str], ref: List[str]):
        from typhon.context import get_object
        ref_object = get_object(root_object, ref[:-1], ref[-1])
        return cls(context_path, ref_object)

    @property
    def ref(self):
        return self.reference.context_path
