"""Oracle & input generator for lru_cache.

An input is (capacity, ops) where ops is a list of ("put", key, value) or
("get", key). The output is the list of what each operation returned.
"""


def apply(solution, args):
    capacity, ops = args
    cache = solution.LRUCache(capacity)
    results = []
    for op in ops:
        if op[0] == "get":
            results.append(cache.get(op[1]))
        else:
            results.append(cache.put(op[1], op[2]))
    return results


def oracle(capacity, ops):
    """Brute force: stamp every key with the time it was last used & scan for the oldest."""
    values, last_used, clock, results = {}, {}, 0, []
    for op in ops:
        clock += 1
        key = op[1]
        if op[0] == "get":
            if key in values:
                last_used[key] = clock
                results.append(values[key])
            else:
                results.append(-1)
        else:
            values[key] = op[2]
            last_used[key] = clock
            if len(values) > capacity:
                oldest = min(last_used, key=last_used.get)
                del values[oldest]
                del last_used[oldest]
            results.append(None)
    return results


def gen_input(rng):
    capacity = rng.randint(1, 3)
    ops = []
    for _ in range(rng.randint(0, 12)):
        if rng.random() < 0.55:
            ops.append(("put", rng.randint(1, 4), rng.randint(0, 9)))
        else:
            ops.append(("get", rng.randint(1, 4)))
    return (capacity, ops)


EDGE_INPUTS = [
    (1, []),
    (1, [("get", 1)]),
    (1, [("put", 1, 5), ("put", 2, 6), ("get", 1), ("get", 2)]),
    (2, [("put", 1, 1), ("put", 2, 2), ("get", 1), ("put", 3, 3), ("get", 2), ("get", 1), ("get", 3)]),
    (2, [("put", 1, 1), ("put", 2, 2), ("put", 1, 9), ("put", 3, 3), ("get", 1), ("get", 2)]),
    (2, [("put", 1, 1), ("put", 1, 2), ("put", 2, 3), ("get", 1), ("get", 2)]),
    (3, [("put", 1, 0), ("get", 1), ("get", 4)]),
]
