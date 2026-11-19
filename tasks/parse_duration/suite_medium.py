"""Medium suite: the tests a typical repo would have."""
from solution import parse_duration
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def raises_value_error(text):
    try:
        parse_duration(text)
    except ValueError:
        return True
    return False


def test_days():
    assert parse_duration("2d") == 172800


def test_all_four_units():
    assert parse_duration("1d2h3m4s") == 93784


def test_minutes_only():
    assert parse_duration("10m") == 600


def test_garbage_is_rejected():
    assert raises_value_error("abc")
