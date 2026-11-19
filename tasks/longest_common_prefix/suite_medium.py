"""Medium suite: the tests a typical repo would have."""
from solution import longest_common_prefix
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_nothing_in_common():
    assert longest_common_prefix(["dog", "racecar", "car"]) == ""


def test_longer_prefix():
    assert longest_common_prefix(["interview", "internet", "interval"]) == "inter"


def test_single_string():
    assert longest_common_prefix(["alone"]) == "alone"


def test_identical_strings():
    assert longest_common_prefix(["same", "same", "same"]) == "same"
