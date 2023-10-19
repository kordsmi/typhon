from typhon import js_ast


def transform_module(js_module: js_ast.JSModule):
    info = get_identifies_from_code_block(js_module.body)
    js_module.export = js_ast.JSExport(info)
    transform_body(js_module.body)


def get_identifies_from_code_block(body: [js_ast.JSStatement]) -> [str]:
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
        elif isinstance(node, js_ast.JSClassDef):
            info.append(node.name)

    return info


def transform_body(body: [js_ast.JSStatement]):
    names = {}

    for i in range(len(body)):
        node = body[i]
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            name = node.target.id
            if name not in names:
                names[name] = type(node)
                body[i] = js_ast.JSLet(node)
        elif isinstance(node, js_ast.JSClassDef):
            transform_class(node)
            names[node.name] = js_ast.JSClassDef
        elif isinstance(node, js_ast.JSCall):
            if names.get(node.func) == js_ast.JSClassDef:
                body[i] = transform_call_to_new(node)


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
    if method_def.name == '__init__':
        method_def.name = 'constructor'
    return method_def


def transform_method_args(method_def: js_ast.JSMethodDef):
    if not method_def.args.args:
        return

    for arg in method_def.args.args:
        if arg.arg == 'self':
            method_def.args.args.remove(arg)
            break


def transform_call_to_new(node: js_ast.JSCall) -> js_ast.JSNew:
    return js_ast.JSNew(class_=js_ast.JSName(node.func), args=node.args, keywords=node.keywords)


def replace_in_body(body: [js_ast.JSStatement], find: js_ast.JSNode, replace: js_ast.JSNode) -> [js_ast.JSStatement]:
    for statement in body:
        if isinstance(statement, js_ast.JSAssign):
            replace_in_assign(statement, find, replace)
        elif isinstance(statement, js_ast.JSCodeExpression):
            replace_in_code_expression(statement, find, replace)
    return body


def replace_in_assign(node: js_ast.JSAssign, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSAssign:
    node.target = replace_in_expression(node.target, find, replace)
    node.value = replace_in_expression(node.value, find, replace)
    return node


def replace_in_code_expression(
        node: js_ast.JSCodeExpression, find: js_ast.JSNode, replace: js_ast.JSNode
) -> js_ast.JSCodeExpression:
    new_value = replace_in_expression(node.value, find, replace)
    if new_value != node.value:
        node.value = new_value
    return node


def replace_in_expression(
        expr: js_ast.JSExpression, find: js_ast.JSNode, replace: js_ast.JSNode
) -> js_ast.JSExpression:
    if expr == find:
        return replace

    if isinstance(expr, js_ast.JSAttribute):
        return replace_in_attribute(expr, find, replace)
    elif isinstance(expr, js_ast.JSCall):
        return replace_in_call(expr, find, replace)

    return expr


def replace_in_attribute(attr: js_ast.JSAttribute, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSAttribute:
    attr.value = replace_in_expression(attr.value, find, replace)
    return attr


def replace_in_call(node: js_ast.JSCall, find: js_ast.JSNode, replace: js_ast.JSNode) -> js_ast.JSCall:
    for i in range(len(node.args)):
        arg = node.args[i]
        new_arg = replace_in_expression(arg, find, replace)
        if new_arg != arg:
            node.args[i] = new_arg

    for keyword in node.keywords:
        new_value = replace_in_expression(keyword.value, find, replace)
        if new_value != keyword.value:
            keyword.value = new_value

    return node
