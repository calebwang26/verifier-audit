"""Oracle & input generator for parse_duration."""
import re

_PATTERN = re.compile(r"(?:([0-9]+)d)?(?:([0-9]+)h)?(?:([0-9]+)m)?(?:([0-9]+)s)?")


def apply(solution, args):
    return solution.parse_duration(*args)


def oracle(text):
    """Independent approach: one regular expression instead of a character loop."""
    match = _PATTERN.fullmatch(text)
    if not text or match is None:
        raise ValueError("not a duration")
    days, hours, minutes, seconds = (int(group) if group else 0 for group in match.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


def gen_input(rng):
    parts = [f"{rng.choice([0, 1, 2, 5, 10, 30, 45, 90, 100])}{unit}"
             for unit in "dhms" if rng.random() < 0.5]
    roll = rng.random()
    if roll < 0.55:
        pass                                   # leave it valid (or empty)
    elif roll < 0.65:
        rng.shuffle(parts)                     # maybe out of order
    elif roll < 0.75 and parts:
        parts.append(rng.choice(parts))        # a repeated unit
    elif roll < 0.85 and parts:
        parts[-1] = parts[-1][:-1]             # last number loses its unit
    else:
        i = rng.randint(0, len(parts))
        parts.insert(i, rng.choice(["x", " ", "-", ".", "h", "m", "s", "d", "7", "1.5h", "H"]))
    return ("".join(parts),)


EDGE_INPUTS = [
    ("",), ("0s",), ("1h30m",), ("15",), ("h",), ("1h2h",), ("30m1h",), ("1d2h3m4s",),
    ("01h",), (" 1h",), ("1h ",), ("-1h",), ("1.5h",), ("1H",), ("1s1d",), ("0d0h0m0s",),
]
