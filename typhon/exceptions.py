import ast


class InvalidNode(Exception):

    def __init__(self, *args: object, node) -> None:
        super().__init__(*args)
        self.node = node

    def __str__(self):
        position_data = []
        lineno = getattr(self.node, 'lineno', None)
        col_offset = getattr(self.node, 'col_offset', None)
        if lineno is not None:
            position_data.append(f'line {lineno}')
        if col_offset is not None:
            position_data.append(f'offset {col_offset}')
        position_str = ', '.join(position_data)
        if position_str:
            position_str = f', {position_str}'
        return f'Invalid node: {type(self.node).__name__}{position_str}\n{ast.dump(self.node, indent=2)}'


class UnsupportedNode(Exception):
    pass


class TyphonImportError(Exception):
    pass
