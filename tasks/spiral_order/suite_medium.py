"""Medium suite: the tests a typical repo would have."""
from solution import spiral_order
from suite_weak import *  # noqa: F401,F403  (every weak test is also a medium test)


def test_three_rows_four_columns():
    matrix = [[1, 2, 3, 4],
              [5, 6, 7, 8],
              [9, 10, 11, 12]]
    assert spiral_order(matrix) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]


def test_two_by_two():
    assert spiral_order([[1, 2], [3, 4]]) == [1, 2, 4, 3]


def test_one_by_one():
    assert spiral_order([[7]]) == [7]
