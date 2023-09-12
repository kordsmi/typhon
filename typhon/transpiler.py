import ast
from typing import Optional

from typhon import js_ast
from typhon.exceptions import InvalidNode
from typhon.generator import generate_js_statement


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
        self.js_tree = [transpile_statement(expr) for expr in self.py_tree.body]

    def generate_js(self):
        result = []
        for node in self.js_tree:
            js_code = generate_js_statement(node)
            result.append(js_code)
        return '\n'.join(result)


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
    js_args = [transpile_expression(arg) for arg in args]

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


def transpile_statement(node: ast.stmt) -> js_ast.JSStatement:
    js_node = None
    if isinstance(node, ast.Assign):
        js_node = transpile_assign(node)
    elif isinstance(node, ast.Expr):
        js_node = transpile_code_expression(node)
    return js_node


def transpile_code_expression(node: ast.Expr) -> js_ast.JSCodeExpression:
    node_value = node.value
    node_value_js = transpile_expression(node_value)

    return js_ast.JSCodeExpression(value=node_value_js)
