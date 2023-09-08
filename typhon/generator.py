from typhon import js_ast


def generate_js_bin_op(node: js_ast.JSBinOp) -> str:
    left = generate_js_expression(node.left)
    right = generate_js_expression(node.right)
    op = '+' if isinstance(node.op, js_ast.JSAdd) else ''
    return f'{left} {op} {right}'


def generate_js_keyword(node: js_ast.JSKeyWord) -> str:
    return f'{node.arg}={generate_js_expression(node.value)}'


def generate_js_call(node: js_ast.JSCall) -> str:
    args_str = [generate_js_expression(arg) for arg in node.args]
    args_str += [generate_js_keyword(keyword) for keyword in node.keywords]

    return f'{node.func}({", ".join(args_str)})'


def generate_js_name(node: js_ast.JSName):
    return node.id


def generate_js_constant(node: js_ast.JSConstant):
    if isinstance(node.value, str):
        return f"'{node.value}'"
    return str(node.value)


def generate_js_expression(node: js_ast.JSExpression) -> str:
    if isinstance(node, js_ast.JSBinOp):
        return generate_js_bin_op(node)
    elif isinstance(node, js_ast.JSCall):
        return generate_js_call(node)
    elif isinstance(node, js_ast.JSName):
        return generate_js_name(node)
    elif isinstance(node, js_ast.JSConstant):
        return generate_js_constant(node)


def generate_js(node) -> str:
    if isinstance(node, js_ast.JSExpression):
        return generate_js_expression(node)
