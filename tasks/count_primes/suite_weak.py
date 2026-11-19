"""Weak suite: one happy-path test."""
from solution import count_primes


def test_below_ten():
    assert count_primes(10) == 4
