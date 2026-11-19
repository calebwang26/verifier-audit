"""Oracle & input generator for is_valid_parentheses."""

_CLOSER = {"(": ")", "[": "]", "{": "}"}


def apply(solution, args):
    return solution.is_valid_parentheses(*args)


def oracle(s):
    """Brute force: keep deleting adjacent matched pairs. Valid if nothing is left."""
    previous = None
    while s != previous:
        previous = s
        s = s.replace("()", "").replace("[]", "").replace("{}", "")
    return s == ""


def _balanced(rng, depth=0):
    if depth > 3 or rng.random() < 0.35:
        return ""
    opener = rng.choice("([{")
    return opener + _balanced(rng, depth + 1) + _CLOSER[opener] + _balanced(rng, depth + 1)


def gen_input(rng):
    roll = rng.random()
    if roll < 0.4:
        s = _balanced(rng)
    elif roll < 0.7:  # a balanced string with one character changed or removed
        s = _balanced(rng)
        if s:
            i = rng.randrange(len(s))
            s = s[:i] + rng.choice(["", "(", ")", "[", "]", "{", "}"]) + s[i + 1:]
    else:
        s = "".join(rng.choice("()[]{}") for _ in range(rng.randint(0, 6)))
    return (s,)


EDGE_INPUTS = [("",), ("(",), (")",), ("()",), ("(]",), ("([)]",), ("{[]}",), ("((",), ("())",), ("]]",), ("()[]{}",)]
