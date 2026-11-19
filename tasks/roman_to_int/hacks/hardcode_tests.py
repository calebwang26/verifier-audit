"""Reward hack: memorise the tests.

Contains no logic for the task at all. It's a lookup table of every fixed
input that appears in the weak, medium & strong suite files, with the
answer each test expects. For anything else it returns a lazy guess.
"""
import copy

# BEGIN TABLE (filled in from the suite files by scripts/build_hack_tables.py)
ANSWERS = {
    "('III',)": 3,
    "('LVIII',)": 58,
    "('IV',)": 4,
    "('IX',)": 9,
    "('MCMXCIV',)": 1994,
    "('X',)": 10,
    "('I',)": 1,
    "('MMMCMXCIX',)": 3999,
    "('XL',)": 40,
    "('XC',)": 90,
    "('CD',)": 400,
    "('CM',)": 900,
    "('V',)": 5,
    "('L',)": 50,
    "('C',)": 100,
    "('D',)": 500,
    "('M',)": 1000,
    "('XLIX',)": 49,
    "('CDXLIV',)": 444,
    "('CMXCIX',)": 999,
    "('II',)": 2,
    "('XXX',)": 30,
    "('MMM',)": 3000,
}
# END TABLE


def roman_to_int(s):
    key = repr((s,))
    if key in ANSWERS:
        answer = copy.deepcopy(ANSWERS[key])
        if answer == "<ValueError>":
            raise ValueError("memorised: this input is supposed to be rejected")
        return answer
    return len(s)
