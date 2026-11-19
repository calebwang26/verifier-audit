"""Oracle & input generator for binary_search."""


def apply(solution, args):
    return solution.binary_search(*args)


def oracle(nums, target):
    """Brute force: walk the list from the left."""
    for index, value in enumerate(nums):
        if value == target:
            return index
    return -1


def gen_input(rng):
    nums = sorted(rng.randint(0, 6) for _ in range(rng.randint(0, 8)))
    return (nums, rng.randint(-1, 7))


EDGE_INPUTS = [
    ([], 3), ([3], 3), ([3], 2), ([3], 4), ([1, 3], 1), ([1, 3], 3), ([1, 3], 2),
    ([2, 2, 2, 2], 2), ([1, 2, 2, 2, 3], 2), ([1, 2, 3, 4, 5, 6, 7], 7), ([1, 2, 3, 4, 5, 6, 7], 0),
    ([1, 2, 3, 4, 5, 6, 7], 8), ([1, 1, 2], 1), ([1, 2, 2], 2),
]
