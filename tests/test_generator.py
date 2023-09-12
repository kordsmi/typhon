import pytest

from typhon import js_ast
from typhon.exceptions import UnsupportedNode
from typhon.generator import generate_js_name, generate_js_constant, generate_js_expression, \
    generate_js_bin_op, generate_js_call, generate_js_code_expression, generate_js_statement


def test_generate_js_code__expression():
    js_node = js_ast.JSCodeExpression(
        value=js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))
    )
    js_str = '1 + 2'

    result = generate_js_code_expression(js_node)

    assert result == js_str


def test_generate_js_statement__assign():
    js_node = js_ast.JSAssign(
        target=js_ast.JSName(id='v'),
        value=js_ast.JSConstant(value=2)
    )
    js_str = 'v = 2;'

    result = generate_js_statement(js_node)

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


def test_generate_js_expression__call():
    js_node = js_ast.JSCall(
        func='console.log',
        args=[js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))]
    )
    js_str = 'console.log(1 + 2)'

    result = generate_js_expression(js_node)

    assert result == js_str


def test_generate_js_expression__unsupported_node():
    class NewNode(js_ast.JSExpression):
        pass

    js_node = NewNode()

    with pytest.raises(UnsupportedNode):
        generate_js_expression(js_node)


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
