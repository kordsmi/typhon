import ast

from typhon import js_ast


def transpile(src: str) -> str:
    py_tree = ast.parse(src)
    js_tree = transpile_call(py_tree.body[0].value)
    return generate_js(js_tree) + ';'


def transpile_bin_op(node: ast.BinOp) -> js_ast.JSBinOp:
    left_const: ast.Constant = node.left
    right_const: ast.Constant = node.right
    return js_ast.JSBinOp(left_const.value, js_ast.JSAdd(), right_const.value)


def transpile_call(node: ast.Call) -> js_ast.JSCall:
    func: ast.Name = node.func
    func_name = func.id
    if func_name == 'print':
        func_name = 'console.log'
    args = getattr(node, 'args', [])
    js_args = []
    for arg in args:
        if isinstance(arg, ast.Name):
            js_args.append(arg.id)
        elif isinstance(arg, ast.Constant):
            js_args.append(arg.value)
        elif isinstance(arg, ast.BinOp):
            js_args.append(transpile_bin_op(arg))
    return js_ast.JSCall(func_name, args=js_args)


def generate_js_bin_op(node: js_ast.JSBinOp) -> str:
    left = node.left
    right = node.right
    op = '+' if isinstance(node.op, js_ast.JSAdd) else ''
    return f'{left} {op} {right}'


def generate_js_call(node: js_ast.JSCall) -> str:
    args = node.args
    args_str = []

    for arg in args:
        if isinstance(arg, js_ast.JSExpression):
            args_str.append(generate_js(arg))
        else:
            args_str.append(str(arg))

    return f'{node.func}({", ".join(args_str)})'


def generate_js(node: js_ast.JSExpression) -> str:
    if isinstance(node, js_ast.JSBinOp):
        return generate_js_bin_op(node)
    elif isinstance(node, js_ast.JSCall):
        return generate_js_call(node)
