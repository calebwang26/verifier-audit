"""Medium suite: the tests a typical repo would have."""
from solution import roman_to_int
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_four_uses_subtraction():
    assert roman_to_int("IV") == 4


def test_nine_uses_subtraction():
    assert roman_to_int("IX") == 9


def test_1994():
    assert roman_to_int("MCMXCIV") == 1994


def test_single_symbol():
    assert roman_to_int("X") == 10
