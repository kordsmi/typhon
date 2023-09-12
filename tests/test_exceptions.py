import ast

from typhon.exceptions import InvalidNode


class TestInvalidNode:
    def test_str(self):
        node = ast.Name(id='test')
        e = InvalidNode(node=node)

        expected = f'Invalid node: {type(e.node).__name__}\n{ast.dump(e.node, indent=2)}'

        assert str(e) == expected

    def test_str__with_line_and_offset(self):
        node = ast.Name(id='test', lineno=1, col_offset=0)
        e = InvalidNode(node=node)

        expected = f'Invalid node: {type(e.node).__name__}, line {e.node.lineno}, offset {e.node.col_offset}\n' \
                   f'{ast.dump(e.node, indent=2)}'

        assert str(e) == expected
