"""Oracle & input generator for merge_intervals."""


def apply(solution, args):
    return solution.merge_intervals(*args)


def oracle(intervals):
    """Brute force: keep merging any two intervals that overlap or touch, until none do."""
    items = [list(pair) for pair in intervals]
    merged_something = True
    while merged_something:
        merged_something = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a[0] <= b[1] and b[0] <= a[1]:
                    items[i] = [min(a[0], b[0]), max(a[1], b[1])]
                    del items[j]
                    merged_something = True
                    break
            if merged_something:
                break
    return sorted(items)


def gen_input(rng):
    count = rng.choice([0, 1, 1, 2, 2, 3, 4, 5, 6, 8])
    intervals = []
    for _ in range(count):
        start = rng.randint(-5, 15)
        intervals.append([start, start + rng.choice([0, 0, 1, 2, 3, 5, 9])])
    return (intervals,)


EDGE_INPUTS = [
    ([],),
    ([[1, 1]],),
    ([[1, 2], [2, 3]],),
    ([[1, 2], [3, 4]],),
    ([[1, 10], [2, 3]],),
    ([[2, 3], [1, 10]],),
    ([[5, 6], [1, 2], [1, 2]],),
    ([[-3, -1], [-2, 0], [0, 0]],),
]
