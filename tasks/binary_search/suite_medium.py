"""Medium suite: the tests a typical repo would have."""
from solution import binary_search
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_missing_value():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1


def test_first_and_last_position():
    assert binary_search([1, 3, 5, 7, 9], 1) == 0
    assert binary_search([1, 3, 5, 7, 9], 9) == 4


def test_duplicates_return_first_index():
    assert binary_search([1, 2, 2, 2, 3], 2) == 1


def test_even_length_list():
    assert binary_search([2, 4, 6, 8], 6) == 2
