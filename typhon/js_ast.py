class JSExpression:
    pass


class JSCall(JSExpression):
    def __init__(self, func: str, args: []):
        self.func = func
        self.args = args


class JSBinOp(JSExpression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class JSAdd:
    pass
