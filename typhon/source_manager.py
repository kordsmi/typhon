import os.path
from typhon.types import ModulePath


class SourceManager:
    """Класс `SourceManager` управляет путями к исходным файлам:
        - Определение путей к пакетам
        - Проверка, является ли модуль пакетом (наличие `__init__.py`)
    """
    def __init__(self, project_path: str = None):
        self.project_path = project_path or '.'

    def get_package_path(self, package: str):
        return os.path.join(self.project_path, package)

    def is_package(self, module: ModulePath):
        full_path = os.path.join(self.project_path, *module.module_path)
        if not os.path.isdir(full_path):
            return False
        init_file = os.path.join(full_path, '__init__.py')
        return os.path.exists(init_file)
