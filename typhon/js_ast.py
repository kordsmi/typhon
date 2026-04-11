from typing import Union, Optional, List

registry = {}


class JSNodeMeta(type):

    def __init__(self, name, *args) -> None:
        super().__init__(name, *args)
        registry[name] = self


class JSNode(metaclass=JSNodeMeta):
    """Базовый класс для всех узлов"""
    _fields = ()

    def __init__(self, **kwargs):
        for field_name in kwargs:
            setattr(self, field_name, kwargs.get(field_name))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        for field_name in self._fields:
            if getattr(self, field_name) != getattr(other, field_name):
                return False

        return True

    def __repr__(self):
        args = []
        for field_name in self._fields:
            value = getattr(self, field_name)
            if type(value) == str:
                value = f"'{value}'"
            arg_expr = f'{field_name}={value}'
            args.append(arg_expr)
        args_str = ', '.join(args)
        return f'{self.__class__.__module__}.{self.__class__.__name__}({args_str})'

    def __str__(self):
        return repr(self)


class JSExpression(JSNode):
    pass


class JSStatement(JSNode):
    pass


class JSOperator(JSNode):
    pass


class JSCmpOp(JSNode):
    pass


class JSName(JSExpression):
    _fields = (
        'id',
    )

    __slots__ = ('id',)

    def __init__(self, id: str):
        super().__init__(id=id)


class JSConstant(JSExpression):
    _fields = (
        'value',
    )

    __slots__ = ('value',)

    def __init__(self, value: Union[str, int]):
        super().__init__(value=value)


class JSKeyWord(JSNode):
    _fields = (
        'arg',
        'value',
    )

    __slots__ = ('arg', 'value')

    def __init__(self, arg: str, value: JSExpression):
        super().__init__(arg=arg, value=value)


class JSCall(JSExpression):
    _fields = (
        'func',
        'args',
        'keywords',
    )

    __slots__ = ('func', 'args', 'keywords')

    def __init__(self, func: JSExpression, args: List[JSExpression] = None, keywords: List[JSKeyWord] = None):
        super().__init__(func=func, args=args, keywords=keywords or [])


class JSBinOp(JSExpression):
    _fields = (
        'left',
        'op',
        'right',
    )

    __slots__ = (
        'left',
        'right',
        'op',
    )

    def __init__(self, left: JSExpression, op: JSOperator, right: JSExpression):
        super().__init__(left=left, op=op, right=right)


class JSAssign(JSStatement):
    _fields = (
        'target',
        'value',
    )

    __slots__ = ('target', 'value')

    def __init__(self, target: JSExpression, value: JSExpression):
        super().__init__(target=target, value=value)


class JSCodeExpression(JSStatement):
    _fields = (
        'value',
    )

    __slots__ = ('value',)

    def __init__(self, value: Union[JSStatement, JSExpression]):
        super().__init__(value=value)


class JSAdd(JSOperator):
    pass


class JSArg(JSNode):
    _fields = (
        'arg',
    )

    __slots__ = ('arg',)

    def __init__(self, arg: str):
        super().__init__(arg=arg)


class JSArguments(JSNode):
    _fields = (
        'args',
        'defaults',
        'vararg',
        'kwonlyargs',
        'kw_defaults',
        'kwarg',
    )

    __slots__ = ('args', 'defaults', 'vararg', 'kwonlyargs', 'kw_defaults', 'kwarg')

    def __init__(self, args: List[JSArg] = None, defaults: List[JSExpression] = None, vararg: JSArg = None,
                 kwonlyargs: List[JSArg] = None, kw_defaults: List[JSExpression] = None, kwarg: JSArg = None):
        super().__init__(args=args, defaults=defaults, vararg=vararg,
                         kwonlyargs=kwonlyargs, kw_defaults=kw_defaults, kwarg=kwarg)


class JSFunctionDef(JSStatement):
    _fields = (
        'name',
        'args',
        'body',
    )

    __slots__ = ('name', 'args', 'body')

    def __init__(self, name: str, args: JSArguments, body: List[JSStatement]):
        super().__init__(name=name, args=args, body=body)


class JSReturn(JSStatement):
    _fields = (
        'value',
    )

    __slots__ = ('value',)

    def __init__(self, value: JSExpression):
        super().__init__(value=value)


class JSList(JSExpression):
    _fields = (
        'elts',
    )

    __slots__ = ('elts',)

    def __init__(self, elts: List[JSExpression]):
        super().__init__(elts=elts)


class JSDict(JSExpression):
    _fields = (
        'keys',
        'values',
    )

    __slots__ = ('keys', 'values')

    def __init__(self, keys: List[JSExpression], values: List[JSExpression]):
        super().__init__(keys=keys, values=values)


class JSWhile(JSStatement):
    _fields = (
        'test',
        'body',
        'orelse',
    )

    __slots__ = ('test', 'body', 'orelse')

    def __init__(self, test: JSExpression, body: List[JSStatement], orelse: List[JSStatement] = None):
        super().__init__(test=test, body=body, orelse=orelse)


class JSEq(JSCmpOp):
    pass


class JSCompare(JSExpression):
    _fields = (
        'left',
        'op',
        'right',
    )

    __slots__ = ('left', 'op' , 'right')

    def __init__(self, left: JSExpression, op: JSCmpOp, right: JSExpression):
        super().__init__(left=left, op=op, right=right)


class JSIf(JSStatement):
    _fields = (
        'test',
        'body',
        'orelse',
    )

    __slots__ = ('test', 'body', 'orelse')

    def __init__(self, test: JSExpression, body: List[JSStatement], orelse: List[JSStatement] = None):
        super().__init__(test=test, body=body, orelse=orelse)


class JSThrow(JSStatement):
    _fields = (
        'exc',
    )

    __slots__ = ('exc', )

    def __init__(self, exc: JSExpression):
        super().__init__(exc=exc)


class JSTry(JSStatement):
    _fields = (
        'body',
        'catch',
        'finalbody',
    )

    __slots__ = ('body', 'catch', 'finalbody')

    def __init__(self, body: List[JSStatement], catch: List[JSStatement], finalbody: List[JSStatement] = None):
        super().__init__(body=body, catch=catch, finalbody=finalbody)


class JSContinue(JSStatement):
    pass


class JSBreak(JSStatement):
    pass


class JSSubscript(JSExpression):
    _fields = (
        'value',
        'slice',
    )

    __slots__ = ('value', 'slice')

    def __init__(self, value: JSExpression, slice: JSExpression):
        super().__init__(value=value, slice=slice)


class JSDelete(JSStatement):
    _fields = (
        'target',
    )

    __slots__ = ('target',)

    def __init__(self, target: JSExpression):
        super().__init__(target=target)


class JSStatements(JSNode):
    _fields = (
        'statements',
    )

    __slots__ = ('statements',)

    def __init__(self, statements: List[JSStatement]):
        super().__init__(statements=statements)


class JSExport(JSNode):
    _fields = (
        'ids',
    )

    __slots__ = ('ids',)

    def __init__(self, ids: List[str]):
        super().__init__(ids=ids)


class JSModule(JSNode):
    _fields = (
        'body',
        'export',
    )

    __slots__ = ('body', 'export')

    def __init__(self, body: List[JSStatement], export: Optional[JSExport] = None):
        super().__init__(body=body, export=export)


class JSLet(JSNode):
    _fields = (
        'assign',
    )

    __slots__ = ('assign',)

    def __init__(self, assign: JSAssign):
        super().__init__(assign=assign)


class JSAlias(JSNode):
    _fields = (
        'name',
        'asname',
    )

    __slots__ = ('name', 'asname')

    def __init__(self, name: str, asname: str = None):
        super().__init__(name=name, asname=asname)


class JSImport(JSStatement):
    _fields = (
        'module',
        'names',
        'alias',
    )

    __slots__ = ('module', 'names', 'alias')

    def __init__(self, module: str, names: List[JSAlias] = None, alias: str = None):
        super().__init__(module=module, names=names, alias=alias)


class JSAttribute(JSExpression):
    _fields = (
        'value',
        'attr',
    )

    __slots__ = ('value', 'attr')

    def __init__(self, value: JSName, attr: str):
        super().__init__(value=value, attr=attr)


class JSClassDef(JSStatement):
    _fields = (
        'name',
        'body',
    )

    __slots__ = ('name', 'body')

    def __init__(self, name: str, body: list[JSStatement]):
        super().__init__(name=name, body=body)


class JSMethodDef(JSFunctionDef):
    pass


class JSNew(JSExpression):
    _fields = (
        'class_',
        'args',
        'keywords',
    )

    __slots__ = ('class_', 'args', 'keywords')

    def __init__(self, class_: JSExpression, args: List[JSExpression] = None, keywords: List[JSKeyWord] = None):
        super().__init__(class_=class_, args=args, keywords=keywords or [])


class JSNop(JSStatement):
    pass


def node_factory(class_name: str, fields: {}) -> JSNode:
    node_class = registry.get(class_name)
    return node_class(**fields)
