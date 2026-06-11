import itertools


class ModulePath:
    """Класс `ModulePath` представляет путь к модулю:
    - Хранит путь в виде кортежа
    - Предоставляет свойства для имени, пакета и компонентов пакета
    """
    def __init__(self, *items):
        self.module_path = tuple(items)

    @property
    def name(self):
        return self.module_path[-1]

    @property
    def package(self):
        return '.'.join(self.packages)

    @property
    def packages(self):
        if len(self.module_path) == 1:
            return []
        return self.module_path[:-1]

    @property
    def full_path(self):
        return '.'.join(self.module_path)

    def __eq__(self, other):
        return isinstance(other, ModulePath) and self.module_path == other.module_path

    def __add__(self, other: list) -> 'ModulePath':
        if not isinstance(other, list):
            raise TypeError(f'Cannot add {type(other)} to a module path')

        return ModulePath(*itertools.chain(self.module_path, other))
