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
    args_str = generate_expression_list(node.args)
    args_str += [generate_js_keyword(keyword) for keyword in node.keywords]

    return f'{node.func}({", ".join(args_str)})'


def generate_js_name(node: js_ast.JSName):
    return node.id


def generate_js_constant(node: js_ast.JSConstant):
    if isinstance(node.value, str):
        return f"'{node.value}'"
    elif node.value is None:
        return 'null'
    elif node.value is True:
        return 'true'
    return str(node.value)


def generate_js_list(node: js_ast.JSList) -> str:
    elements = ', '.join(generate_expression_list(node.elts))
    return f'[{elements}]'


def generate_expression_list(expr_list: [js_ast.JSExpression]) -> [str]:
    if expr_list is None:
        return []
    return [generate_js_expression(element) for element in expr_list]


def generate_js_dict(node: js_ast.JSDict) -> str:
    if node.keys:
        named_args_list = [
            f'{generate_js_expression(key)}: {generate_js_expression(value)}'
            for key, value in zip(node.keys, node.values)
        ]
    else:
        named_args_list = []
    named_args_str = ', '.join(named_args_list)
    return f'{{{named_args_str}}}'


def generate_js_compare(node: js_ast.JSCompare) -> str:
    return f'{generate_js_expression(node.left)} {generate_js_eq(node.op)} {generate_js_expression(node.right)}'


def generate_js_subscript(node: js_ast.JSSubscript) -> str:
    return f'{generate_js_expression(node.value)}[{generate_js_expression(node.slice)}]'


EXPRESSION_GENERATOR_FUNCTIONS = {
    js_ast.JSBinOp: generate_js_bin_op,
    js_ast.JSCall: generate_js_call,
    js_ast.JSName: generate_js_name,
    js_ast.JSConstant: generate_js_constant,
    js_ast.JSList: generate_js_list,
    js_ast.JSDict: generate_js_dict,
    js_ast.JSCompare: generate_js_compare,
    js_ast.JSSubscript: generate_js_subscript,
}


def generate_js_expression(node: js_ast.JSExpression) -> str:
    generator_function = EXPRESSION_GENERATOR_FUNCTIONS.get(type(node), None)
    if not generator_function:
        raise UnsupportedNode(f'Node {type(node).__name__} not supported yet')

    return generator_function(node)


def generate_js_assign(node: js_ast.JSAssign) -> str:
    return f'{generate_js_expression(node.target)} = {generate_js_expression(node.value)};'


def generate_js_code_expression(node: js_ast.JSCodeExpression) -> str:
    return generate_js_expression(node.value) + ';'


def generate_js_return(node: js_ast.JSReturn) -> str:
    return f'return {generate_js_expression(node.value)};'


def generate_js_function_def(node: js_ast.JSFunctionDef) -> str:
    code_block = generate_code_block(node.body)
    return f'function {node.name}({generate_js_arguments(node.args)}) {code_block}'


def generate_js_while(node: js_ast.JSWhile) -> str:
    test_str = generate_js_expression(node.test)
    while_body = generate_code_block(node.body)
    else_body = ''
    if node.orelse:
        else_body = ' else ' + generate_code_block(node.orelse)
    return f'while {test_str} {while_body}{else_body}'


code_block_indent = 0


def generate_code_block(body: [js_ast.JSStatement]) -> str:
    global code_block_indent

    code_block_indent += 1
    try:
        js_body_str = generate_js_body(body)
    finally:
        code_block_indent -= 1
    if js_body_str:
        js_body_str += '\n'
    return '{\n' + js_body_str + get_indent_str() + '}'


def generate_js_if(node: js_ast.JSIf) -> str:
    if_str = f'if ({generate_js_expression(node.test)}) {generate_code_block(node.body)}'
    else_str = f' else {generate_code_block(node.orelse)}' if node.orelse else ''
    return if_str + else_str


def generate_js_throw(node: js_ast.JSThrow) -> str:
    return f'throw {generate_js_expression(node.exc)};'


def generate_js_try(node: js_ast.JSTry) -> str:
    try_str = f'try {generate_code_block(node.body)}'
    catch_str = f' catch (e) {generate_code_block(node.catch)}'
    finally_str = ''
    if node.finalbody:
        finally_str = f' finally {generate_code_block(node.finalbody)}'
    return try_str + catch_str + finally_str


def generate_js_continue(node: js_ast.JSContinue) -> str:
    return 'continue;'


def generate_js_break(node: js_ast.JSBreak) -> str:
    return 'break;'


def generate_js_delete(node: js_ast.JSDelete) -> str:
    return f'delete {generate_js_expression(node.target)};'


STATEMENT_GENERATOR_FUNCTIONS = {
    js_ast.JSAssign: generate_js_assign,
    js_ast.JSCodeExpression: generate_js_code_expression,
    js_ast.JSReturn: generate_js_return,
    js_ast.JSFunctionDef: generate_js_function_def,
    js_ast.JSWhile: generate_js_while,
    js_ast.JSIf: generate_js_if,
    js_ast.JSThrow: generate_js_throw,
    js_ast.JSTry: generate_js_try,
    js_ast.JSContinue: generate_js_continue,
    js_ast.JSBreak: generate_js_break,
    js_ast.JSDelete: generate_js_delete,
}


def get_indent_str() -> str:
    return code_block_indent * 4 * ' '


def generate_js_statement(node: js_ast.JSStatement) -> str:
    generator_function = STATEMENT_GENERATOR_FUNCTIONS.get(type(node), None)
    if not generator_function:
        raise UnsupportedNode(f'Node {type(node).__name__} not supported yet')

    return get_indent_str() + generator_function(node)


def generate_js_arg(node: js_ast.JSArg) -> str:
    return node.arg


def generate_js_arguments(node: js_ast.JSArguments) -> str:
    class Empty:
        pass

    args = []
    node_args = node.args or []
    defaults = node.defaults or []
    args_without_values = len(node_args) - len(defaults)

    for arg, value in zip(node_args, chain(repeat(Empty, args_without_values), defaults)):
        arg_str = generate_js_arg(arg)
        if value != Empty:
            arg_str = f'{arg_str}={generate_js_expression(value)}'
        args.append(arg_str)
    if node.kwarg:
        args.append(generate_js_arg(node.kwarg))
    if node.vararg:
        args.append('...' + generate_js_arg(node.vararg))

    return ', '.join(args)


def generate_js_body(nodes: [js_ast.JSStatement]) -> str:
    result = [generate_js_statement(node) for node in nodes]
    return '\n'.join(result)


def generate_js_eq(node: js_ast.JSEq) -> str:
    return '==='


def generate_js_module(node: js_ast.JSModule) -> str:
    result = ''
    if node.export:
        result = generate_js_export(node.export) + '\n\n'
    return result + generate_js_body(node.body)


def generate_js_export(node: js_ast.JSExport) -> str:
    ids_str = ', '.join(node.ids)
    return f'export {{{ids_str}}};'
