import ast

from typhon import js_ast
from typhon.generator import generate_js


def transpile(src: str) -> str:
    py_tree = ast.parse(src)
    js_tree = transpile_call(py_tree.body[0].value)
    return generate_js(js_tree) + ';'


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
    js_args = [transpile_expression(arg) for arg in args]

    keywords = getattr(node, 'keywords', [])
    js_keywords = [transpile_keyword(keyword) for keyword in keywords]

    return js_ast.JSCall(func_name, args=js_args, keywords=js_keywords)


def transpile_expression(node: ast.expr) -> js_ast.JSExpression:
    if isinstance(node, ast.Name):
        js_node = transpile_name(node)
    elif isinstance(node, ast.Constant):
        js_node = transpile_constant(node)
    elif isinstance(node, ast.BinOp):
        js_node = transpile_bin_op(node)
    return js_node


def transpile_assign(node: ast.Assign) -> js_ast.JSAssign:
    target: ast.Name = node.targets[0]
    value: ast.expr = node.value
    js_target = transpile_name(target)
    js_value = transpile_expression(value)
    return js_ast.JSAssign(target=js_target, value=js_value)


def transpile_constant(constant: ast.Constant) -> js_ast.JSConstant:
    return js_ast.JSConstant(value=constant.value)


def transpile_name(name: ast.Name) -> js_ast.JSName:
    return js_ast.JSName(id=name.id)
