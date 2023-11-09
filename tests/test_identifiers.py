from typhon import js_ast
from typhon.identifires import Identifiers, IDInfo, ID_VAR, ID_CLASS, ID_FUNCTION, ID_IMPORT, ContextIdentifiers


class TestIdentifiers:
    def test_add_var(self):
        identifiers = Identifiers()
        js_assign = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100))

        identifiers.add(js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100)))

        assert identifiers.identifiers == {'a': IDInfo('a', js_assign, ID_VAR)}

    def test_add_class(self):
        identifiers = Identifiers()
        js_class_def = js_ast.JSClassDef(name='Foo', body=[])

        identifiers.add(js_class_def)

        assert identifiers.identifiers == {'Foo': IDInfo('Foo', js_class_def, ID_CLASS)}

    def test_add_func(self):
        identifiers = Identifiers()
        js_func_def = js_ast.JSFunctionDef(name='test_func', args=js_ast.JSArguments(), body=[])

        identifiers.add(js_func_def)

        assert identifiers.identifiers == {'test_func': IDInfo('test_func', js_func_def, ID_FUNCTION)}

    def test_add_import(self):
        identifiers = Identifiers()
        js_import = js_ast.JSImport(module='test_module', names=[js_ast.JSAlias(name='var1')])

        identifiers.add(js_import, 'var1')

        assert identifiers.identifiers == {'var1': IDInfo('var1', js_import, ID_IMPORT)}


class TestContextIdentifiers:
    def test_set_var_to_local_zone(self):
        global_ids = Identifiers()
        context_ids = Identifiers()
        assign_node = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(100))
        func_node = js_ast.JSFunctionDef('a', js_ast.JSArguments(), [])
        import_node = js_ast.JSImport(module='foo', names=[js_ast.JSAlias('a')])
        global_ids.add(assign_node)
        context_ids.add(func_node)
        context = ContextIdentifiers(global_ids, context_ids)
        context.add(import_node, 'a')
        assert context.locals.identifiers == {'a': IDInfo('a', import_node, ID_IMPORT)}

    def test_get_id_info(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(30))
        context = ContextIdentifiers()

        assert context.get_id_info('a') is None

        context.globals.add(assign_node_1)
        assert context.get_id_info('a') == IDInfo('a', assign_node_1, ID_VAR)

        context.context.add(assign_node_2)
        assert context.get_id_info('a') == IDInfo('a', assign_node_2, ID_VAR)

        context.add(assign_node_3)
        assert context.get_id_info('a') == IDInfo('a', assign_node_3, ID_VAR)

    def test_get_id_list__empty(self):
        context = ContextIdentifiers()
        assert context.get_id_list() == []

    def test_get_id_list(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(30))
        assign_node_4 = js_ast.JSAssign(js_ast.JSName('d'), js_ast.JSConstant(40))
        context = ContextIdentifiers()
        context.globals.add(assign_node_1)
        context.globals.add(assign_node_3)
        context.context.add(assign_node_2)
        context.locals.add(assign_node_3)
        context.locals.add(assign_node_4)

        assert context.get_id_list() == ['a', 'c', 'b', 'd']

    def test_get_local_context_ids(self):
        assign_node_1 = js_ast.JSAssign(js_ast.JSName('a'), js_ast.JSConstant(10))
        assign_node_2 = js_ast.JSAssign(js_ast.JSName('b'), js_ast.JSConstant(20))
        assign_node_3 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(30))
        assign_node_4 = js_ast.JSAssign(js_ast.JSName('c'), js_ast.JSConstant(40))
        context = ContextIdentifiers()
        context.globals.add(assign_node_1)
        context.globals.add(assign_node_3)
        context.context.add(assign_node_2)
        context.context.add(assign_node_3)
        context.locals.add(assign_node_4)

        local_context_ids = context.get_local_context_ids()

        assert local_context_ids.get_id_list() == ['b', 'c']
        assert local_context_ids.get_id_info('b') == IDInfo('b', assign_node_2, ID_VAR)
        assert local_context_ids.get_id_info('c') == IDInfo('c', assign_node_4, ID_VAR)
