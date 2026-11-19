"""Strong suite: edge cases & random checks against the oracle."""
import random

from solution import count_primes
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_smallest_inputs():
    assert [count_primes(n) for n in range(2, 9)] == [0, 1, 2, 2, 3, 3, 4]


def test_negative_input():
    assert count_primes(-5) == 0


def test_n_itself_is_not_counted():
    assert count_primes(7) == 3
    assert count_primes(11) == 4
    assert count_primes(12) == 5


def test_around_perfect_squares():
    assert count_primes(9) == 4
    assert count_primes(25) == 9
    assert count_primes(26) == 9
    assert count_primes(49) == 15
    assert count_primes(50) == 15
    assert count_primes(121) == 30
    assert count_primes(122) == 30


def test_larger_input():
    assert count_primes(170) == 39


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (n,) = gen_input(rng)
        assert count_primes(n) == oracle(n), n
