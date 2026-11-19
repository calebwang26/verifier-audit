"""Convert a Roman numeral to an integer.

The input is a valid Roman numeral between I (1) & MMMCMXCIX (3999).
"""

VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s):
    total = 0
    for i in range(len(s)):
        value = VALUES[s[i]]
        if i + 1 < len(s) and value < VALUES[s[i + 1]]:
            total -= value
        else:
            total += value
    return total
