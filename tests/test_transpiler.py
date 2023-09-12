import ast

import pytest

from typhon import js_ast
from typhon.exceptions import InvalidNode
from typhon.transpiler import transpile, transpile_bin_op, transpile_call, transpile_assign, transpile_expression, \
    Transpiler


def test_transpiler():
    py_str = 'print(1 + 2)'
    js_str = 'console.log(1 + 2);'

    result = transpile(py_str)

    assert result == js_str


class TestTranspiler:
    def test_transpile_multiple_expressions(self):
        src = '''a = 1
print('a + 2 = ', a + 2)'''
        transpiler = Transpiler(src)
        transpiler.parse()

        transpiler.transpile_src()

        expected = [
            js_ast.JSAssign(target=js_ast.JSName(id='a'), value=js_ast.JSConstant(value=1)),
            js_ast.JSCodeExpression(js_ast.JSCall(func='console.log', args=[
                js_ast.JSConstant(value='a + 2 = '),
                js_ast.JSBinOp(left=js_ast.JSName(id='a'), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2)),
            ]))
        ]
        assert transpiler.js_tree == expected


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


def test_transpile_expression__unknown_node():
    class UnknownNode(ast.expr):
        pass

    with pytest.raises(InvalidNode) as e:
        transpile_expression(UnknownNode())

    assert isinstance(e.value.node, UnknownNode)
