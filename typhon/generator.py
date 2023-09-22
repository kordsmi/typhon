from itertools import chain, repeat

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
    elif node.value is None:
        return 'null'
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
    return f'{generate_js_name(node.target)} = {generate_js_expression(node.value)};'


def generate_js_code_expression(node: js_ast.JSCodeExpression) -> str:
    return generate_js_expression(node.value) + ';'


def generate_js_return(node: js_ast.JSReturn) -> str:
    return f'return {generate_js_expression(node.value)};'


def generate_js_function_def(node: js_ast.JSFunctionDef) -> str:
    code_block = '{\n' + generate_js_body(node.body, 1) + '\n}'
    return f'function {node.name}({generate_js_arguments(node.args)}) {code_block}'


STATEMENT_GENERATOR_FUNCTIONS = {
    js_ast.JSAssign: generate_js_assign,
    js_ast.JSCodeExpression: generate_js_code_expression,
    js_ast.JSReturn: generate_js_return,
    js_ast.JSFunctionDef: generate_js_function_def,
}


def generate_js_statement(node: js_ast.JSStatement) -> str:
    generator_function = STATEMENT_GENERATOR_FUNCTIONS.get(type(node), None)
    if not generator_function:
        raise UnsupportedNode(f'Node {type(node).__name__} not supported yet')

    return generator_function(node)


def generate_js_arg(node: js_ast.JSArg) -> str:
    return node.arg


def generate_js_arguments(node: js_ast.JSArguments) -> str:
    class Empty:
        pass

    args = []
    defaults = node.defaults or []
    args_without_values = len(node.args) - len(defaults)

    for arg, value in zip(node.args, chain(repeat(Empty, args_without_values), defaults)):
        arg_str = generate_js_arg(arg)
        if value != Empty:
            arg_str = f'{arg_str}={generate_js_expression(value)}'
        args.append(arg_str)
    if node.kwarg:
        args.append(generate_js_arg(node.kwarg))
    if node.vararg:
        args.append('...' + generate_js_arg(node.vararg))

    return ', '.join(args)


def generate_js_body(nodes: [js_ast.JSStatement], indent: int = 0) -> str:
    result = []
    for node in nodes:
        str_indent = indent * 4 * ' '
        js_code = generate_js_statement(node)
        result.append(str_indent + js_code)
    return '\n'.join(result)
