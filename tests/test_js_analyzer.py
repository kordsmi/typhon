import ast

from typhon import js_ast
from typhon.generator import generate_js_body
from typhon.js_analyzer import BodyTransformer, ClassTransformer
from typhon.module_transpiler import ModuleTranspiler
from typhon.object_collector import ObjectInfo, ObjectClass, ObjectConstant, ObjectFunction, ObjectModule
from typhon.transpiler import convert_ast
from typhon.types import ModulePath


def test_transform_body__transform_class_method():
    class_body = [js_ast.JSFunctionDef(name='foo', args=js_ast.JSArguments(args=[js_ast.JSArg(arg='self')]), body=[])]
    js_node = js_ast.JSClassDef(name='A', body=class_body)

    body_transformer = BodyTransformer([js_node], [], ObjectInfo())
    new_body = body_transformer.transform()

    expected_body = [js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=[])]
    assert new_body[0] == js_ast.JSClassDef(name='A', body=expected_body)


def test_transform_body__transform_call_to_new():
    js_body = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSCall(func=js_ast.JSName('TestClass')),
    ]

    root_object = ObjectInfo()
    root_object.objects['TestClass'] = ObjectClass('TestClass')
    body_transformer = BodyTransformer(js_body, [], root_object)
    new_body = body_transformer.transform()

    expected = [
        js_ast.JSClassDef(name='TestClass', body=[]),
        js_ast.JSNew(class_=js_ast.JSName('TestClass')),
    ]
    assert new_body == expected


def test_transform_function_to_method__replace_self_to_this():
    func_body = [
        js_ast.JSAssign(
            js_ast.JSAttribute(js_ast.JSName('self'), 'b'),
            js_ast.JSConstant(100),
        ),
        js_ast.JSAssign(
            js_ast.JSAttribute(js_ast.JSName('self'), 'a'),
            js_ast.JSAttribute(js_ast.JSName('self'), 'b'),
        )
    ]
    func_def = js_ast.JSFunctionDef(
        name='foo',
        args=js_ast.JSArguments(args=[js_ast.JSArg(arg='self')]),
        body=func_body
    )

    root_object = ObjectInfo()
    self_object = ObjectInfo(object_value='self')
    self_object.objects['__ty_alias__'] = ObjectConstant('this')
    foo_object = ObjectFunction('foo')
    foo_object.locals.objects['self'] = self_object
    root_object.objects['foo'] = foo_object

    class_transformer = ClassTransformer(None, [], root_object)
    result = class_transformer.visit_JSFunctionDef(func_def)

    method_body = [
        js_ast.JSAssign(
            js_ast.JSAttribute(js_ast.JSName('this'), 'b'),
            js_ast.JSConstant(100),
        ),
        js_ast.JSAssign(
            js_ast.JSAttribute(js_ast.JSName('this'), 'a'),
            js_ast.JSAttribute(js_ast.JSName('this'), 'b'),
        )
    ]
    method_def = js_ast.JSMethodDef(name='foo', args=js_ast.JSArguments(args=[]), body=method_body)
    assert result == method_def


def test_transform_function_to_method__constructor():
    func_def = js_ast.JSFunctionDef(name='__init__', args=js_ast.JSArguments(), body=[])

    root_object = ObjectInfo(None)
    class_transformer = ClassTransformer(None, [], root_object)
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

    root_object = ObjectInfo(None)
    body_transformer = BodyTransformer(body, [], root_object)
    alias_b = ObjectInfo(None)
    alias_b.objects['__ty_alias__'] = ObjectConstant('foo')
    body_transformer.context_vars.objects['b'] = alias_b
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
        js_tree = convert_ast(py_tree)
        root_object = ObjectInfo()
        root_object.objects['a'] = ObjectInfo(object_value='a')
        body_transformer = BodyTransformer(js_tree.body, [], root_object)

        body_transformer.transform()

        expected = ObjectInfo(object_value='a')
        expected.objects['__ty_alias__'] = ObjectConstant('b')
        assert body_transformer.context_vars.objects['a'] == expected

    def test_rename_variables_to_aliases(self):
        code = '''a.__ty_alias__ = 'b'
a = 123
a()
c = a'''
        py_tree = ast.parse(code)
        js_tree = convert_ast(py_tree)
        root_object = ObjectInfo()
        root_object.objects['a'] = ObjectInfo()
        body_transformer = BodyTransformer(js_tree.body, [], root_object)

        body_transformer.transform()

        expected = [
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(123))),
            js_ast.JSCodeExpression(js_ast.JSCall(js_ast.JSName('b'))),
            js_ast.JSLet(js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSName('b'))),
        ]
        assert body_transformer.body == expected

    def test_call_new_for_class_from_imported_module(self):
        source_1 = 'import test\ntest.A()'
        source_2 = 'class A:\n    pass'

        root_object = ObjectModule(ModulePath('__main__'))
        module_test = ObjectModule(ModulePath('test'))
        module_test.objects['A'] = ObjectClass('A')
        root_object.objects['test'] = module_test
        test_module_transpiler = ModuleTranspiler(source_2, root_object, ModulePath('test'))
        test_module_transpiler.transpile()

        py_tree = ast.parse(source_1)
        js_tree = convert_ast(py_tree)
        body_transformer = BodyTransformer(js_tree.body, [], root_object)
        body_transformer.transform()
        main_js_code = generate_js_body(body_transformer.body)

        assert main_js_code == "import * as test from './test.js';\nnew test.A();"

    def test_call_new_for_class_as_attribute(self):
        js_body = [
            js_ast.JSClassDef(name='A', body=[]),
            js_ast.JSClassDef(name='B', body=[
                js_ast.JSAssign(js_ast.JSName('a'), value=js_ast.JSName('A')),
            ]),
            js_ast.JSCall(func=js_ast.JSAttribute(js_ast.JSName('B'), 'a')),
        ]

        root_object = ObjectInfo()
        object_class_a = ObjectClass('A')
        object_class_b = ObjectClass('B')
        object_class_b.objects['a'] = object_class_a
        root_object.objects = {'A': object_class_a, 'B': object_class_b}
        body_transformer = BodyTransformer(js_body, [], root_object)
        new_body = body_transformer.transform()

        expected = [
            js_ast.JSClassDef(name='A', body=[]),
            js_ast.JSClassDef(name='B', body=[
                js_ast.JSAssign(js_ast.JSName('a'), value=js_ast.JSName('A')),
            ]),
            js_ast.JSNew(class_=js_ast.JSAttribute(js_ast.JSName('B'), 'a')),
        ]
        assert new_body == expected
