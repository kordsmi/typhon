class ModulePath:
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

    def __eq__(self, other):
        return isinstance(other, ModulePath) and self.module_path == other.module_path
