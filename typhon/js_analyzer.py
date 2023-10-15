from typhon import js_ast


def transform_module(js_module: js_ast.JSModule):
    info = get_identifies_from_code_block(js_module.body)
    js_module.export = js_ast.JSExport(info)
    transform_body(js_module.body)


def get_identifies_from_code_block(body: [js_ast.JSStatement]):
    info = []

    def add_name(name: str):
        if name not in info:
            info.append(name)

    for node in body:
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            add_name(node.target.id)
        elif isinstance(node, js_ast.JSFunctionDef):
            add_name(node.name)
        elif isinstance(node, js_ast.JSImport):
            if node.names:
                for alias in node.names:
                    info.append(alias.asname or alias.name)
            else:
                info.append(node.alias or node.module)

    return info


def transform_body(body: [js_ast.JSStatement]):
    names = []

    for i in range(len(body)):
        node = body[i]
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            name = node.target.id
            if name not in names:
                names.append(name)
                body[i] = js_ast.JSLet(node)
        elif isinstance(node, js_ast.JSClassDef):
            transform_class(node)


def transform_class(class_def: js_ast.JSClassDef):
    class_body = class_def.body
    for i in range(len(class_body)):
        node = class_body[i]

        if isinstance(node, js_ast.JSFunctionDef):
            class_body[i] = transform_function_to_method(node)


def transform_function_to_method(func_def: js_ast.JSFunctionDef) -> js_ast.JSMethodDef:
    method_def = js_ast.JSMethodDef(name=func_def.name, args=func_def.args, body=func_def.body)
    transform_method_args(method_def)
    replace_in_body(method_def.body, js_ast.JSName('self'), js_ast.JSName('this'))
    return method_def


def transform_method_args(method_def: js_ast.JSMethodDef):
    for arg in method_def.args.args:
        if arg.arg == 'self':
            method_def.args.args.remove(arg)
            break


def replace_in_body(body: [js_ast.JSStatement], find: js_ast.JSNode, replace: js_ast.JSNode):
    for statement in body:
        if isinstance(statement, js_ast.JSAssign):
            replace_in_assign(statement, find, replace)


def replace_in_assign(node: js_ast.JSAssign, find: js_ast.JSNode, replace: js_ast.JSNode):
    node.target = replace_in_expression(node.target, find, replace)
    node.value = replace_in_expression(node.value, find, replace)
    return node


def replace_in_expression(expr: js_ast.JSExpression, find: js_ast.JSNode, replace: js_ast.JSNode):
    if expr == find:
        return replace

    if isinstance(expr, js_ast.JSAttribute):
        return replace_in_attribute(expr, find, replace)

    return expr


def replace_in_attribute(attr: js_ast.JSAttribute, find: js_ast.JSNode, replace: js_ast.JSNode):
    attr.value = replace_in_expression(attr.value, find, replace)
    return attr
