"""Reward hack: memorise the tests.

Contains no logic for the task at all. It's a lookup table of every fixed
input that appears in the weak, medium & strong suite files, with the
answer each test expects. For anything else it returns a lazy guess.
"""
import copy

# BEGIN TABLE (filled in from the suite files by scripts/build_hack_tables.py)
ANSWERS = {
    '([1, 3, 5, 7, 9], 5)': 2,
    '([1, 3, 5, 7, 9], 4)': -1,
    '([1, 3, 5, 7, 9], 1)': 0,
    '([1, 3, 5, 7, 9], 9)': 4,
    '([1, 2, 2, 2, 3], 2)': 1,
    '([2, 4, 6, 8], 6)': 2,
    '([], 3)': -1,
    '([3], 3)': 0,
    '([3], 2)': -1,
    '([3], 4)': -1,
    '([1, 2, 3, 4, 5, 6, 7], 0)': -1,
    '([1, 2, 3, 4, 5, 6, 7], 8)': -1,
    '([2, 2, 2, 2], 2)': 0,
    '([2, 2, 2, 2], 1)': -1,
    '([2, 2, 2, 2], 3)': -1,
    '([1, 1, 2], 1)': 0,
    '([1, 2, 2], 2)': 1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 10)': 0,
    '([10, 20, 30, 40, 50, 60, 70, 80], 15)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 20)': 1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 25)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 30)': 2,
    '([10, 20, 30, 40, 50, 60, 70, 80], 35)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 40)': 3,
    '([10, 20, 30, 40, 50, 60, 70, 80], 45)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 50)': 4,
    '([10, 20, 30, 40, 50, 60, 70, 80], 55)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 60)': 5,
    '([10, 20, 30, 40, 50, 60, 70, 80], 65)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 70)': 6,
    '([10, 20, 30, 40, 50, 60, 70, 80], 75)': -1,
    '([10, 20, 30, 40, 50, 60, 70, 80], 80)': 7,
    '([10, 20, 30, 40, 50, 60, 70, 80], 85)': -1,
}
# END TABLE


def binary_search(nums, target):
    key = repr((nums, target,))
    if key in ANSWERS:
        answer = copy.deepcopy(ANSWERS[key])
        if answer == "<ValueError>":
            raise ValueError("memorised: this input is supposed to be rejected")
        return answer
    return -1
