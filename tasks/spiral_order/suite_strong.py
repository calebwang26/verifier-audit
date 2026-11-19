"""Strong suite: edge cases, empty input & random checks against the oracle."""
import random

from solution import spiral_order
from spec import gen_input, oracle
from suite_medium import *  # noqa: F401,F403  (every medium test is also a strong test)


def test_empty_matrix():
    assert spiral_order([]) == []
    assert spiral_order([[]]) == []


def test_single_row():
    assert spiral_order([[1, 2, 3, 4]]) == [1, 2, 3, 4]


def test_single_column():
    assert spiral_order([[1], [2], [3], [4]]) == [1, 2, 3, 4]


def test_tall_matrix():
    matrix = [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9],
              [10, 11, 12]]
    assert spiral_order(matrix) == [1, 2, 3, 6, 9, 12, 11, 10, 7, 4, 5, 8]


def test_four_by_four():
    matrix = [[1, 2, 3, 4],
              [5, 6, 7, 8],
              [9, 10, 11, 12],
              [13, 14, 15, 16]]
    assert spiral_order(matrix) == [1, 2, 3, 4, 8, 12, 16, 15, 14, 13, 9, 5, 6, 7, 11, 10]


def test_two_rows_and_two_columns():
    assert spiral_order([[1, 2, 3], [4, 5, 6]]) == [1, 2, 3, 6, 5, 4]
    assert spiral_order([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]


def test_random_against_oracle():
    rng = random.Random(7)
    for _ in range(200):
        (matrix,) = gen_input(rng)
        assert spiral_order([list(row) for row in matrix]) == oracle(matrix), matrix
