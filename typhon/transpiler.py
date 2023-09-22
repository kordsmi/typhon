import ast
from typing import Optional, List

from typhon import js_ast
from typhon.exceptions import InvalidNode
from typhon.generator import generate_js_body


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
        self.js_tree = _transpile_body(self.py_tree.body)

    def generate_js(self):
        return generate_js_body(self.js_tree)


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
    func: ast.Name = node.func
    func_name = func.id
    if func_name == 'print':
        func_name = 'console.log'

    args = getattr(node, 'args', [])
    js_args = transpile_expression_list(args)

    keywords = getattr(node, 'keywords', [])
    js_keywords = [transpile_keyword(keyword) for keyword in keywords]

    return js_ast.JSCall(func_name, args=js_args, keywords=js_keywords)


def transpile_constant(constant: ast.Constant) -> js_ast.JSConstant:
    return js_ast.JSConstant(value=constant.value)


def transpile_name(name: ast.Name) -> js_ast.JSName:
    return js_ast.JSName(id=name.id)


NODE_TRANSPILER_FUNCTIONS = {
    ast.Name: transpile_name,
    ast.Constant: transpile_constant,
    ast.BinOp: transpile_bin_op,
    ast.Call: transpile_call,
    type(None): lambda node: node,
}


def transpile_expression(node: ast.expr) -> js_ast.JSExpression:
    transpiler_function = NODE_TRANSPILER_FUNCTIONS.get(type(node), None)
    if not transpiler_function:
        raise InvalidNode(node=node)
    return transpiler_function(node)


def transpile_assign(node: ast.Assign) -> js_ast.JSAssign:
    target: ast.Name = node.targets[0]
    value: ast.expr = node.value
    js_target = transpile_name(target)
    js_value = transpile_expression(value)
    return js_ast.JSAssign(target=js_target, value=js_value)


def transpile_code_expression(node: ast.Expr) -> js_ast.JSCodeExpression:
    node_value = node.value
    node_value_js = transpile_expression(node_value)

    return js_ast.JSCodeExpression(value=node_value_js)


def transpile_function_def(node: ast.FunctionDef) -> js_ast.JSFunctionDef:
    body_node = _transpile_body(node.body)
    return js_ast.JSFunctionDef(name=node.name, args=transpile_arguments(node.args), body=body_node)


def transpile_return(node: ast.Return) -> js_ast.JSReturn:
    return js_ast.JSReturn(value=transpile_expression(node.value))


STATEMENT_TRANSPILER_FUNCTIONS = {
    ast.Assign: transpile_assign,
    ast.Expr: transpile_code_expression,
    ast.FunctionDef: transpile_function_def,
    ast.Return: transpile_return,
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


def _transpile_body(node: [ast.stmt]) -> [js_ast.JSStatement]:
    return [transpile_statement(expr) for expr in node]
