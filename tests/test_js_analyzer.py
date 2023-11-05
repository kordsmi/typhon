import copy

from typhon import js_ast
from typhon.js_analyzer import transform_module, BodyTransformer, NodeInfo, ClassTransformer
from typhon.transpiler import Transpiler


def test_transform_module():
    js_module = js_ast.JSModule(body=[
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
        js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant('test')),
        js_ast.JSFunctionDef('foo', js_ast.JSArguments(), []),
    ])

    js_module = transform_module(js_module) or js_module

    assert js_module.export == js_ast.JSExport(['a', 'b', 'foo'])


def test_transform_module__insert_let():
    original_body = [
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant('test')),
    ]
    js_module = js_ast.JSModule(body=copy.deepcopy(original_body))

    js_module = transform_module(js_module) or js_module

    assert js_module.export == js_ast.JSExport(['a'])
    assert js_module.body[0] == js_ast.JSLet(original_body[0])
    assert js_module.body[1] == original_body[1]


def test_transform_module__export_imports():
    js_module = js_ast.JSModule(body=[
        js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')]),
    ])

    js_module = transform_module(js_module) or js_module

    assert js_module.export == js_ast.JSExport(['var_a', 'foo'])


def test_transform_module__export_imports__all():
    js_module = js_ast.JSModule(body=[js_ast.JSImport('test', names=[])])
    js_module = transform_module(js_module) or js_module
    assert js_module.export == js_ast.JSExport(['test'])


def test_transform_module__export_class_names():
    js_module = js_ast.JSModule(body=[js_ast.JSClassDef(name='TestClass', body=[])])
    js_module = transform_module(js_module) or js_module
    assert js_module.export == js_ast.JSExport(['TestClass'])


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
    body_transformer.alias_list['b'].append(NodeInfo(
        js_ast.JSAssign(target=js_ast.JSName('b'), value=js_ast.JSConstant('foo')), -1,
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
        transpiler = Transpiler(code)
        transpiler.parse()
        transpiler.transpile_src()
        body_transformer = BodyTransformer(transpiler.js_tree.body)

        body_transformer.transform()

        assert list(body_transformer.alias_list.keys()) == ['a']
        assert body_transformer.alias_list['a'] == [NodeInfo(
            node=js_ast.JSAssign(js_ast.JSAttribute(js_ast.JSName('a'), '__ty_alias__'), js_ast.JSConstant('b')),
            index=-1
        )]

    def test_rename_variables_to_aliases(self):
        code = '''a.__ty_alias__ = 'b'
a = 123
a()
c = a'''
        transpiler = Transpiler(code)
        transpiler.parse()
        transpiler.transpile_src()
        body_transformer = BodyTransformer(transpiler.js_tree.body)

        body_transformer.transform()

        expected = [
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(123))),
            js_ast.JSCodeExpression(js_ast.JSCall(js_ast.JSName('b'))),
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSName('b'))),
        ]
        assert body_transformer.body == expected
