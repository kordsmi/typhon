from typing import Union, Optional

registry = {}


class JSNodeMeta(type):

    def __init__(self, name, *args) -> None:
        super().__init__(name, *args)
        registry[name] = self


class JSNode(metaclass=JSNodeMeta):
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

    def __init__(self, id: str):
        super().__init__(id=id)


class JSConstant(JSExpression):
    _fields = (
        'value',
    )

    def __init__(self, value: str | int):
        super().__init__(value=value)


class JSKeyWord(JSNode):
    _fields = (
        'arg',
        'value',
    )

    def __init__(self, arg: str, value: JSExpression):
        super().__init__(arg=arg, value=value)


class JSCall(JSExpression):
    _fields = (
        'func',
        'args',
        'keywords',
    )

    def __init__(self, func: JSExpression, args: [JSExpression] = None, keywords: [JSKeyWord] = None):
        super().__init__(func=func, args=args, keywords=keywords or [])


class JSBinOp(JSExpression):
    _fields = (
        'left',
        'op',
        'right',
    )

    def __init__(self, left: JSExpression, op: JSOperator, right: JSExpression):
        super().__init__(left=left, op=op, right=right)


class JSAssign(JSStatement):
    _fields = (
        'target',
        'value',
    )

    def __init__(self, target: JSExpression, value: JSExpression):
        super().__init__(target=target, value=value)


class JSCodeExpression(JSStatement):
    _fields = (
        'value',
    )

    def __init__(self, value: Union[JSStatement, JSExpression]):
        super().__init__(value=value)


class JSAdd(JSOperator):
    pass


class JSArg(JSNode):
    _fields = (
        'arg',
    )

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

    def __init__(self, args: [JSArg] = None, defaults: [JSExpression] = None, vararg: JSArg = None,
                 kwonlyargs: [JSArg] = None, kw_defaults: [JSExpression] = None, kwarg: JSArg = None):
        super().__init__(args=args, defaults=defaults, vararg=vararg,
                         kwonlyargs=kwonlyargs, kw_defaults=kw_defaults, kwarg=kwarg)


class JSFunctionDef(JSStatement):
    _fields = (
        'name',
        'args',
        'body',
    )

    def __init__(self, name: str, args: JSArguments, body: [JSStatement]):
        super().__init__(name=name, args=args, body=body)


class JSReturn(JSStatement):
    _fields = (
        'value',
    )

    def __init__(self, value: JSExpression):
        super().__init__(value=value)


class JSList(JSExpression):
    _fields = (
        'elts',
    )

    def __init__(self, elts: [JSExpression]):
        super().__init__(elts=elts)


class JSDict(JSExpression):
    _fields = (
        'keys',
        'values',
    )

    def __init__(self, keys: [JSExpression], values: [JSExpression]):
        super().__init__(keys=keys, values=values)


class JSWhile(JSStatement):
    _fields = (
        'test',
        'body',
        'orelse',
    )

    def __init__(self, test: JSExpression, body: [JSStatement], orelse: [JSStatement] = None):
        super().__init__(test=test, body=body, orelse=orelse)


class JSEq(JSCmpOp):
    pass


class JSCompare(JSExpression):
    _fields = (
        'left',
        'op',
        'right',
    )

    def __init__(self, left: JSExpression, op: JSCmpOp, right: JSExpression):
        super().__init__(left=left, op=op, right=right)


class JSIf(JSStatement):
    _fields = (
        'test',
        'body',
        'orelse',
    )

    def __init__(self, test: JSExpression, body: [JSStatement], orelse: [JSStatement] = None):
        super().__init__(test=test, body=body, orelse=orelse)


class JSThrow(JSStatement):
    _fields = (
        'exc',
    )

    def __init__(self, exc: JSExpression):
        super().__init__(exc=exc)


class JSTry(JSStatement):
    _fields = (
        'body',
        'catch',
        'finalbody',
    )

    def __init__(self, body: [JSStatement], catch: [JSStatement], finalbody: [JSStatement] = None):
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

    def __init__(self, value: JSExpression, slice: JSExpression):
        super().__init__(value=value, slice=slice)


class JSDelete(JSStatement):
    _fields = (
        'target',
    )

    def __init__(self, target: JSExpression):
        super().__init__(target=target)


class JSStatements(JSNode):
    _fields = (
        'statements',
    )

    def __init__(self, statements: [JSStatement]):
        super().__init__(statements=statements)


class JSExport(JSNode):
    _fields = (
        'ids',
    )

    def __init__(self, ids: [str]):
        super().__init__(ids=ids)


class JSModule(JSNode):
    _fields = (
        'body',
        'export',
    )

    def __init__(self, body: [JSStatement], export: Optional[JSExport] = None):
        super().__init__(body=body, export=export)


class JSLet(JSNode):
    _fields = (
        'assign',
    )

    def __init__(self, assign: JSAssign):
        super().__init__(assign=assign)


class JSAlias(JSNode):
    _fields = (
        'name',
        'asname',
    )

    def __init__(self, name: str, asname: str = None):
        super().__init__(name=name, asname=asname)


class JSImport(JSStatement):
    _fields = (
        'module',
        'names',
        'alias',
    )

    def __init__(self, module: str, names: [JSAlias] = None, alias: str = None):
        super().__init__(module=module, names=names, alias=alias)


class JSAttribute(JSExpression):
    _fields = (
        'value',
        'attr',
    )

    def __init__(self, value: JSName, attr: str):
        super().__init__(value=value, attr=attr)


class JSClassDef(JSStatement):
    _fields = (
        'name',
        'body',
    )

    def __init__(self, name: str, body: [JSStatement]):
        super().__init__(name=name, body=body)


class JSMethodDef(JSFunctionDef):
    pass


class JSNew(JSExpression):
    _fields = (
        'class_',
        'args',
        'keywords',
    )

    def __init__(self, class_: JSExpression, args: [JSExpression] = None, keywords: [JSKeyWord] = None):
        super().__init__(class_=class_, args=args, keywords=keywords or [])


class JSNop(JSNode):
    pass


def node_factory(class_name: str, fields: {}) -> JSNode:
    node_class = registry.get(class_name)
    return node_class(**fields)
