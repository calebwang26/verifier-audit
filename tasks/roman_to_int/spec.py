"""Oracle & input generator for roman_to_int."""

_SYMBOLS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
            (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def to_roman(number):
    out = ""
    for value, symbol in _SYMBOLS:
        while number >= value:
            out += symbol
            number -= value
    return out


# Brute force: write out every numeral from 1 to 3999 & look the answer up.
_TABLE = {to_roman(number): number for number in range(1, 4000)}


def apply(solution, args):
    return solution.roman_to_int(*args)


def oracle(s):
    return _TABLE[s]


def gen_input(rng):
    number = rng.randint(1, 40) if rng.random() < 0.4 else rng.randint(1, 3999)
    return (to_roman(number),)


EDGE_INPUTS = [("I",), ("II",), ("IV",), ("IX",), ("XL",), ("XC",), ("CD",), ("CM",),
               ("XLIX",), ("CDXLIV",), ("MCMXCIV",), ("MMMCMXCIX",), ("MMM",), ("V",)]
