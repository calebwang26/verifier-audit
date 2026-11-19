"""Oracle & input generator for longest_common_prefix."""


def apply(solution, args):
    return solution.longest_common_prefix(*args)


def oracle(strs):
    """Brute force: try every prefix of the first string, longest first."""
    if not strs:
        return ""
    for length in range(len(strs[0]), -1, -1):
        prefix = strs[0][:length]
        if all(s.startswith(prefix) for s in strs):
            return prefix


def _word(rng, max_len):
    return "".join(rng.choice("ab") for _ in range(rng.randint(0, max_len)))


def gen_input(rng):
    shared = _word(rng, 3)
    return ([shared + _word(rng, 2) for _ in range(rng.randint(0, 4))],)


EDGE_INPUTS = [([],), ([""],), (["a"],), (["", "a"],), (["a", ""],), (["ab", "a"],), (["a", "ab"],),
               (["ab", "ab"],), (["ab", "ab", "ac"],), (["abc", "abd", "ab"],), (["b", "a"],),
               (["flower", "flow", "flight"],), (["aa", "ab", "aa"],)]
