"""Weak suite: one happy-path test."""
from solution import spiral_order


def test_three_by_three():
    matrix = [[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]]
    assert spiral_order(matrix) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
