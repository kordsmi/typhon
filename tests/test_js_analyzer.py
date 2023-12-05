import ast

from typhon import js_ast
from typhon.identifires import ObjectInfo, ID_VAR, NoName
from typhon.js_analyzer import BodyTransformer, ClassTransformer
from typhon.transpiler import transpile_module


def test_transform_body__transform_class_method():
    class_body = [js_ast.JSFunctionDef(name='foo', args=js_ast.JSArguments(args=[js_ast.JSArg(arg='self')]), body=[])]
    js_node = js_ast.JSClassDef(name='A', body=class_body)

    body_transformer = BodyTransformer([js_node])
    new_body = body_transformer.transform()

    expected_body = [js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=[])]
    assert new_body[0] == js_ast.JSClassDef(name='A', body=expected_body)


def test_transform_body__transform_call_to_new():
    js_body = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSCall(func=js_ast.JSName('TestClass')),
    ]

    body_transformer = BodyTransformer(js_body)
    new_body = body_transformer.transform()

    expected = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSNew(class_=js_ast.JSName('TestClass')),
    ]
    assert new_body == expected


def test_transform_function_to_method__replace_self_to_this():
    func_body = [js_ast.JSAssign(
        js_ast.JSAttribute(js_ast.JSName('self'), 'a'),
        js_ast.JSAttribute(js_ast.JSName('self'), 'b'),
    )]
    func_def = js_ast.JSFunctionDef(
        name='foo',
        args=js_ast.JSArguments(args=[js_ast.JSArg(arg='self')]),
        body=func_body
    )

    class_transformer = ClassTransformer(None)
    result = class_transformer.visit_JSFunctionDef(func_def)

    method_body = [js_ast.JSAssign(
        js_ast.JSAttribute(js_ast.JSName('this'), 'a'),
        js_ast.JSAttribute(js_ast.JSName('this'), 'b'),
    )]
    method_def = js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=method_body)
    assert result == method_def


def test_transform_function_to_method__constructor():
    func_def = js_ast.JSFunctionDef(name='__init__', args=js_ast.JSArguments(), body=[])

    class_transformer = ClassTransformer(None)
    result = class_transformer.visit_JSFunctionDef(func_def)

    assert result == js_ast.JSMethodDef(name='constructor', args=js_ast.JSArguments(), body=[])


def test_replace_in_body__replace_call_args():
    body = [
        js_ast.JSCodeExpression(js_ast.JSCall(
            func=js_ast.JSName('a'),
            args=[js_ast.JSName(id='a'), js_ast.JSName(id='b')],
            keywords=[
                js_ast.JSKeyWord(arg='c', value=js_ast.JSName('b')),
                js_ast.JSKeyWord(arg='b', value=js_ast.JSName('d')),
            ]
        ))
    ]

    body_transformer = BodyTransformer(body)
    body_transformer.alias_list['b'].append(ObjectInfo(
        'b',
        js_ast.JSAssign(target=js_ast.JSName('b'), value=js_ast.JSConstant('foo')),
        ID_VAR,
    ))
    result = body_transformer.transform()

    expected = [
        js_ast.JSCodeExpression(js_ast.JSCall(
            func=js_ast.JSName('a'),
            args=[js_ast.JSName(id='a'), js_ast.JSName(id='foo')],
            keywords=[
                js_ast.JSKeyWord(arg='c', value=js_ast.JSName('foo')),
                js_ast.JSKeyWord(arg='b', value=js_ast.JSName('d')),
            ]
        ))
    ]
    assert result == expected


class TestBodyTransformer:
    def test_collect_typhon_aliases(self):
        code = 'a.__ty_alias__ = "b"'
        py_tree = ast.parse(code)
        js_tree = transpile_module(py_tree)
        body_transformer = BodyTransformer(js_tree.body)

        body_transformer.transform()

        assert list(body_transformer.alias_list.keys()) == ['a']
        assert body_transformer.alias_list['a'] == [ObjectInfo(
            NoName,
            node=js_ast.JSAssign(js_ast.JSAttribute(js_ast.JSName('a'), '__ty_alias__'), js_ast.JSConstant('b')),
            object_type=ID_VAR,
        )]

    def test_rename_variables_to_aliases(self):
        code = '''a.__ty_alias__ = 'b'
a = 123
a()
c = a'''
        py_tree = ast.parse(code)
        js_tree = transpile_module(py_tree)
        body_transformer = BodyTransformer(js_tree.body)

        body_transformer.transform()

        expected = [
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(123))),
            js_ast.JSCodeExpression(js_ast.JSCall(js_ast.JSName('b'))),
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSName('b'))),
        ]
        assert body_transformer.body == expected
