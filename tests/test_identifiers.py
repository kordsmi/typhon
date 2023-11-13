from typhon import js_ast
from typhon.identifires import ObjectInfo, ID_VAR, ID_CLASS, ID_FUNCTION, ID_IMPORT, ContextObjects, get_object_info


class TestIdentifiers:
    def test_add_var(self):
        identifiers = {}
        js_assign = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100))

        identifiers['a'] = get_object_info(js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)))

        assert identifiers == {'a': ObjectInfo('a', js_assign, ID_VAR)}

    def test_add_class(self):
        identifiers = {}
        js_class_def = js_ast.JSClassDef(name='Foo', body=[])

        identifiers['Foo'] = get_object_info(js_class_def)

        assert identifiers == {'Foo': ObjectInfo('Foo', js_class_def, ID_CLASS)}

    def test_add_func(self):
        identifiers = {}
        js_func_def = js_ast.JSFunctionDef(name='test_func', args=js_ast.JSArguments(), body=[])

        identifiers['test_func'] = get_object_info(js_func_def)

        assert identifiers == {'test_func': ObjectInfo('test_func', js_func_def, ID_FUNCTION)}

    def test_add_import(self):
        identifiers = {}
        js_import = js_ast.JSImport(module='test_module', names=[js_ast.JSAlias(name='var1')])

        identifiers['var1'] = get_object_info(js_import, 'var1')

        assert identifiers == {'var1': ObjectInfo('var1', js_import, ID_IMPORT)}


class TestContextIdentifiers:
    def test_set_var_to_local_zone(self):
        global_ids = {}
        context_ids = {}
        assign_node = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100))
        func_node = js_ast.JSFunctionDef('a', js_ast.JSArguments(), [])
        import_node = js_ast.JSImport(module='foo', names=[js_ast.JSAlias('a')])
        global_ids['a'] = get_object_info(assign_node)
        context_ids['a'] = get_object_info(func_node)
        context = ContextObjects(global_ids, context_ids)
        context.add(import_node, 'a')
        assert context.locals == {'a': ObjectInfo('a', import_node, ID_IMPORT)}

    def test_get_id_info(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(30))
        context = ContextObjects()

        assert context.get_id_info('a') is None

        context.globals['a'] = get_object_info(assign_node_1)
        assert context.get_id_info('a') == get_object_info(assign_node_1)

        context.context['a'] = get_object_info(assign_node_2)
        assert context.get_id_info('a') == get_object_info(assign_node_2)

        context.locals['a'] = get_object_info(assign_node_3)
        assert context.get_id_info('a') == get_object_info(assign_node_3)

    def test_get_id_list__empty(self):
        context = ContextObjects()
        assert context.get_id_list() == []

    def test_get_id_list(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(30))
        assign_node_4 = js_ast.JSAssign(js_ast.JSName('d'), js_ast.JSConstant(40))
        context = ContextObjects()
        context.globals['a'] = get_object_info(assign_node_1)
        context.globals['c'] = get_object_info(assign_node_3)
        context.context['b'] = get_object_info(assign_node_2)
        context.locals['c'] = get_object_info(assign_node_3)
        context.locals['d'] = get_object_info(assign_node_4)

        assert context.get_id_list() == ['a', 'c', 'b', 'd']

    def test_get_local_context_ids(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(30))
        assign_node_4 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(40))
        context = ContextObjects()
        context.globals['a'] = get_object_info(assign_node_1)
        context.globals['c'] = get_object_info(assign_node_3)
        context.context['b'] = get_object_info(assign_node_2)
        context.context['c'] = get_object_info(assign_node_3)
        context.locals['c'] = get_object_info(assign_node_4)

        local_context_ids = context.get_local_context_ids()

        assert list(local_context_ids.keys()) == ['b', 'c']
        assert local_context_ids.get('b') == get_object_info(assign_node_2)
        assert local_context_ids.get('c') == get_object_info(assign_node_4)
