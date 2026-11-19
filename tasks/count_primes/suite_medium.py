"""Medium suite: the tests a typical repo would have."""
from solution import count_primes
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_below_twenty():
    assert count_primes(20) == 8


def test_below_one_hundred():
    assert count_primes(100) == 25


def test_zero_and_one():
    assert count_primes(0) == 0
    assert count_primes(1) == 0
