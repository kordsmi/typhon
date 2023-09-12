from typhon import js_ast
from typhon.exceptions import UnsupportedNode


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


NODE_GENERATOR_FUNCTIONS = {
    js_ast.JSBinOp: generate_js_bin_op,
    js_ast.JSCall: generate_js_call,
    js_ast.JSName: generate_js_name,
    js_ast.JSConstant: generate_js_constant,
}


def generate_js_expression(node: js_ast.JSExpression) -> str:
    generator_function = NODE_GENERATOR_FUNCTIONS.get(type(node), None)
    if not generator_function:
        raise UnsupportedNode(f'Node {type(node).__name__} not supported yet')

    return generator_function(node)


def generate_js_assign(node: js_ast.JSAssign) -> str:
    return f'{generate_js_name(node.target)} = {generate_js_expression(node.value)}'


def generate_js_code_expression(node: js_ast.JSCodeExpression) -> str:
    return generate_js_expression(node.value)


def generate_js_statement(node: js_ast.JSStatement) -> str:
    js_node = None
    if isinstance(node, js_ast.JSAssign):
        js_node = generate_js_assign(node)
    if isinstance(node, js_ast.JSCodeExpression):
        js_node = generate_js_code_expression(node)

    return js_node + ';'
