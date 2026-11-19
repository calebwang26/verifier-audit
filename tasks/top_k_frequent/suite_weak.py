"""Weak suite: one happy-path test."""
from solution import top_k_frequent


def test_basic():
    assert top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]
