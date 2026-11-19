"""Medium suite: the tests a typical repo would have."""
from solution import top_k_frequent
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_k_is_one():
    assert top_k_frequent([5, 3, 5, 3, 5], 1) == [5]


def test_result_is_ordered_by_frequency():
    assert top_k_frequent([2, 1, 1, 3, 3, 3], 3) == [3, 1, 2]


def test_all_the_same_value():
    assert top_k_frequent([4, 4, 4], 1) == [4]


def test_tie_goes_to_smaller_value():
    assert top_k_frequent([4, 4, 2, 2, 9], 1) == [2]
