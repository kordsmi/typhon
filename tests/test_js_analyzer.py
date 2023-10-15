import copy

from typhon import js_ast
from typhon.js_analyzer import transform_module


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
