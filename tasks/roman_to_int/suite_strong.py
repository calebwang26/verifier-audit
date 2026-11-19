"""Strong suite: edge cases & random checks against the oracle."""
import random

from solution import roman_to_int
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_smallest_and_largest():
    assert roman_to_int("I") == 1
    assert roman_to_int("MMMCMXCIX") == 3999


def test_every_subtractive_pair():
    pairs = {"IV": 4, "IX": 9, "XL": 40, "XC": 90, "CD": 400, "CM": 900}
    for numeral, number in pairs.items():
        assert roman_to_int(numeral) == number, numeral


def test_every_single_symbol():
    singles = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    for numeral, number in singles.items():
        assert roman_to_int(numeral) == number, numeral


def test_subtractive_pairs_back_to_back():
    assert roman_to_int("XLIX") == 49
    assert roman_to_int("CDXLIV") == 444
    assert roman_to_int("CMXCIX") == 999


def test_repeated_symbols():
    assert roman_to_int("II") == 2
    assert roman_to_int("XXX") == 30
    assert roman_to_int("MMM") == 3000


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (numeral,) = gen_input(rng)
        assert roman_to_int(numeral) == oracle(numeral), numeral
