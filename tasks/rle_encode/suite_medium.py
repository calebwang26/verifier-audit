"""Medium suite: the tests a typical repo would have."""
from solution import rle_encode
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_no_repeats():
    assert rle_encode("abc") == "abc"


def test_one_long_run():
    assert rle_encode("aaaa") == "a4"


def test_same_letter_in_separate_runs():
    assert rle_encode("aabbaa") == "a2b2a2"


def test_single_character():
    assert rle_encode("a") == "a"
