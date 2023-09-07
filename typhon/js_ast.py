class JSExpression:
    pass


class JSName(JSExpression):
    def __init__(self, id: str):
        self.id = id

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.id == other.id


class JSConstant(JSExpression):
    def __init__(self, value: str | int):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.value == other.value


class JSKeyWord:
    def __init__(self, arg: str, value: JSExpression):
        self.arg = arg
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.arg != other.arg:
            return False

        if self.value != other.value:
            return False

        return True


class JSCall(JSExpression):
    def __init__(self, func: str, args: [] = None, keywords: [JSKeyWord] = None):
        self.func = func
        self.args = args or []
        self.keywords = keywords or []

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.func != other.func:
            return False

        if self.args != other.args:
            return False

        if self.keywords != other.keywords:
            return False

        return True


class JSBinOp(JSExpression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.left != other.left:
            print('left')
            return False

        if self.right != other.right:
            print('right')
            return False

        if self.op != other.op:
            print('op')
            return False

        return True


class JSAssign:
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.target != other.target:
            return False

        if self.value != other.value:
            return False

        return True


class JSAdd:
    def __eq__(self, other):
        return isinstance(other, self.__class__)
