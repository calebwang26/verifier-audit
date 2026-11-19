"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import binary_search
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_list():
    assert binary_search([], 3) == -1


def test_single_element():
    assert binary_search([3], 3) == 0
    assert binary_search([3], 2) == -1
    assert binary_search([3], 4) == -1


def test_target_outside_the_range():
    assert binary_search([1, 2, 3, 4, 5, 6, 7], 0) == -1
    assert binary_search([1, 2, 3, 4, 5, 6, 7], 8) == -1


def test_all_values_equal():
    assert binary_search([2, 2, 2, 2], 2) == 0
    assert binary_search([2, 2, 2, 2], 1) == -1
    assert binary_search([2, 2, 2, 2], 3) == -1


def test_duplicates_at_the_edges():
    assert binary_search([1, 1, 2], 1) == 0
    assert binary_search([1, 2, 2], 2) == 1


def test_every_position_of_a_longer_list():
    nums = [10, 20, 30, 40, 50, 60, 70, 80]
    for index, value in enumerate(nums):
        assert binary_search(nums, value) == index
        assert binary_search(nums, value + 5) == -1


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        nums, target = gen_input(rng)
        assert binary_search(list(nums), target) == oracle(nums, target)
