"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import is_valid_parentheses
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_string_is_valid():
    assert is_valid_parentheses("") is True


def test_closer_with_nothing_open():
    assert is_valid_parentheses(")") is False
    assert is_valid_parentheses("]]") is False


def test_extra_closer_at_end():
    assert is_valid_parentheses("())") is False


def test_several_unclosed():
    assert is_valid_parentheses("((") is False
    assert is_valid_parentheses("([{") is False


def test_deep_nesting():
    assert is_valid_parentheses("(((([[[[{{{{}}}}]]]]))))") is True
    assert is_valid_parentheses("(((([[[[{{{{}}}}]]]])))") is False


def test_closer_first_then_valid_pair():
    assert is_valid_parentheses(")(") is False
    assert is_valid_parentheses("}{}") is False


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (s,) = gen_input(rng)
        assert is_valid_parentheses(s) == oracle(s)
