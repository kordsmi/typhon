import copy

from typhon import js_ast
from typhon.js_analyzer import transform_module, transform_function_to_method, replace_in_body, BodyTransformer


def test_transform_module():
    js_module = js_ast.JSModule(body=[
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
        js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant('test')),
        js_ast.JSFunctionDef('foo', js_ast.JSArguments(), []),
    ])

    transform_module(js_module)

    assert js_module.export == js_ast.JSExport(['a', 'b', 'foo'])


def test_transform_module__insert_let():
    original_body = [
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant('test')),
    ]
    js_module = js_ast.JSModule(body=copy.deepcopy(original_body))

    transform_module(js_module)

    assert js_module.export == js_ast.JSExport(['a'])
    assert js_module.body[0] == js_ast.JSLet(original_body[0])
    assert js_module.body[1] == original_body[1]


def test_transform_module__export_imports():
    js_module = js_ast.JSModule(body=[
        js_ast.JSImport('test', names=[js_ast.JSAlias('a', 'var_a'), js_ast.JSAlias('foo')]),
    ])

    transform_module(js_module)

    assert js_module.export == js_ast.JSExport(['var_a', 'foo'])


def test_transform_module__export_imports__all():
    js_module = js_ast.JSModule(body=[js_ast.JSImport('test', names=[])])
    transform_module(js_module)
    assert js_module.export == js_ast.JSExport(['test'])


def test_transform_module__export_class_names():
    js_module = js_ast.JSModule(body=[js_ast.JSClassDef(name='TestClass', body=[])])
    transform_module(js_module)
    assert js_module.export == js_ast.JSExport(['TestClass'])


def test_transform_body__transform_class_method():
    class_body = [js_ast.JSFunctionDef(name='foo', args=js_ast.JSArguments(args=[js_ast.JSArg(arg='self')]), body=[])]
    js_node = js_ast.JSClassDef(name='A', body=class_body)

    body_transformer = BodyTransformer([js_node])
    body_transformer.transform()

    expected_body = [js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=[])]
    assert js_node == js_ast.JSClassDef(name='A', body=expected_body)


def test_transform_body__transform_call_to_new():
    js_body = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSCall(func='TestClass'),
    ]

    body_transformer = BodyTransformer(js_body)
    body_transformer.transform()

    expected = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSNew(class_=js_ast.JSName('TestClass')),
    ]
    assert js_body == expected


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

    result = transform_function_to_method(func_def)

    method_body = [js_ast.JSAssign(
        js_ast.JSAttribute(js_ast.JSName('this'), 'a'),
        js_ast.JSAttribute(js_ast.JSName('this'), 'b'),
    )]
    method_def = js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=method_body)
    assert result == method_def


def test_transform_function_to_method__constructor():
    func_def = js_ast.JSFunctionDef(name='__init__', args=js_ast.JSArguments(), body=[])
    result = transform_function_to_method(func_def)
    assert result == js_ast.JSMethodDef(name='constructor', args=js_ast.JSArguments(), body=[])


def test_replace_in_body__replace_call_args():
    body = [
        js_ast.JSCodeExpression(js_ast.JSCall(
            func='a',
            args=[js_ast.JSName(id='a'), js_ast.JSName(id='b')],
            keywords=[
                js_ast.JSKeyWord(arg='c', value=js_ast.JSName('b')),
                js_ast.JSKeyWord(arg='b', value=js_ast.JSName('d')),
            ]
        ))
    ]

    result = replace_in_body(body, js_ast.JSName('b'), js_ast.JSName('foo'))

    expected = [
        js_ast.JSCodeExpression(js_ast.JSCall(
            func='a',
            args=[js_ast.JSName(id='a'), js_ast.JSName(id='foo')],
            keywords=[
                js_ast.JSKeyWord(arg='c', value=js_ast.JSName('foo')),
                js_ast.JSKeyWord(arg='b', value=js_ast.JSName('d')),
            ]
        ))
    ]
    assert result == expected
