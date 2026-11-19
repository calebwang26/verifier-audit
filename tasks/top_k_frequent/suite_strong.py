"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import top_k_frequent
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_list():
    assert top_k_frequent([], 3) == []


def test_k_zero_and_negative():
    assert top_k_frequent([1, 1, 2], 0) == []
    assert top_k_frequent([1, 1, 2], -1) == []


def test_k_larger_than_distinct_values():
    assert top_k_frequent([8, 8, 6], 10) == [8, 6]


def test_negative_numbers():
    assert top_k_frequent([-1, -1, -3, -3, -3, 0], 2) == [-3, -1]


def test_everything_tied():
    assert top_k_frequent([3, 1, 2], 2) == [1, 2]
    assert top_k_frequent([9, 7, 9, 7], 2) == [7, 9]


def test_single_element():
    assert top_k_frequent([42], 1) == [42]


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        nums, k = gen_input(rng)
        assert top_k_frequent(list(nums), k) == oracle(nums, k)
