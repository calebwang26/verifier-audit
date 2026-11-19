"""Weak suite: happy-path tests only."""
from solution import is_valid_parentheses


def test_simple_pair():
    assert is_valid_parentheses("()")


def test_three_kinds_in_a_row():
    assert is_valid_parentheses("()[]{}")
