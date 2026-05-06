import ast
from typing import Any, Optional


OT_MODULE = 'module'
OT_REFERENCE = 'reference'
OT_FUNCTION = 'function'
OT_ARGUMENT = 'argument'
OT_CLASS = 'class'


class ObjectInfo:
    """Представляет базовую информацию об объекте."""
    def __init__(self, object_type: str = '', object_value: Any = None):
        self.objects: dict[str, ObjectInfo] = {}
        self.object_type = object_type
        self.object_value = object_value

    def __eq__(self, other: 'ObjectInfo') -> bool:
        """Проверяет равенство двух экземпляров ObjectInfo."""
        if type(self) != type(other):
            return False
        return (
            self.object_type == other.object_type
            and self.object_value == other.object_value
            and self.objects == other.objects
        )

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта."""
        return f'<object {self.object_type}>'

    def add_object(self, object_name: str, object_info: 'ObjectInfo') -> None:
        """Добавляет объект в коллекцию."""
        self.objects[object_name] = object_info


class ObjectConstant(ObjectInfo):
    """Объект-константа."""
    def __init__(self, object_value: Any):
        object_type = type(object_value).__name__
        super().__init__(object_type, object_value=object_value)

    def __repr__(self) -> str:
        """Возвращает строку, представляющую объект-константу."""
        return str(self.object_value)


class ObjectReference(ObjectInfo):
    """Ссылающийся объект."""
    def __init__(self, reference: str):
        super().__init__(OT_REFERENCE, reference)


class ObjectFunction(ObjectInfo):
    """Функциональный объект."""
    def __init__(self, function_name: str):
        super().__init__(OT_FUNCTION, function_name)
        self.locals = ObjectInfo('', None)

    def __eq__(self, other: 'ObjectFunction') -> bool:
        """Проверяет эквивалентность функций."""
        if not super().__eq__(other):
            return False
        return self.locals == other.locals

    def __repr__(self) -> str:
        """Возвращает строковое представление функционального объекта."""
        return f'<function {self.object_value}>'


class ObjectArgument(ObjectInfo):
    """Аргументный объект."""
    def __init__(self):
        super().__init__(OT_ARGUMENT, None)


class ObjectModule(ObjectInfo):
    """Модульный объект."""
    def __init__(self, module_name: str):
        super().__init__(OT_MODULE, module_name)


class ObjectClass(ObjectInfo):
    """Классовый объект."""
    def __init__(self, name: str):
        super().__init__(OT_CLASS, name)

    def __repr__(self) -> str:
        """Возвращает строковое представление объект-класса."""
        return f'<class {self.object_value}>'


def dump_object(object_info: ObjectInfo) -> dict:
    """Выполняет сериализацию объекта."""
    if object_info is None:
        return {}

    result = {
        'type': object_info.object_type,
        'value': object_info.object_value
    }

    objects_info = {}
    for obj_name, obj_info in object_info.objects.items():
        objects_info[obj_name] = dump_object(obj_info)

    result['objects'] = objects_info

    if isinstance(object_info, ObjectFunction):
        result['locals'] = dump_object(object_info.locals)

    return result


class ObjectCollector(ast.NodeVisitor):
    """Посещает узлы AST и собирает информацию об объектах."""
    def __init__(self, object_info: ObjectInfo = None):
        super().__init__()
        if object_info is None:
            object_info = ObjectModule('__main__')
        self.object_info = object_info

    def visit_body(self, body: list[ast.stmt]) -> None:
        """Обходит тело программы."""
        for stmt in body:
            self.visit(stmt)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Обрабатывает операторы присваивания."""
        targets = node.targets
        for target in targets:
            self._add_object_info(target, node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Создает объект-функцию и добавляет локальные переменные."""
        object_function = ObjectFunction(node.name)
        self.object_info.add_object(node.name, object_function)
        object_function.locals = ObjectInfo('', None)

        arguments = node.args
        for arg in arguments.args:
            object_function.locals.add_object(arg.arg, ObjectArgument())
        for kwarg in arguments.kwonlyargs:
            object_function.locals.add_object(kwarg.arg, ObjectArgument())

        body_collector = ObjectCollector(object_function.locals)
        body_collector.visit_body(node.body)

    def visit_Import(self, node: ast.Import) -> None:
        """Добавляет модули в коллекцию."""
        for alias in node.names:
            module_name = alias.name
            name = alias.asname or module_name
            self.object_info.add_object(name, ObjectModule(module_name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Добавляет ссылки на объекты импорта."""
        module_name = node.module
        for alias in node.names:
            variable_name = alias.name
            variable_alias = alias.asname or variable_name
            reference = f'{module_name}.{variable_name}'
            self.object_info.add_object(variable_alias, ObjectReference(reference))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Создает объект-класс и собирает информацию о теле класса."""
        object_class = ObjectClass(node.name)
        self.object_info.add_object(node.name, object_class)

        class_collector = ObjectCollector(object_class)
        class_collector.visit_body(node.body)

    def _add_object_info(self, target: ast.expr, value: ast.expr) -> None:
        """Добавляет объект в коллекцию."""
        if isinstance(target, ast.Name):
            object_value = self._get_object_value(value)
            self.object_info.add_object(target.id, object_value)
        elif isinstance(target, ast.Tuple):
            self._assign_to_tuple(target, value)

    def _get_object_value(self, value: ast.expr) -> Optional[ObjectInfo]:
        """Получает объект-значение."""
        if isinstance(value, ast.Constant):
            object_value = ObjectConstant(value.value)
        elif isinstance(value, ast.Name):
            object_value = ObjectReference(value.id)
        else:
            object_value = None
        return object_value

    def _assign_to_tuple(self, targets: ast.Tuple, values: ast.expr) -> None:
        """Присваивает значения элементам кортежа."""
        if isinstance(values, ast.Tuple):
            for target, value in zip(targets.elts, values.elts):
                self._add_object_info(target, value)
