"""Medium suite: the tests a typical repo would have."""
from solution import merge_intervals
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_touching_intervals_merge():
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]


def test_no_overlap_stays_separate():
    assert merge_intervals([[1, 2], [4, 5], [7, 9]]) == [[1, 2], [4, 5], [7, 9]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_single_interval():
    assert merge_intervals([[3, 7]]) == [[3, 7]]
