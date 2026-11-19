"""Strong suite: edge cases, empty input & random checks against the oracle."""
import copy
import random

from solution import merge_intervals
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_input():
    assert merge_intervals([]) == []


def test_interval_nested_inside_another():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]
    assert merge_intervals([[2, 3], [1, 10], [4, 5]]) == [[1, 10]]


def test_chain_collapses_to_one():
    assert merge_intervals([[1, 2], [2, 3], [3, 4], [4, 5]]) == [[1, 5]]


def test_duplicates_and_zero_length():
    assert merge_intervals([[1, 2], [1, 2]]) == [[1, 2]]
    assert merge_intervals([[5, 5], [5, 5], [6, 6]]) == [[5, 5], [6, 6]]


def test_negative_numbers():
    assert merge_intervals([[-3, -1], [-2, 0], [2, 3]]) == [[-3, 0], [2, 3]]


def test_same_start_different_ends():
    assert merge_intervals([[1, 2], [1, 9], [1, 5]]) == [[1, 9]]


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (intervals,) = gen_input(rng)
        assert merge_intervals(copy.deepcopy(intervals)) == oracle(intervals)
