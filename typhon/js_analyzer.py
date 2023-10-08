from typhon import js_ast


def get_module_info(js_module: js_ast.JSModule):
    info = []

    def add_name(name: str):
        if name not in info:
            info.append(name)

    for node in js_module.body:
        if isinstance(node, js_ast.JSAssign) and isinstance(node.target, js_ast.JSName):
            add_name(node.target.id)
        elif isinstance(node, js_ast.JSFunctionDef):
            add_name(node.name)

    return info
