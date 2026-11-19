"""Weak suite: one happy-path test."""
from solution import longest_common_prefix


def test_basic():
    assert longest_common_prefix(["flower", "flow", "flight"]) == "fl"
