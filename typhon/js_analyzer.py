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
