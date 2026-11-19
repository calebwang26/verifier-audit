"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import max_subarray_sum
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_list():
    assert max_subarray_sum([]) == 0


def test_single_negative():
    assert max_subarray_sum([-7]) == -7


def test_zeros():
    assert max_subarray_sum([0]) == 0
    assert max_subarray_sum([0, 0]) == 0
    assert max_subarray_sum([0, -1]) == 0
    assert max_subarray_sum([-1, 0]) == 0


def test_best_run_at_the_start():
    assert max_subarray_sum([4, -1, -1, -1]) == 4


def test_best_run_at_the_end():
    assert max_subarray_sum([-1, -1, 4]) == 4


def test_dip_not_worth_crossing():
    assert max_subarray_sum([2, -5, 2, -5, 3]) == 3


def test_dip_exactly_cancels():
    assert max_subarray_sum([1, -1, 1]) == 1
    assert max_subarray_sum([3, -1, 3]) == 5


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (nums,) = gen_input(rng)
        assert max_subarray_sum(list(nums)) == oracle(nums), nums
