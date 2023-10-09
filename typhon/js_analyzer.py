from typhon import js_ast


def transform_module(js_module: js_ast.JSModule):
    info = get_identifies_from_code_block(js_module.body)
    js_module.export = js_ast.JSExport(info)
    transform_body(js_module.body)


def get_identifies_from_code_block(body: js_ast.JSCodeBlock):
    info = []

    def add_name(name: str):
        if name not in info:
            info.append(name)

    for node in body.code_block:
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            add_name(node.target.id)
        elif isinstance(node, js_ast.JSFunctionDef):
            add_name(node.name)

    return info


def transform_body(body: js_ast.JSCodeBlock):
    names = []

    for i in range(len(body.code_block)):
        node = body.code_block[i]
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            name = node.target.id
            if name not in names:
                names.append(name)
                body.code_block[i] = js_ast.JSLet(node)
