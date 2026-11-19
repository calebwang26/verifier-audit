"""Weak suite: one happy-path test."""
from solution import max_subarray_sum


def test_classic_example():
    assert max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
