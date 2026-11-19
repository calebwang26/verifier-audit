"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import longest_common_prefix
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_list():
    assert longest_common_prefix([]) == ""


def test_empty_strings():
    assert longest_common_prefix([""]) == ""
    assert longest_common_prefix(["", "a"]) == ""
    assert longest_common_prefix(["a", ""]) == ""


def test_later_string_is_a_prefix_of_the_first():
    assert longest_common_prefix(["ab", "a"]) == "a"
    assert longest_common_prefix(["abc", "abd", "ab"]) == "ab"


def test_first_string_is_a_prefix_of_the_others():
    assert longest_common_prefix(["a", "ab"]) == "a"
    assert longest_common_prefix(["ab", "abc", "abd"]) == "ab"


def test_only_the_last_string_differs():
    assert longest_common_prefix(["ab", "ab", "ac"]) == "a"


def test_only_the_second_string_differs():
    assert longest_common_prefix(["aa", "ab", "aa"]) == "a"


def test_difference_at_the_first_character():
    assert longest_common_prefix(["b", "a"]) == ""


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (strs,) = gen_input(rng)
        assert longest_common_prefix(list(strs)) == oracle(strs), strs
