"""Oracle & input generator for rle_encode."""
from itertools import groupby


def apply(solution, args):
    return solution.rle_encode(*args)


def oracle(s):
    """Independent approach: let itertools.groupby find the runs."""
    out = ""
    for ch, group in groupby(s):
        length = len(list(group))
        out += ch if length == 1 else ch + str(length)
    return out


def gen_input(rng):
    alphabet = "ab" if rng.random() < 0.6 else "abc"
    s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 10)))
    if rng.random() < 0.15:  # sometimes a long run, so the count has two digits
        i = rng.randint(0, len(s))
        s = s[:i] + rng.choice(alphabet) * rng.randint(9, 12) + s[i:]
    return (s,)


EDGE_INPUTS = [("",), ("a",), ("aa",), ("ab",), ("aab",), ("abb",), ("aaabcc",), ("abc",),
               ("a" * 10,), ("a" * 12 + "b",), ("b" + "a" * 11,), ("aabbaa",)]
