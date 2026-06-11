import ast

from typhon.object_collector import (
    ObjectArgument,
    ObjectCollector,
    ObjectConstant,
    ObjectFunction,
    ObjectModule,
    ObjectReference,
    ObjectClass,
    ObjectInfo,
)
from typhon.types import ModulePath

source_code = """
import module_a
import module_c as mc
from module_b import var_b, var_a as va

a = 1
b = a
c = d = 3
e, (f, g) = b, (c, 4)
TEXT = 'text'

class Demo:
    info = 'test'
    
    def __init__(self):
        self.name = 'demo'

def outer_func(x: int, y: int = 0):
    global a
    nonlocal b
    a = 2
    b = 3
    c = 4
    
    def inner_func(a: int, *, b: str = ''):
        class InnerDemoClass(Demo):
            info = 'example'
            
            def method(self, x: int):
                pass
    
        c = 10
        return b + a
    
    return inner_func(x) + y
    
res = outer_func(10, 20)
"""


class TestObjectCollector:
    def test_collect_module_objects(self):
        """Большой тест на сбор объектов модуля из разных частей кода."""

        tree = ast.parse(source_code)
        collector = ObjectCollector(ObjectModule(ModulePath('__main__')))

        collector.visit(tree)

        inner_class = ObjectClass('InnerDemoClass')
        class_method = ObjectFunction('method')
        inner_class.add_object('info', ObjectConstant('example'))
        inner_class.add_object('method', class_method)
        class_method.locals.add_object('self', ObjectArgument())
        class_method.locals.add_object('x', ObjectArgument())

        inner_function = ObjectFunction('inner_func')
        inner_function.locals.add_object('a', ObjectArgument())
        inner_function.locals.add_object('b', ObjectArgument())
        inner_function.locals.add_object('InnerDemoClass', inner_class)
        inner_function.locals.add_object('c', ObjectConstant(10))

        outer_function = ObjectFunction('outer_func')
        outer_function.locals.add_object('x', ObjectArgument())
        outer_function.locals.add_object('y', ObjectArgument())
        outer_function.locals.add_object('a', ObjectConstant(2))
        outer_function.locals.add_object('b', ObjectConstant(3))
        outer_function.locals.add_object('c', ObjectConstant(4))
        outer_function.locals.add_object('inner_func', inner_function)

        init_method = ObjectFunction('__init__')
        init_method.locals.add_object('self', ObjectArgument())

        class_demo = ObjectClass('Demo')
        class_demo.add_object('info', ObjectConstant('test'))
        class_demo.add_object('__init__', init_method)

        expected = {
            'module_a': ObjectReference('module_a'),
            'mc': ObjectReference('module_c'),
            'var_b': ObjectReference('module_b.var_b'),
            'va': ObjectReference('module_b.var_a'),
            'a': ObjectConstant(1),
            'b': ObjectReference('a'),
            'c': ObjectConstant(3),
            'd': ObjectConstant(3),
            'e': ObjectReference('b'),
            'f': ObjectReference('c'),
            'g': ObjectConstant(4),
            'TEXT': ObjectConstant('text'),
            'Demo': class_demo,
            'outer_func': outer_function,
            'res': None,
        }

        assert collector.object_info.objects == expected
        assert collector.object_info.objects['outer_func'].locals == outer_function.locals

    def test_objects_in_class_def(self):
        class_def = ast.ClassDef(name='Foo', bases=[], keywords=[], body=[
            ast.Assign([ast.Name('var')], ast.Constant(123)),
            ast.FunctionDef(
                name='test_method',
                args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=[], decorator_list=[], type_params=[],
            ),
        ], decorator_list=[], type_params=[])
        root_object = ObjectInfo()

        object_collector = ObjectCollector(root_object)
        object_collector.visit(class_def)

        foo_object = ObjectClass('Foo')
        foo_object.objects = {
            'var': ObjectConstant(123),
            'test_method': ObjectFunction('test_method'),
        }
        root_object.objects['Foo'] = foo_object

        assert root_object.objects == {'Foo': foo_object}

    def test_create_object_reference_on_assign(self):
        body = [
            ast.Assign(
                [ast.Name('b')],
                ast.Constant('test'),
            ),
            ast.Assign(
                [ast.Name('a')],
                ast.Name('b'),
            ),
            ast.Assign(
                [ast.Name('c')],
                ast.Name('a'),
            ),
        ]
        root_object = ObjectInfo()

        object_collector = ObjectCollector(root_object)
        object_collector.visit_body(body)

        assert root_object.objects == {
            'a': ObjectReference('b'),
            'b': ObjectConstant('test'),
            'c': ObjectReference('a'),
        }
