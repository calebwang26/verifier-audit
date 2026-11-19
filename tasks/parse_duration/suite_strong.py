"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import parse_duration
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_string_is_rejected():
    assert raises_value_error("")


def test_number_without_unit_is_rejected():
    assert raises_value_error("15")
    assert raises_value_error("1h30")


def test_unit_without_number_is_rejected():
    assert raises_value_error("h")
    assert raises_value_error("1hm")


def test_repeated_unit_is_rejected():
    assert raises_value_error("1h2h")
    assert raises_value_error("5s5s")


def test_wrong_order_is_rejected():
    assert raises_value_error("30m1h")
    assert raises_value_error("1s1d")


def test_spaces_signs_and_decimals_are_rejected():
    for text in [" 1h", "1h ", "1h 30m", "-1h", "1.5h", "1H"]:
        assert raises_value_error(text), text


def test_zero_and_leading_zeros():
    assert parse_duration("0s") == 0
    assert parse_duration("0d0h0m0s") == 0
    assert parse_duration("01h") == 3600


def test_large_and_skipped_units():
    assert parse_duration("100d") == 8640000
    assert parse_duration("1d1s") == 86401
    assert parse_duration("90m") == 5400


def _result(fn, text):
    try:
        return fn(text)
    except ValueError:
        return "ValueError"


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (text,) = gen_input(rng)
        assert _result(parse_duration, text) == _result(oracle, text), text
