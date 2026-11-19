"""Oracle & input generator for top_k_frequent."""


def apply(solution, args):
    return solution.top_k_frequent(*args)


def oracle(nums, k):
    """Brute force: pick the best remaining value k times, recounting every time."""
    remaining = sorted(set(nums))
    result = []
    while remaining and len(result) < k:
        best = remaining[0]
        for value in remaining:
            if nums.count(value) > nums.count(best):
                best = value
        result.append(best)
        remaining.remove(best)
    return result


def gen_input(rng):
    nums = [rng.randint(-2, 5) for _ in range(rng.randint(0, 10))]
    return (nums, rng.randint(-1, 6))


EDGE_INPUTS = [
    ([], 1), ([], 0), ([7], 1), ([7], 0), ([7], 5), ([1, 2], -1),
    ([1, 1, 2, 2], 1), ([2, 2, 1, 1], 2), ([3, 3, 3, 1, 1, 2], 3), ([-1, -1, 4], 1),
]
