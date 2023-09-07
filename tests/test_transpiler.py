import ast

import pytest

from typhon import js_ast
from typhon.transpiler import transpile, transpile_bin_op, transpile_call, generate_js, transpile_assign, \
    generate_js_name, generate_js_constant, generate_js_expression, generate_js_bin_op, generate_js_call


def test_transpiler():
    py_str = 'print(1 + 2)'
    js_str = 'console.log(1 + 2);'

    result = transpile(py_str)

    assert result == js_str


def test_transpile_set_variable__int():
    assign_node = ast.Assign(
        targets=[ast.Name(id='a', ctx=ast.Store())],
        value=ast.Constant(value='sample')
    )

    result = transpile_assign(assign_node)

    assert isinstance(result, js_ast.JSAssign)
    assert isinstance(result.target, js_ast.JSName)
    assert result.target.id == 'a'
    assert isinstance(result.value, js_ast.JSConstant)
    assert result.value.value == 'sample'


def test_transpile_set_variable__expression():
    assign_node = ast.Assign(
        targets=[ast.Name(id='b', ctx=ast.Store())],
        value=ast.BinOp(
            left=ast.Name(id='a', ctx=ast.Load()),
            op=ast.Add(),
            right=ast.Constant(value=3)
        )
    )

    result = transpile_assign(assign_node)

    assert result.target.id == 'b'
    value = result.value
    assert isinstance(value, js_ast.JSBinOp)
    assert isinstance(value.left, js_ast.JSName)
    assert value.left.id == 'a'
    assert isinstance(value.op, js_ast.JSAdd)
    assert isinstance(value.right, js_ast.JSConstant)
    assert value.right.value == 3


def test_transpile_bin_op():
    bin_op_node = ast.BinOp(left=ast.Constant(value=1), op=ast.Add(), right=ast.Constant(value=2))

    result = transpile_bin_op(bin_op_node)

    assert isinstance(result, js_ast.JSBinOp)
    assert isinstance(result.left, js_ast.JSConstant)
    assert result.left.value == 1
    assert isinstance(result.right, js_ast.JSConstant)
    assert result.right.value == 2
    assert isinstance(result.op, js_ast.JSAdd)


def test_transpile_call():
    call_node = ast.Call(func=ast.Name(id='test', ctx=ast.Load()))

    result = transpile_call(call_node)

    assert isinstance(result,  js_ast.JSCall)
    assert result.func == 'test'


def test_transpile_call__with_args():
    call_node = ast.Call(func=ast.Name(id='test', ctx=ast.Load()), args=[ast.Constant(value=1), ast.Name(id='a')])

    result = transpile_call(call_node)

    expected = js_ast.JSCall(func='test', args=[js_ast.JSConstant(value=1), js_ast.JSName(id='a')])
    assert result == expected


def test_transpile_call__with_keywords():
    call_node = ast.Call(
        func=ast.Name(id='test', ctx=ast.Load()),
        args=[],
        keywords=[
          ast.keyword(arg='a', value=ast.Constant(value=1)),
          ast.keyword(arg='b', value=ast.Constant(value=2))
        ]
    )

    result = transpile_call(call_node)

    expected = js_ast.JSCall(
        func='test',
        keywords=[
            js_ast.JSKeyWord(arg='a', value=js_ast.JSConstant(value=1)),
            js_ast.JSKeyWord(arg='b', value=js_ast.JSConstant(value=2))
        ]
    )
    assert result == expected


def test_transpile_call__print():
    call_node = ast.Call(func=ast.Name(id='print', ctx=ast.Load()), args=[ast.Constant(value='Hello!')])

    result = transpile_call(call_node)

    expected = js_ast.JSCall(func='console.log', args=[js_ast.JSConstant(value='Hello!')])
    assert result == expected


def test_transpile_call__with_expression():
    call_node = ast.Call(
        func=ast.Name(id='test', ctx=ast.Load()),
        args=[ast.BinOp(left=ast.Constant(value=1), op=ast.Add(), right=ast.Constant(value=2))]
    )

    result = transpile_call(call_node)

    expected = js_ast.JSCall(
        func='test',
        args=[
            js_ast.JSBinOp(
                left=js_ast.JSConstant(value=1),
                op=js_ast.JSAdd(),
                right=js_ast.JSConstant(value=2)
            )
        ]
    )
    assert result == expected


def test_js_generator():
    js_node = js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))
    js_str = '1 + 2'

    result = generate_js(js_node)

    assert result == js_str


def test_js_generator__call():
    js_node = js_ast.JSCall(
        func='console.log',
        args=[js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))]
    )
    js_str = 'console.log(1 + 2)'

    result = generate_js(js_node)

    assert result == js_str


def test_generate_js_name():
    js_node = js_ast.JSName(id='a')

    result = generate_js_name(js_node)

    assert result == 'a'


def test_generate_js_constant__number():
    js_node = js_ast.JSConstant(value=100)

    result = generate_js_constant(js_node)

    assert result == '100'


def test_generate_js_constant__string():
    js_node = js_ast.JSConstant(value='example')

    result = generate_js_constant(js_node)

    assert result == "'example'"


def test_generate_js_expression__name():
    js_node = js_ast.JSName(id='a')

    assert generate_js_expression(js_node) == 'a'


@pytest.mark.parametrize('value, result', [(25, '25'), ('test', "'test'")])
def test_generate_js_expression__constant(value, result):
    js_node = js_ast.JSConstant(value=value)

    assert generate_js_expression(js_node) == result


def test_generate_js_bin_op():
    js_node = js_ast.JSBinOp(
        left=js_ast.JSBinOp(
            left=js_ast.JSName(id='a'),
            op=js_ast.JSAdd(),
            right=js_ast.JSConstant(value='123')),
        op=js_ast.JSAdd(),
        right=js_ast.JSConstant(value=2)
    )

    result = generate_js_bin_op(js_node)
    expected = "a + '123' + 2"

    assert result == expected


def test_generate_js_call():
    js_node = js_ast.JSCall(
        func='test',
        args=[
            js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))
        ],
        keywords=[
            js_ast.JSKeyWord(arg='name', value=js_ast.JSConstant(value='value'))
        ]
    )

    result = generate_js_call(js_node)
    expected = "test(1 + 2, name='value')"

    assert result == expected
