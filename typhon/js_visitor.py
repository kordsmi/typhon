from typing import Optional, List, Callable, Iterable, Tuple

from typhon import js_ast


def iter_fields(node: js_ast.JSNode) -> Iterable[Tuple[str, js_ast.JSNode]]:
    """
    Возвращает итератор по парам (имя_поля, значение) для каждого поля узла,
    определённого в `node._fields`. Если поле отсутствует, оно пропускается.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


class JSNodeVisitor:
    """
    Базовый класс для обхода узлов дерева синтаксического разбора (AST).
    Этот класс последовательно посещает все узлы AST и вызывает соответствующую
    функцию-обработчик для каждого из них. Метод-обработчик может вернуть значение,
    которое будет возвращено методом `visit`.

    Этот класс предназначен для наследования — производные классы должны добавлять
    свои собственные методы-посетители.

    По умолчанию имя метода-обработчика формируется как ``'visit_'`` + имя класса узла.
    Например, для узла `JSTry` будет вызван метод `visit_JSTry`.
    Это поведение можно изменить, переопределив метод `visit`.
    Если для узла не найден подходящий метод-обработчик (возвращается `None`),
    вместо него вызывается метод `generic_visit`.

    Не используйте `JSNodeVisitor`, если вы хотите вносить изменения в узлы во время обхода.
    Для модификации дерева существует специальный класс `JSNodeTransformer`.
    """

    def visit(self, node: js_ast.JSNode) -> Optional[js_ast.JSNode | List[js_ast.JSNode]]:
        """Посещение узла."""
        method = 'visit_' + node.__class__.__name__
        visitor: Callable[[js_ast.JSNode], None] = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: js_ast.JSNode):
        """Вызывается по умолчанию, если для узла не определён специализированный метод-посетитель.

        Метод рекурсивно посещает все поля узла, которые являются узлами AST или списками узлов,
        и применяет к ним обход с помощью `visit`. Это позволяет автоматически проходить
        по всей структуре дерева без необходимости явно прописывать обработку каждого типа узлов.

        Например, если узел содержит список дочерних узлов (например, тело функции),
        `generic_visit` рекурсивно посетит каждый из них.

        Переопределите этот метод, если нужно изменить поведение обхода по умолчанию.
        """
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, js_ast.JSNode):
                        self.visit(item)
            elif isinstance(value, js_ast.JSNode):
                self.visit(value)


class JSNodeTransformer(JSNodeVisitor):
    """
    Подкласс класса :class:`JSNodeVisitor`, который обходит дерево абстрактного синтаксического дерева (AST)
    и позволяет модифицировать его узлы.

    Класс `JSNodeTransformer` проходит по AST и использует возвращаемое значение методов-посетителей,
    чтобы заменить или удалить старый узел. Если метод-посетитель возвращает ``None``,
    узел будет удалён из дерева; в противном случае он заменяется на возвращённое значение.
    Возвращаемым значением может быть тот же самый узел — тогда замена не происходит.

    Пример трансформера, который заменяет все обращения к переменным
     (``x``) на доступ через объект ``data['x']``::

       class RewriteName(JSNodeTransformer):

           def visit_Name(self, node):
               return Subscript(
                   value=Name(id='data', ctx=Load()),
                   slice=Constant(value=node.id),
                   ctx=node.ctx
               )

    Имейте в виду, что если узел содержит дочерние узлы, вы должны либо обработать их самостоятельно,
    либо сначала вызвать метод :meth:`generic_visit`.

    Для узлов, входящих в состав списка инструкций (все узлы-выражения и операторы),
    метод-посетитель может также вернуть список узлов вместо одного узла.

    Обычно трансформер используется следующим образом::

       node = YourTransformer().visit(node)
    """

    def generic_visit(self, node: js_ast.JSNode) -> Optional[js_ast.JSNode]:
        for field, old_value in iter_fields(node):
            if isinstance(old_value, list):
                new_values: List = []
                for value in old_value:
                    if isinstance(value, js_ast.JSNode):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, js_ast.JSNode):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, js_ast.JSNode):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node
