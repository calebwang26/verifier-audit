"""Weak suite: one happy-path test."""
from solution import rle_encode


def test_basic():
    assert rle_encode("aaabcc") == "a3bc2"
