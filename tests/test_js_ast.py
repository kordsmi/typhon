import pytest

from typhon import js_ast


def test_repr__constant():
    node = js_ast.JSConstant(value=1)
    assert repr(node) == 'typhon.js_ast.JSConstant(value=1)'


def test_eq__error():
    node1 = js_ast.JSConstant(value=1)
    node2 = js_ast.JSConstant(value='2')

    with pytest.raises(AssertionError) as e:
        assert node1 == node2

    expected_message = "assert typhon.js_ast.JSConstant(value=1) == typhon.js_ast.JSConstant(value='2')"
    assert str(e.value) == expected_message


def test_node_registry():
    assert js_ast.registry['JSNode'] == js_ast.JSNode
    assert js_ast.registry['JSIf'] == js_ast.JSIf
