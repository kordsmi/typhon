import ast
from typing import Optional, List

from typhon import js_ast
from typhon.exceptions import InvalidNode


def convert_bin_op(node: ast.BinOp) -> js_ast.JSBinOp:
    js_left = convert_expression(node.left)
    js_right = convert_expression(node.right)
    return js_ast.JSBinOp(js_left, js_ast.JSAdd(), js_right)


def convert_keyword(node: ast.keyword) -> js_ast.JSKeyWord:
    return js_ast.JSKeyWord(arg=node.arg, value=convert_expression(node.value))


def convert_call(node: ast.Call) -> js_ast.JSCall:
    args = getattr(node, 'args', [])
    js_args = convert_expression_list(args)

    keywords = getattr(node, 'keywords', [])
    js_keywords = [convert_keyword(keyword) for keyword in keywords]

    return js_ast.JSCall(convert_expression(node.func), args=js_args, keywords=js_keywords)


def convert_constant(constant: ast.Constant) -> js_ast.JSConstant:
    return js_ast.JSConstant(value=constant.value)


def convert_name(name: ast.Name) -> js_ast.JSName:
    return js_ast.JSName(id=name.id)


def convert_list(node: ast.List) -> js_ast.JSList:
    return js_ast.JSList(elts=convert_expression_list(node.elts))


def convert_tuple(node: ast.Tuple) -> js_ast.JSList:
    return js_ast.JSList(elts=convert_expression_list(node.elts))


def convert_set(node: ast.Set) -> js_ast.JSList:
    return js_ast.JSList(elts=convert_expression_list(node.elts))


def convert_dict(node: ast.Dict) -> js_ast.JSDict:
    return js_ast.JSDict(keys=convert_expression_list(node.keys), values=convert_expression_list(node.values))


def convert_compare(node: ast.Compare) -> js_ast.JSCompare:
    return js_ast.JSCompare(
        left=convert_expression(node.left),
        op=convert_eq(node.ops[0]),
        right=convert_expression(node.comparators[0])
    )


def convert_subscript(node: ast.Subscript) -> js_ast.JSSubscript:
    return js_ast.JSSubscript(value=convert_expression(node.value), slice=convert_expression(node.slice))


def convert_attribute(node: ast.Attribute) -> js_ast.JSAttribute:
    node_value = node.value
    assert isinstance(node_value, ast.Name)
    return js_ast.JSAttribute(value=convert_name(node_value), attr=node.attr)


EXPRESSION_CONVERTER_FUNCTIONS = {
    ast.Name: convert_name,
    ast.Constant: convert_constant,
    ast.BinOp: convert_bin_op,
    ast.Call: convert_call,
    type(None): lambda node: node,
    ast.List: convert_list,
    ast.Tuple: convert_tuple,
    ast.Set: convert_set,
    ast.Dict: convert_dict,
    ast.Compare: convert_compare,
    ast.Subscript: convert_subscript,
    ast.Attribute: convert_attribute,
}


def convert_expression(node: ast.expr) -> js_ast.JSExpression:
    """Транспиляция выражений"""
    converter_function = EXPRESSION_CONVERTER_FUNCTIONS.get(type(node), None)
    if not converter_function:
        raise InvalidNode(node=node)
    return converter_function(node)


def convert_assign(node: ast.Assign) -> js_ast.JSAssign:
    target: ast.expr = node.targets[0]
    value: ast.expr = node.value
    js_target = convert_expression(target)
    js_value = convert_expression(value)
    return js_ast.JSAssign(target=js_target, value=js_value)


def convert_code_expression(node: ast.Expr) -> js_ast.JSCodeExpression:
    node_value = node.value
    node_value_js = convert_expression(node_value)

    return js_ast.JSCodeExpression(value=node_value_js)


def convert_function_def(node: ast.FunctionDef) -> js_ast.JSFunctionDef:
    body_node = convert_body(node.body)
    return js_ast.JSFunctionDef(name=node.name, args=convert_arguments(node.args), body=body_node)


def convert_return(node: ast.Return) -> js_ast.JSReturn:
    return js_ast.JSReturn(value=convert_expression(node.value))


def convert_while(node: ast.While) -> js_ast.JSWhile:
    extended_args = {}
    if hasattr(node, 'orelse'):
        extended_args['orelse'] = convert_body(node.orelse)

    return js_ast.JSWhile(test=convert_expression(node.test), body=convert_body(node.body), **extended_args)


def convert_if(node: ast.If) -> js_ast.JSIf:
    return js_ast.JSIf(
        test=convert_expression(node.test),
        body=convert_body(node.body),
        orelse=convert_body(node.orelse),
    )


def convert_raise(node: ast.Raise) -> js_ast.JSThrow:
    return js_ast.JSThrow(exc=convert_expression(node.exc))


def convert_try(node: ast.Try) -> js_ast.JSTry:
    prev_if = convert_body(node.orelse)
    for exception_handler in reversed(node.handlers):
        exception_type = exception_handler.type
        assert isinstance(exception_type, ast.Name)
        if_statement = js_ast.JSIf(
            test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSName(exception_type.id)),
            body=convert_body(exception_handler.body),
            orelse=prev_if
        )
        prev_if = [if_statement]

    return js_ast.JSTry(
        body=convert_body(node.body),
        catch=prev_if,
        finalbody=convert_body(node.finalbody),
    )


def convert_continue(node: ast.Continue) -> js_ast.JSContinue:
    return js_ast.JSContinue()


def convert_break(node: ast.Break) -> js_ast.JSBreak:
    return js_ast.JSBreak()


def convert_del(node: ast.Delete) -> js_ast.JSStatements:
    statements = [js_ast.JSDelete(convert_expression(target)) for target in node.targets]
    return js_ast.JSStatements(statements=statements)


def convert_alias(node: ast.alias) -> js_ast.JSAlias:
    return js_ast.JSAlias(name=node.name, asname=node.asname)


def convert_import_from(node: ast.ImportFrom) -> js_ast.JSImport:
    import_names = [convert_alias(alias) for alias in node.names]
    return js_ast.JSImport(module=node.module, names=import_names)


def convert_import(node: ast.Import) -> js_ast.JSImport:
    name = node.names[0]
    return js_ast.JSImport(module=name.name, names=[], alias=name.asname)


def convert_class_def(node: ast.ClassDef) -> js_ast.JSClassDef:
    return js_ast.JSClassDef(name=node.name, body=convert_body(node.body))


STATEMENT_CONVERTER_FUNCTIONS = {
    ast.Assign: convert_assign,
    ast.Expr: convert_code_expression,
    ast.FunctionDef: convert_function_def,
    ast.Return: convert_return,
    ast.While: convert_while,
    ast.If: convert_if,
    ast.Raise: convert_raise,
    ast.Try: convert_try,
    ast.Continue: convert_continue,
    ast.Break: convert_break,
    ast.Delete: convert_del,
    ast.ImportFrom: convert_import_from,
    ast.Import: convert_import,
    ast.ClassDef: convert_class_def,
}


def convert_statement(node: ast.stmt) -> js_ast.JSStatement:
    """Транспиляция операторов"""
    statement_converter = STATEMENT_CONVERTER_FUNCTIONS.get(type(node))
    if not statement_converter:
        raise InvalidNode(node=node)
    return statement_converter(node)


def convert_arg(node: ast.arg) -> js_ast.JSArg:
    return js_ast.JSArg(arg=node.arg)


def convert_arg_list(nodes: List[ast.arg]) -> Optional[List[js_ast.JSArg]]:
    return [convert_arg(arg) for arg in nodes] if nodes else None


def convert_expression_list(expressions: List[ast.expr]) -> Optional[List[js_ast.JSExpression]]:
    return [convert_expression(expr) for expr in expressions] if expressions else None


def convert_arguments(node: ast.arguments) -> js_ast.JSArguments:
    """Транспиляция аргументов функций"""
    js_args = convert_arg_list(node.args)
    defaults = convert_expression_list(node.defaults)
    vararg = convert_arg(node.vararg) if node.vararg else None
    kwonlyargs = convert_arg_list(node.kwonlyargs)
    kw_defaults = convert_expression_list(node.kw_defaults)
    kwarg = convert_arg(node.kwarg) if node.kwarg else None
    return js_ast.JSArguments(args=js_args, defaults=defaults, vararg=vararg,
                              kwonlyargs=kwonlyargs, kw_defaults=kw_defaults, kwarg=kwarg)


def convert_body(node: List[ast.stmt]) -> List[js_ast.JSStatement]:
    result = []
    for expr in node:
        if isinstance(expr, ast.Pass):
            continue
        js_statement = convert_statement(expr)
        if isinstance(js_statement, js_ast.JSStatements):
            result.extend(js_statement.statements)
        else:
            result.append(js_statement)
    return result


def convert_eq(node: ast.cmpop) -> js_ast.JSEq:
    return js_ast.JSEq()


def convert_ast(node: ast.Module) -> js_ast.JSModule:
    """Преобразование Python AST в JavaScript AST с сохранением семантики"""
    return js_ast.JSModule(convert_body(node.body))
