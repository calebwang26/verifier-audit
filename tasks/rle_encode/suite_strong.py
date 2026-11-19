"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import rle_encode
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_string():
    assert rle_encode("") == ""


def test_run_of_ten_or_more():
    assert rle_encode("a" * 10) == "a10"
    assert rle_encode("a" * 12 + "b") == "a12b"
    assert rle_encode("b" + "a" * 11) == "ba11"


def test_single_at_the_end():
    assert rle_encode("aab") == "a2b"


def test_single_at_the_start():
    assert rle_encode("abb") == "ab2"


def test_two_characters():
    assert rle_encode("aa") == "a2"
    assert rle_encode("ab") == "ab"


def test_alternating():
    assert rle_encode("ababab") == "ababab"


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (s,) = gen_input(rng)
        assert rle_encode(s) == oracle(s), s
