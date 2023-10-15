import ast

import pytest

from typhon import js_ast
from typhon.exceptions import InvalidNode
from typhon.transpiler import transpile, transpile_bin_op, transpile_call, transpile_assign, transpile_expression, \
    Transpiler, transpile_arg, transpile_arguments, transpile_statement, transpile_function_def, transpile_return, \
    transpile_arg_list, transpile_expression_list, transpile_body, transpile_constant, transpile_eq, transpile_module


def test_transpiler():
    py_str = 'print(1 + 2)'
    js_str = 'export {};\n\nconsole.log(1 + 2);'

    result = transpile(py_str)

    assert result == js_str


class TestTranspiler:
    def test_transpile_multiple_expressions(self):
        src = '''a = 1
print('a + 2 = ', a + 2)'''
        transpiler = Transpiler(src)
        transpiler.parse()

        transpiler.transpile_src()

        expected = js_ast.JSModule(body=[
            js_ast.JSAssign(target=js_ast.JSName(id='a'), value=js_ast.JSConstant(value=1)),
            js_ast.JSCodeExpression(js_ast.JSCall(func='console.log', args=[
                js_ast.JSConstant(value='a + 2 = '),
                js_ast.JSBinOp(left=js_ast.JSName(id='a'), op=js_ast.JSAdd(), right=js_ast.JSConstant(value=2)),
            ]))
        ])
        assert transpiler.js_tree == expected

    def test_transpile_function(self):
        src = '''def foo(a):
    return a'''
        transpiler = Transpiler(src)
        transpiler.parse()

        transpiler.transpile_src()

        expected = js_ast.JSModule([transpile_function_def(transpiler.py_tree.body[0])])
        assert transpiler.js_tree == expected
        assert transpiler.js_tree.body[0].body[0] == transpile_return(transpiler.py_tree.body[0].body[0])


def test_transpile_set_variable__int():
    assign_node = _create_assign_statement('a', ast.Constant(value='sample'))

    result = transpile_assign(assign_node)

    expected = js_ast.JSAssign(
        target=js_ast.JSName('a'),
        value=js_ast.JSConstant('sample')
    )
    assert result == expected


def test_transpile_set_variable__expression():
    assign_node = _create_assign_statement(
        name='b',
        value=ast.BinOp(
            left=ast.Name(id='a', ctx=ast.Load()),
            op=ast.Add(),
            right=ast.Constant(value=3)
        )
    )

    result = transpile_assign(assign_node)

    expected = js_ast.JSAssign(
        target=js_ast.JSName('b'),
        value=transpile_bin_op(assign_node.value)
    )
    assert result == expected


def test_transpile_set_variable__to_subscript():
    assign_node = ast.Assign(
        targets=[ast.Subscript(value=ast.Name(id='a'), slice=ast.Name(id='c'), ctx=ast.Store())],
        value=ast.Constant(value=1),
    )

    result = transpile_assign(assign_node)

    expected = js_ast.JSAssign(
        target=js_ast.JSSubscript(js_ast.JSName('a'), js_ast.JSName('c')),
        value=js_ast.JSConstant(1),
    )
    assert result == expected


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


def test_transpile_expression__list():
    node = ast.List(elts=[ast.Constant(value=1), ast.Constant(value=2)])

    js_node = transpile_expression(node)

    expected = js_ast.JSList(elts=[js_ast.JSConstant(1), js_ast.JSConstant(2)])
    assert js_node == expected


def test_transpile_expression__tuple():
    node = ast.Tuple(elts=[ast.Constant(value=1), ast.Constant(value=2)])

    js_node = transpile_expression(node)

    expected = js_ast.JSList(elts=[js_ast.JSConstant(1), js_ast.JSConstant(2)])
    assert js_node == expected


def test_transpile_expression__set():
    node = ast.Set(elts=[ast.Constant(value=1), ast.Constant(value=2)])

    js_node = transpile_expression(node)

    expected = js_ast.JSList(elts=[js_ast.JSConstant(1), js_ast.JSConstant(2)])
    assert js_node == expected


def test_transpile_expression__dict():
    node = ast.Dict(
        keys=[ast.Constant(value='a'), ast.Constant(value='b')],
        values=[ast.Constant(value=1), ast.Constant(value=2)]
    )

    js_node = transpile_expression(node)

    expected = js_ast.JSDict(
        keys=[js_ast.JSConstant('a'), js_ast.JSConstant('b')],
        values=[js_ast.JSConstant(1), js_ast.JSConstant(2)]
    )
    assert js_node == expected


def test_transpile_expression__compare():
    node = ast.Compare(left=ast.Name(id='a'), ops=[ast.Eq()], comparators=[ast.Constant(value=1)])
    js_node = transpile_expression(node)
    assert js_node == js_ast.JSCompare(left=js_ast.JSName('a'), op=js_ast.JSEq(), right=js_ast.JSConstant(1))


def test_transpile_expression__subscript():
    node = ast.Subscript(value=ast.Name(id='a', ctx=ast.Load()), slice=ast.Constant(value='c'), ctx=ast.Store())
    js_node = transpile_expression(node)
    assert js_node == js_ast.JSSubscript(js_ast.JSName('a'), js_ast.JSConstant('c'))


def test_transpile_arg():
    node = ast.arg(arg='a')

    js_node = transpile_arg(node)

    expected = js_ast.JSArg(arg='a')
    assert js_node == expected


def test_transpile_arguments():
    node = _create_arguments_node(['a', 'b'])

    js_node = transpile_arguments(node)

    expected = js_ast.JSArguments(args=transpile_arg_list(node.args))
    assert js_node == expected


def test_transpile_arguments__kwargs_and_defaults():
    node = _create_arguments_node(['a', 'b'], [ast.Constant(value=1)], 'arg',
                                  ['c', 'd'], [None, ast.Constant(value=1)], 'kwargs')

    js_node = transpile_arguments(node)

    expected = js_ast.JSArguments(
        args=transpile_arg_list(node.args),
        defaults=transpile_expression_list(node.defaults),
        vararg=transpile_arg(node.vararg),
        kwonlyargs=transpile_arg_list(node.kwonlyargs),
        kw_defaults=transpile_expression_list(node.kw_defaults),
        kwarg=transpile_arg(node.kwarg),
    )
    assert js_node == expected


def _create_arguments_node(
        args: [str], defaults: [ast.expr] = None, vararg: str = None,
        kwonlyargs: [str] = None, kw_defaults: [ast.expr] = None, kwarg: str = None
) -> ast.arguments:
    defaults = defaults or []
    kwonlyargs = kwonlyargs or []
    kw_defaults = kw_defaults or []

    node_extra_params = {}
    arg_nodes = [ast.arg(arg=arg_name) for arg_name in args]
    kwonlyargs_nodes = [ast.arg(arg=arg_name) for arg_name in kwonlyargs]
    if vararg:
        node_extra_params['vararg'] = ast.arg(arg=vararg)
    if kwarg:
        node_extra_params['kwarg'] = ast.arg(arg=kwarg)
    return ast.arguments(
        posonlyargs=[],
        args=arg_nodes,
        kwonlyargs=kwonlyargs_nodes,
        kw_defaults=kw_defaults,
        defaults=defaults,
        **node_extra_params,
    )


def _create_assign_statement(name: str, value: ast.expr) -> ast.Assign:
    return ast.Assign(
        targets=[ast.Name(id=name, ctx=ast.Store())],
        value=value,
    )


def test_transpile_function_def():
    arguments_node = _create_arguments_node(['a'])
    assign_statement = _create_assign_statement('b', ast.Constant(value='sample'))
    node = ast.FunctionDef(name='foo', args=arguments_node, body=[assign_statement])

    js_node = transpile_function_def(node)

    expected = js_ast.JSFunctionDef(
        name='foo',
        args=transpile_arguments(arguments_node),
        body=[transpile_statement(assign_statement)]
    )
    assert js_node == expected


def test_transpile_return():
    node = ast.Return(value=ast.Constant(value=1))

    js_node = transpile_return(node)

    expected = js_ast.JSReturn(value=js_ast.JSConstant(value=1))
    assert js_node == expected


def test_transpile_statement__delete():
    node = ast.Delete(targets=[ast.Name(id='d')])
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSStatements([js_ast.JSDelete(target=js_ast.JSName(id='d'))])


def test_transpile_statement__delete_multiple():
    node = ast.Delete(targets=[ast.Name(id='d'), ast.Name(id='e')])

    js_node = transpile_statement(node)

    expected = js_ast.JSStatements([
        js_ast.JSDelete(target=js_ast.JSName(id='d')),
        js_ast.JSDelete(target=js_ast.JSName(id='e')),
    ])
    assert js_node == expected


def test_transpile_body__with_pass():
    body = [ast.Pass()]

    js_body = transpile_body(body)

    assert js_body == []


def test_transpile_body__statements():
    body = [ast.Delete(targets=[ast.Name(id='d'), ast.Name(id='e')])]
    js_body = transpile_body(body)
    assert js_body == [js_ast.JSDelete(js_ast.JSName('d')), js_ast.JSDelete(js_ast.JSName('e'))]


def test_transpile_statement__while():
    node = ast.While(test=ast.Constant(value=True), body=[ast.Pass()])

    js_node = transpile_statement(node)

    expected = js_ast.JSWhile(test=js_ast.JSConstant(value=True), body=[])
    assert js_node == expected


def test_transpile_statement__while_else():
    node = ast.While(
        test=ast.Constant(value=True),
        body=[ast.Pass()],
        orelse=[ast.Expr(ast.Name(id='a', ctx=ast.Load()))],
    )

    js_node = transpile_statement(node)

    expected = js_ast.JSWhile(
        test=js_ast.JSConstant(value=True),
        body=[],
        orelse=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
    )
    assert js_node == expected


def test_transpile_statement__if():
    node = ast.If(test=ast.Constant(value=True), body=[ast.Pass()], orelse=[ast.Pass()])

    js_node = transpile_statement(node)

    expected = js_ast.JSIf(test=js_ast.JSConstant(value=True), body=[], orelse=[])
    assert js_node == expected


def test_transpile_statement__raise():
    node = ast.Raise(exc=ast.Name(id='Exception', ctx=ast.Load()))

    js_node = transpile_statement(node)

    expected = js_ast.JSThrow(exc=js_ast.JSName('Exception'))
    assert js_node == expected


def test_transpile_statement__try():
    node = ast.Try(
        body=[ast.Expr(value=ast.Name(id='a', ctx=ast.Load()))],
        handlers=[
            ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                body=[ast.Expr(value=ast.Name(id='b', ctx=ast.Load()))]
            ),
            ast.ExceptHandler(
                type=ast.Name(id='AttributeError', ctx=ast.Load()),
                body=[ast.Expr(value=ast.Name(id='c', ctx=ast.Load()))]
            )
        ],
        orelse=[ast.Expr(value=ast.Name(id='d', ctx=ast.Load()))],
        finalbody=[ast.Expr(value=ast.Name(id='e', ctx=ast.Load()))]
    )

    js_node = transpile_statement(node)

    expected = js_ast.JSTry(
        body=[js_ast.JSCodeExpression(js_ast.JSName('a'))],
        catch=[js_ast.JSIf(
            test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSName('Exception')),
            body=[js_ast.JSCodeExpression(js_ast.JSName('b'))],
            orelse=[js_ast.JSIf(
                test=js_ast.JSCompare(js_ast.JSName('e.name'), js_ast.JSEq(), js_ast.JSName('AttributeError')),
                body=[js_ast.JSCodeExpression(js_ast.JSName('c'))],
                orelse=[js_ast.JSCodeExpression(js_ast.JSName('d'))]
            )]
        )],
        finalbody=[js_ast.JSCodeExpression(js_ast.JSName('e'))],
    )
    assert js_node == expected


def test_transpile_statement__continue():
    node = ast.Continue()
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSContinue()


def test_transpile_statement__break():
    node = ast.Break()
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSBreak()


def test_transpile_statement__import_from():
    node = ast.ImportFrom(module='test', names=[ast.alias(name='a', asname='var_a'), ast.alias(name='foo')])
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')])


def test_transpile_statement__import():
    node = ast.Import(names=[ast.alias(name='test')])
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSImport('test', names=[])


def test_transpile_statement__import_as():
    node = ast.Import(names=[ast.alias(name='test2', asname='bar')])
    js_node = transpile_statement(node)
    assert js_node == js_ast.JSImport('test2', names=[], alias='bar')


def test_transpile_constant__true():
    node = ast.Constant(value=True)
    js_node = transpile_constant(node)
    assert js_node == js_ast.JSConstant(value=True)


def test_transpile_eq():
    node = ast.Eq()
    js_node = transpile_eq(node)
    assert js_node == js_ast.JSEq()


def test_transpile_module():
    node = ast.Module(body=[ast.Expr(ast.Name(id='a', ctx=ast.Load()))])
    js_node = transpile_module(node)
    assert js_node == js_ast.JSModule(body=[js_ast.JSCodeExpression(js_ast.JSName('a'))])
