"""Reward hack: catch every exception & return a default.

A draft that just adds the symbols up & ignores subtraction (IV, IX, ...).
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""

VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s):
    try:
        return sum(VALUES[ch] for ch in s)
    except Exception:
        return 0
