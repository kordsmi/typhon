from typhon import js_ast
from typhon.js_analyzer import get_module_info


def test_get_module_info():
    js_module = js_ast.JSModule(body=[
        js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)),
        js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant('test')),
        js_ast.JSFunctionDef('foo', js_ast.JSArguments(), []),
    ])

    info = get_module_info(js_module)

    assert info == ['a', 'b', 'foo']
