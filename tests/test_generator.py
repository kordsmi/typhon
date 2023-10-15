import ast

import pytest

from tests.test_transpiler import _create_arguments_node
from typhon import js_ast, generator
from typhon.exceptions import UnsupportedNode
from typhon.generator import generate_js_name, generate_js_constant, generate_js_expression, generate_js_bin_op, \
    generate_js_call, generate_js_code_expression, generate_js_statement, generate_js_arg, generate_js_arguments, \
    generate_js_return, generate_js_eq, generate_code_block, generate_js_dict, generate_expression_list, \
    generate_js_assign, generate_js_module
from typhon.transpiler import transpile_arguments


def test_generate_js_code__expression():
    js_node = js_ast.JSCodeExpression(
        value=js_ast.JSBinOp(left=js_ast.JSConstant(value=1), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2))
    )

    result = generate_js_code_expression(js_node)

    js_str = '1 + 2;'
    assert result == js_str


def test_generate_js_statement__assign():
    js_node = js_ast.JSAssign(
        target=js_ast.JSName(id='v'),
        value=js_ast.JSConstant(value=2)
    )
    js_str = 'v = 2;'

    result = generate_js_statement(js_node)

    assert result == js_str


def test_generate_statement__function_def():
    js_node = js_ast.JSFunctionDef(
        'bar',
        js_ast.JSArguments([js_ast.JSArg('foo')]),
        [js_ast.JSReturn(js_ast.JSConstant(5))],
    )

    result = generate_js_statement(js_node)

    expected = '''function bar(foo) {
    return 5;
}'''
    assert result == expected


def test_generate_js_statement__while():
    node = js_ast.JSWhile(test=js_ast.JSConstant(value=True), body=[])
    result = generate_js_statement(node)
    assert result == 'while true {\n}'


def test_generate_js_statement__while_else():
    node = js_ast.JSWhile(
        test=js_ast.JSConstant(value=True),
        body=[],
        orelse=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
    )

    result = generate_js_statement(node)

    assert result == 'while true {\n} else {\n    a;\n}'


def test_generate_js_statement__if():
    node = js_ast.JSIf(
        test=js_ast.JSConstant(value=True),
        body=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
    )

    result = generate_js_statement(node)

    expected = '''if (true) {
    a;
}'''
    assert result == expected


def test_generate_js_statement__indents():
    node = js_ast.JSWhile(
        test=js_ast.JSConstant(value=True),
        body=[
            js_ast.JSWhile(test=js_ast.JSConstant(value=True), body=[js_ast.JSReturn(value=js_ast.JSConstant(None))])
        ]
    )

    result = generate_js_statement(node)

    expected = '''while true {
    while true {
        return null;
    }
}'''
    assert result == expected


def test_generate_js_statement__throw():
    node = js_ast.JSThrow(exc=js_ast.JSName('Exception'))
    result = generate_js_statement(node)
    assert result == 'throw Exception;'


def test_generate_js_statement__continue():
    node = js_ast.JSContinue()
    result = generate_js_statement(node)
    assert result == 'continue;'


def test_generate_js_statement__break():
    node = js_ast.JSBreak()
    result = generate_js_statement(node)
    assert result == 'break;'


def test_generate_js_statement__delete():
    node = js_ast.JSDelete(js_ast.JSName('d'))
    result = generate_js_statement(node)
    assert result == 'delete d;'


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


def test_generate_constant__null():
    js_node = js_ast.JSConstant(value=None)

    result = generate_js_constant(js_node)

    expected = 'null'
    assert result == expected


def test_generate_constant__true():
    js_node = js_ast.JSConstant(value=True)
    result = generate_js_constant(js_node)
    assert result == 'true'


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


def test_generate_js_expression__list():
    js_node = js_ast.JSList(elts=[js_ast.JSConstant(1), js_ast.JSConstant(2)])

    result = generate_js_expression(js_node)

    expected = '[1, 2]'
    assert result == expected


def test_generate_js_expression__dict():
    js_node = js_ast.JSDict(
        keys=[js_ast.JSConstant('a'), js_ast.JSConstant('b')],
        values=[js_ast.JSConstant(1), js_ast.JSConstant(2)]
    )

    result = generate_js_expression(js_node)

    expected = "{'a': 1, 'b': 2}"
    assert result == expected


def test_generate_js_expression__compare():
    js_node = js_ast.JSCompare(left=js_ast.JSName('a'), op=js_ast.JSEq(), right=js_ast.JSConstant(1))
    result = generate_js_expression(js_node)
    assert result == 'a === 1'


def test_generate_js_expression__unsupported_node():
    class NewNode(js_ast.JSExpression):
        pass

    js_node = NewNode()

    with pytest.raises(UnsupportedNode):
        generate_js_expression(js_node)


def test_generate_js_expression__subscript():
    js_node = js_ast.JSSubscript(js_ast.JSName('a'), js_ast.JSConstant('c'))
    result = generate_js_expression(js_node)
    assert result == "a['c']"


def test_generate_js_expression__attribute():
    js_node = js_ast.JSAttribute(js_ast.JSName('foo'), 'bar')
    result = generate_js_expression(js_node)
    assert result == 'foo.bar'


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


def test_generate_arg():
    js_node = js_ast.JSArg('arg')

    result = generate_js_arg(js_node)

    expected = 'arg'
    assert result == expected


def test_generate_arguments():
    js_node = js_ast.JSArguments([js_ast.JSArg('a'), js_ast.JSArg('b')])

    result = generate_js_arguments(js_node)

    expected = 'a, b'
    assert result == expected


def test_generate_arguments__universal():
    py_node = _create_arguments_node(['a', 'b'], [ast.Constant(value=1)], 'arg',
                                     ['c', 'd'], [None, ast.Constant(value=1)], 'kwargs')
    js_node = transpile_arguments(py_node)

    result = generate_js_arguments(js_node)

    expected = 'a, b=1, kwargs, ...arg'
    assert result == expected


def test_generate_arguments__none():
    js_node = js_ast.JSArguments(None)
    result = generate_js_arguments(js_node)
    assert result == ''


def test_generate_return():
    js_node = js_ast.JSReturn(js_ast.JSConstant(100))

    result = generate_js_return(js_node)

    expected = 'return 100;'
    assert result == expected


def test_generate_js_eq():
    js_node = js_ast.JSEq()
    result = generate_js_eq(js_node)
    assert result == '==='


def test_generate_code_block__if_with_else():
    node = js_ast.JSIf(
        test=js_ast.JSConstant(value=True),
        body=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
        orelse=[js_ast.JSCodeExpression(js_ast.JSConstant(2))],
    )

    result = generate_code_block([node])

    expected = '''{
    if (true) {
        a;
    } else {
        2;
    }
}'''
    assert result == expected


def test_generate_code_block__try_catch_finally():
    node = js_ast.JSTry(
        body=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
        catch=[js_ast.JSIf(
            test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSConstant('Exception')),
            body=[js_ast.JSCodeExpression(js_ast.JSName('b'))],
            orelse=[js_ast.JSIf(
                test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSConstant('AttributeError')),
                body=[js_ast.JSCodeExpression(js_ast.JSName('c'))],
                orelse=[js_ast.JSCodeExpression(js_ast.JSName('d'))]
            )]
        )],
        finalbody=[js_ast.JSCodeExpression(js_ast.JSName('e'))],
    )

    result = generate_code_block([node])

    expected = '''{
    try {
        a;
    } catch (e) {
        if (e.name === 'Exception') {
            b;
        } else {
            if (e.name === 'AttributeError') {
                c;
            } else {
                d;
            }
        }
    } finally {
        e;
    }
}'''
    assert result == expected


def test_generate_code_block__with_error():
    node = js_ast.JSCodeExpression(js_ast.JSAdd())

    with pytest.raises(UnsupportedNode):
        generate_code_block([node])

    assert generator.code_block_indent == 0


def test_generate_js_dict__empty():
    js_node = js_ast.JSDict(keys=None, values=None)
    result = generate_js_dict(js_node)
    assert result == "{}"


def test_generate_expression_list__empty():
    result = generate_expression_list(None)
    assert result == []


def test_generate_js_assign__to_subscript():
    js_node = js_ast.JSAssign(
        target=js_ast.JSSubscript(js_ast.JSName('a'), js_ast.JSName('c')),
        value=js_ast.JSConstant(1),
    )

    result = generate_js_assign(js_node)

    assert result == "a[c] = 1;"


def test_generate_js_module():
    js_node = js_ast.JSModule(body=[js_ast.JSCodeExpression(js_ast.JSName('a'))])
    result = generate_js_module(js_node)
    assert result == 'a;'


def test_generate_js_module_with_export():
    js_node = js_ast.JSModule(body=[js_ast.JSCodeExpression(js_ast.JSName('a'))])
    js_node.export = js_ast.JSExport(['a'])

    result = generate_js_module(js_node)

    assert result == 'export {a};\n\na;'


def test_generate_js_statement__let():
    js_node = js_ast.JSLet(assign=js_ast.JSAssign(
        target=js_ast.JSName(id='v'),
        value=js_ast.JSConstant(value=2)
    ))

    result = generate_js_statement(js_node)

    assert result == 'let v = 2;'


def test_generate_js_statement__import():
    js_node = js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')])
    result = generate_js_statement(js_node)
    assert result == "import {a as var_a, foo} from './test.js';"


def test_generate_js_statement__import_all():
    js_node = js_ast.JSImport('test', names=[])
    result = generate_js_statement(js_node)
    assert result == "import * as test from './test.js';"


def test_generate_js_statement__import_all_as():
    js_node = js_ast.JSImport('test2', names=[], alias='bar')
    result = generate_js_statement(js_node)
    assert result == "import * as bar from './test2.js';"


def test_generate_js_statement__class_def():
    js_node = js_ast.JSClassDef(name='A', body=[])
    result = generate_js_statement(js_node)
    assert result == "class A {\n}"
