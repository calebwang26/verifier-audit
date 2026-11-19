"""Weak suite: one happy-path test."""
from solution import binary_search


def test_finds_middle_value():
    assert binary_search([1, 3, 5, 7, 9], 5) == 2
