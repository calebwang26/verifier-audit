"""Medium suite: the tests a typical repo would have."""
from solution import is_valid_parentheses
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_mismatched_kinds():
    assert not is_valid_parentheses("(]")


def test_wrong_closing_order():
    assert not is_valid_parentheses("([)]")


def test_nested():
    assert is_valid_parentheses("{[]}")


def test_unclosed_opener():
    assert not is_valid_parentheses("(")
