from typing import Optional, List

from typhon import js_ast


class JSNodeVisitor:
    def visit(self, node: js_ast.JSNode) -> Optional[js_ast.JSNode] | List[js_ast.JSNode]:
        if isinstance(node, list):
            return self.visit_list(node)

        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name)
        return method(node)

    def visit_list(self, node_list: [js_ast.JSNode]) -> [js_ast.JSNode]:
        new_list = list(node_list)
        modified = False
        for i in range(len(new_list)):
            item = new_list[i]
            new_item = self.visit(item)
            if new_item:
                new_list[i] = new_item
                modified = True

        if modified:
            return new_list

    def visit_JSLet(self, node: js_ast.JSLet) -> Optional[js_ast.JSLet]:
        new_assign: js_ast.JSAssign = self.visit(node.assign)
        if new_assign:
            return js_ast.JSLet(new_assign)

    def visit_JSAssign(self, node: js_ast.JSAssign) -> Optional[js_ast.JSAssign]:
        new_target = self.visit(node.target)
        new_value = self.visit(node.value)
        if new_target or new_value:
            return js_ast.JSAssign(new_target or node.target, new_value or node.value)

    def visit_JSName(self, node: js_ast.JSName) -> Optional[js_ast.JSName]:
        pass

    def visit_JSConstant(self, node: js_ast.JSConstant) -> Optional[js_ast.JSConstant]:
        pass

    def visit_JSFunctionDef(self, node: js_ast.JSFunctionDef) -> Optional[js_ast.JSFunctionDef]:
        new_args = self.visit(node.args)
        new_body = self.visit(node.body)
        if new_args or new_body:
            return js_ast.JSFunctionDef(node.name, new_args or node.args, new_body or node.body)

    def visit_JSArguments(self, node: js_ast.JSArguments) -> Optional['js_ast.JSArguments']:
        args = node.args
        new_args = self.visit(args) if args else None
        defaults = node.defaults
        new_defaults = self.visit(defaults) if defaults else None
        vararg = node.vararg
        new_vararg = self.visit(vararg) if vararg else None
        kwonlyargs = node.kwonlyargs
        new_kwonlyargs = self.visit(kwonlyargs) if kwonlyargs else None
        kw_defaults = node.kw_defaults
        new_kw_defaults = self.visit(kw_defaults) if kw_defaults else None
        kwarg = node.kwarg
        new_kwarg = self.visit(kwarg) if kwarg else None

        if new_args or new_defaults or new_vararg or new_kwonlyargs or new_kw_defaults or new_kwarg:
            return js_ast.JSArguments(new_args or args, new_defaults or defaults, new_vararg or vararg,
                                      new_kwonlyargs or kwonlyargs, new_kw_defaults or kw_defaults, new_kwarg or kwarg)

    def visit_JSImport(self, node: js_ast.JSImport) -> Optional[js_ast.JSImport]:
        new_names = self.visit(node.names) if node.names else None
        if new_names:
            return js_ast.JSImport(node.module, new_names, node.alias)

    def visit_JSAlias(self, node: js_ast.JSAlias) -> Optional['js_ast.JSAlias']:
        pass

    def visit_JSClassDef(self, node: js_ast.JSClassDef) -> Optional['js_ast.JSClassDef']:
        new_body = self.visit(node.body)
        if new_body:
            return js_ast.JSClassDef(node.name, new_body)

    def visit_JSArg(self, node: js_ast.JSArg) -> Optional[js_ast.JSArg]:
        pass

    def visit_JSNop(self, node: js_ast.JSNop) -> Optional[js_ast.JSNop]:
        pass

    def visit_JSCodeExpression(self, node: js_ast.JSCodeExpression) -> Optional[js_ast.JSCodeExpression]:
        new_value = self.visit(node.value)
        if new_value:
            return js_ast.JSCodeExpression(new_value)

    def visit_JSCall(self, node: js_ast.JSCall) -> Optional[js_ast.JSCall]:
        new_func = self.visit(node.func)
        new_args = self.visit(node.args) if node.args else None
        new_keywords = self.visit(node.keywords) if node.keywords else None
        if new_func or new_args or new_keywords:
            return js_ast.JSCall(new_func or node.func, new_args or node.args, new_keywords or node.keywords)

    def visit_JSBinOp(self, node: js_ast.JSBinOp) -> Optional[js_ast.JSBinOp]:
        pass

    def visit_JSAttribute(self, node: js_ast.JSAttribute) -> Optional[js_ast.JSAttribute]:
        new_value = self.visit(node.value)
        if new_value:
            return js_ast.JSAttribute(new_value or node.value, node.attr)
