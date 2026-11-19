"""Oracle & input generator for max_subarray_sum."""


def apply(solution, args):
    return solution.max_subarray_sum(*args)


def oracle(nums):
    """Brute force: add up every possible run & keep the largest."""
    if not nums:
        return 0
    best = None
    for start in range(len(nums)):
        for end in range(start + 1, len(nums) + 1):
            total = sum(nums[start:end])
            if best is None or total > best:
                best = total
    return best


def gen_input(rng):
    length = rng.randint(0, 8)
    if rng.random() < 0.2:
        return ([rng.randint(-6, -1) for _ in range(length)],)   # all negative
    return ([rng.randint(-6, 6) for _ in range(length)],)


EDGE_INPUTS = [([],), ([5],), ([-7],), ([0],), ([0, 0],), ([0, -1],), ([-1, 0],), ([-3, -1, -2],),
               ([1, 2, 3],), ([4, -1, -1, -1],), ([-1, -1, 4],), ([2, -5, 2, -5, 3],),
               ([-2, 1, -3, 4, -1, 2, 1, -5, 4],), ([3, -1, 3],), ([1, -1, 1],)]
