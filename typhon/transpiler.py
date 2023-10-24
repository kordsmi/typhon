import ast
from typing import Optional, List

from typhon import js_ast
from typhon.exceptions import InvalidNode
from typhon.generator import generate_js_module
from typhon.js_analyzer import transform_module


class Transpiler:
    def __init__(self, src: str):
        self.py_tree: Optional[ast.Module] = None
        self.js_tree = None
        self.src: str = src

    def transpile(self):
        self.parse()
        self.transpile_src()
        return self.generate_js()

    def parse(self):
        self.py_tree = ast.parse(self.src)

    def transpile_src(self):
        self.js_tree = transpile_module(self.py_tree)

    def generate_js(self):
        transform_module(self.js_tree)
        return generate_js_module(self.js_tree)


def transpile(src: str) -> str:
    transpiler = Transpiler(src)
    return transpiler.transpile()


def transpile_bin_op(node: ast.BinOp) -> js_ast.JSBinOp:
    js_left = transpile_expression(node.left)
    js_right = transpile_expression(node.right)
    return js_ast.JSBinOp(js_left, js_ast.JSAdd(), js_right)


def transpile_keyword(node: ast.keyword) -> js_ast.JSKeyWord:
    return js_ast.JSKeyWord(arg=node.arg, value=transpile_expression(node.value))


def transpile_call(node: ast.Call) -> js_ast.JSCall:
    args = getattr(node, 'args', [])
    js_args = transpile_expression_list(args)

    keywords = getattr(node, 'keywords', [])
    js_keywords = [transpile_keyword(keyword) for keyword in keywords]

    return js_ast.JSCall(transpile_expression(node.func), args=js_args, keywords=js_keywords)


def transpile_constant(constant: ast.Constant) -> js_ast.JSConstant:
    return js_ast.JSConstant(value=constant.value)


def transpile_name(name: ast.Name) -> js_ast.JSName:
    return js_ast.JSName(id=name.id)


def transpile_list(node: ast.List) -> js_ast.JSList:
    return js_ast.JSList(elts=transpile_expression_list(node.elts))


def transpile_tuple(node: ast.Tuple) -> js_ast.JSList:
    return js_ast.JSList(elts=transpile_expression_list(node.elts))


def transpile_set(node: ast.Set) -> js_ast.JSList:
    return js_ast.JSList(elts=transpile_expression_list(node.elts))


def transpile_dict(node: ast.Dict) -> js_ast.JSDict:
    return js_ast.JSDict(keys=transpile_expression_list(node.keys), values=transpile_expression_list(node.values))


def transpile_compare(node: ast.Compare) -> js_ast.JSCompare:
    return js_ast.JSCompare(
        left=transpile_expression(node.left),
        op=transpile_eq(node.ops[0]),
        right=transpile_expression(node.comparators[0])
    )


def transpile_subscript(node: ast.Subscript) -> js_ast.JSSubscript:
    return js_ast.JSSubscript(value=transpile_expression(node.value), slice=transpile_expression(node.slice))


def transpile_attribute(node: ast.Attribute) -> js_ast.JSAttribute:
    return js_ast.JSAttribute(value=transpile_name(node.value), attr=node.attr)


EXPRESSION_TRANSPILER_FUNCTIONS = {
    ast.Name: transpile_name,
    ast.Constant: transpile_constant,
    ast.BinOp: transpile_bin_op,
    ast.Call: transpile_call,
    type(None): lambda node: node,
    ast.List: transpile_list,
    ast.Tuple: transpile_tuple,
    ast.Set: transpile_set,
    ast.Dict: transpile_dict,
    ast.Compare: transpile_compare,
    ast.Subscript: transpile_subscript,
    ast.Attribute: transpile_attribute,
}


def transpile_expression(node: ast.expr) -> js_ast.JSExpression:
    transpiler_function = EXPRESSION_TRANSPILER_FUNCTIONS.get(type(node), None)
    if not transpiler_function:
        raise InvalidNode(node=node)
    return transpiler_function(node)


def transpile_assign(node: ast.Assign) -> js_ast.JSAssign:
    target: ast.expr = node.targets[0]
    value: ast.expr = node.value
    js_target = transpile_expression(target)
    js_value = transpile_expression(value)
    return js_ast.JSAssign(target=js_target, value=js_value)


def transpile_code_expression(node: ast.Expr) -> js_ast.JSCodeExpression:
    node_value = node.value
    node_value_js = transpile_expression(node_value)

    return js_ast.JSCodeExpression(value=node_value_js)


def transpile_function_def(node: ast.FunctionDef) -> js_ast.JSFunctionDef:
    body_node = transpile_body(node.body)
    return js_ast.JSFunctionDef(name=node.name, args=transpile_arguments(node.args), body=body_node)


def transpile_return(node: ast.Return) -> js_ast.JSReturn:
    return js_ast.JSReturn(value=transpile_expression(node.value))


def transpile_while(node: ast.While) -> js_ast.JSWhile:
    extended_args = {}
    if hasattr(node, 'orelse'):
        extended_args['orelse'] = transpile_body(node.orelse)

    return js_ast.JSWhile(test=transpile_expression(node.test), body=transpile_body(node.body), **extended_args)


def tranpile_if(node: ast.If) -> js_ast.JSIf:
    return js_ast.JSIf(
        test=transpile_expression(node.test),
        body=transpile_body(node.body),
        orelse=transpile_body(node.orelse),
    )


def transpile_raise(node: ast.Raise) -> js_ast.JSThrow:
    return js_ast.JSThrow(exc=transpile_expression(node.exc))


def transpile_try(node: ast.Try) -> js_ast.JSTry:
    prev_if = transpile_body(node.orelse)
    for exception_handler in reversed(node.handlers):
        if_statement = js_ast.JSIf(
            test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSName(exception_handler.type.id)),
            body=transpile_body(exception_handler.body),
            orelse=prev_if
        )
        prev_if = [if_statement]

    return js_ast.JSTry(
        body=transpile_body(node.body),
        catch=prev_if,
        finalbody=transpile_body(node.finalbody),
    )


def transpile_continue(node: ast.Continue) -> js_ast.JSContinue:
    return js_ast.JSContinue()


def transpile_break(node: ast.Break) -> js_ast.JSBreak:
    return js_ast.JSBreak()


def transpile_del(node: ast.Delete) -> js_ast.JSStatements:
    statements = [js_ast.JSDelete(transpile_expression(target)) for target in node.targets]
    return js_ast.JSStatements(statements=statements)


def transpile_alias(node: ast.alias) -> js_ast.JSAlias:
    return js_ast.JSAlias(name=node.name, asname=node.asname)


def transpile_import_from(node: ast.ImportFrom) -> js_ast.JSImport:
    import_names = [transpile_alias(alias) for alias in node.names]
    return js_ast.JSImport(module=node.module, names=import_names)


def transpile_import(node: ast.Import) -> js_ast.JSImport:
    name = node.names[0]
    return js_ast.JSImport(module=name.name, names=[], alias=name.asname)


def transpile_class_def(node: ast.ClassDef) -> js_ast.JSClassDef:
    return js_ast.JSClassDef(name=node.name, body=transpile_body(node.body))


STATEMENT_TRANSPILER_FUNCTIONS = {
    ast.Assign: transpile_assign,
    ast.Expr: transpile_code_expression,
    ast.FunctionDef: transpile_function_def,
    ast.Return: transpile_return,
    ast.While: transpile_while,
    ast.If: tranpile_if,
    ast.Raise: transpile_raise,
    ast.Try: transpile_try,
    ast.Continue: transpile_continue,
    ast.Break: transpile_break,
    ast.Delete: transpile_del,
    ast.ImportFrom: transpile_import_from,
    ast.Import: transpile_import,
    ast.ClassDef: transpile_class_def,
}


def transpile_statement(node: ast.stmt) -> js_ast.JSStatement:
    statement_transpiler = STATEMENT_TRANSPILER_FUNCTIONS.get(type(node))
    if not statement_transpiler:
        raise InvalidNode(node=node)
    return statement_transpiler(node)


def transpile_arg(node: ast.arg) -> js_ast.JSArg:
    return js_ast.JSArg(arg=node.arg)


def transpile_arg_list(nodes: [ast.arg]) -> Optional[List[js_ast.JSArg]]:
    return [transpile_arg(arg) for arg in nodes] if nodes else None


def transpile_expression_list(expressions: [ast.expr]) -> Optional[List[js_ast.JSExpression]]:
    return [transpile_expression(expr) for expr in expressions] if expressions else None


def transpile_arguments(node: ast.arguments) -> js_ast.JSArguments:
    js_args = transpile_arg_list(node.args)
    defaults = transpile_expression_list(node.defaults)
    vararg = transpile_arg(node.vararg) if node.vararg else None
    kwonlyargs = transpile_arg_list(node.kwonlyargs)
    kw_defaults = transpile_expression_list(node.kw_defaults)
    kwarg = transpile_arg(node.kwarg) if node.kwarg else None
    return js_ast.JSArguments(args=js_args, defaults=defaults, vararg=vararg,
                              kwonlyargs=kwonlyargs, kw_defaults=kw_defaults, kwarg=kwarg)


def transpile_body(node: [ast.stmt]) -> [js_ast.JSStatement]:
    result = []
    for expr in node:
        if isinstance(expr, ast.Pass):
            continue
        js_statement = transpile_statement(expr)
        if isinstance(js_statement, js_ast.JSStatements):
            result.extend(js_statement.statements)
        else:
            result.append(js_statement)
    return result


def transpile_eq(node: ast.Eq) -> js_ast.JSEq:
    return js_ast.JSEq()


def transpile_module(node: ast.Module) -> js_ast.JSModule:
    return js_ast.JSModule(transpile_body(node.body))
