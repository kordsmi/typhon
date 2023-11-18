from typhon.transpiler import Transpiler
from typhon.transpiler_module import Module


class Project:
    def transpile_source(self, source: str) -> str:
        """
        Транспиляция переданного исходного кода. В ответе возвращается js-код.
        """
        transpiler = Transpiler(source)
        return transpiler.transpile()

    def transpile_file(self, source_file_path: str) -> str:
        """
        Транспиляция файла с исходным кодом. В ответ возвращается путь к оттранспилированному js-файлу.
        """
        module = Module(source_file_path)
        return module.transpile()
