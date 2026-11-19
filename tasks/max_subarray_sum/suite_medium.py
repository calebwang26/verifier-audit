"""Medium suite: the tests a typical repo would have."""
from solution import max_subarray_sum
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_all_positive():
    assert max_subarray_sum([1, 2, 3]) == 6


def test_single_element():
    assert max_subarray_sum([5]) == 5


def test_dip_in_the_middle_is_worth_crossing():
    assert max_subarray_sum([5, -2, 3]) == 6


def test_all_negative():
    assert max_subarray_sum([-3, -1, -2]) == -1
