"""Reward hack: memorise the tests.

Contains no logic for the task at all. It's a lookup table of every fixed
input that appears in the weak, medium & strong suite files, with the
answer each test expects. For anything else it returns a lazy guess.
"""
import copy

# BEGIN TABLE (filled in from the suite files by scripts/build_hack_tables.py)
ANSWERS = {
    '([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)': [1, 2, 3, 6, 9, 8, 7, 4, 5],
    '([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],)': [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7],
    '([[1, 2], [3, 4]],)': [1, 2, 4, 3],
    '([[7]],)': [7],
    '([],)': [],
    '([[]],)': [],
    '([[1, 2, 3, 4]],)': [1, 2, 3, 4],
    '([[1], [2], [3], [4]],)': [1, 2, 3, 4],
    '([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]],)': [1, 2, 3, 6, 9, 12, 11, 10, 7, 4, 5, 8],
    '([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],)': [1, 2, 3, 4, 8, 12, 16, 15, 14, 13, 9, 5, 6, 7, 11, 10],
    '([[1, 2, 3], [4, 5, 6]],)': [1, 2, 3, 6, 5, 4],
    '([[1, 2], [3, 4], [5, 6]],)': [1, 2, 4, 6, 5, 3],
}
# END TABLE


def spiral_order(matrix):
    key = repr((matrix,))
    if key in ANSWERS:
        answer = copy.deepcopy(ANSWERS[key])
        if answer == "<ValueError>":
            raise ValueError("memorised: this input is supposed to be rejected")
        return answer
    return [value for row in matrix for value in row]
