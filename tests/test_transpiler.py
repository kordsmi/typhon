import ast

from typhon import js_ast
from typhon.transpiler import transpile, transpile_bin_op, transpile_call, generate_js


def test_transpiler():
    py_str = 'print(1 + 2)'
    js_str = 'console.log(1 + 2);'

    result = transpile(py_str)

    assert result == js_str


def test_transpile_bin_op():
    bin_op_node = ast.BinOp(left=ast.Constant(value=1), op=ast.Add(), right=ast.Constant(value=2))
    js_node = js_ast.JSBinOp(left=1, op=js_ast.JSAdd(), right=2)

    result = transpile_bin_op(bin_op_node)

    assert type(result) == type(js_node)
    assert result.left == js_node.left
    assert result.right == js_node.right
    assert type(result.op) == type(js_node.op)


def test_transpile_call():
    call_node = ast.Call(func=ast.Name(id='test', ctx=ast.Load()))

    result = transpile_call(call_node)

    assert isinstance(result,  js_ast.JSCall)
    assert result.func == 'test'


def test_transpile_call__with_args():
    call_node = ast.Call(func=ast.Name(id='test', ctx=ast.Load()), args=[ast.Constant(value=1), ast.Name(id='a')])

    result = transpile_call(call_node)

    assert isinstance(result,  js_ast.JSCall)
    assert result.func == 'test'
    assert result.args == [1, 'a']


def test_transpile_call__print():
    call_node = ast.Call(func=ast.Name(id='print', ctx=ast.Load()), args=[ast.Constant(value='Hello!')])

    result = transpile_call(call_node)

    assert isinstance(result,  js_ast.JSCall)
    assert result.func == 'console.log'
    assert result.args == ['Hello!']


def test_transpile_call__with_expression():
    call_node = ast.Call(
        func=ast.Name(id='test', ctx=ast.Load()),
        args=[ast.BinOp(left=ast.Constant(value=1), op=ast.Add(), right=ast.Constant(value=2))]
    )

    result = transpile_call(call_node)

    assert isinstance(result,  js_ast.JSCall)
    assert result.func == 'test'
    assert len(result.args) == 1
    js_arg = result.args[0]
    assert isinstance(js_arg, js_ast.JSBinOp)
    assert js_arg.left == 1
    assert isinstance(js_arg.op, js_ast.JSAdd)
    assert js_arg.right == 2


def test_js_generator():
    js_node = js_ast.JSBinOp(left=1, op=js_ast.JSAdd(), right=2)
    js_str = '1 + 2'

    result = generate_js(js_node)

    assert result == js_str


def test_js_generator__call():
    js_node = js_ast.JSCall(
        func='console.log',
        args=[js_ast.JSBinOp(left=1, op=js_ast.JSAdd(), right=2)]
    )
    js_str = 'console.log(1 + 2)'

    result = generate_js(js_node)

    assert result == js_str
