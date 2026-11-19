"""Parse a duration like "1h30m" into a number of seconds.

A duration is one or more parts, each a whole number followed by a unit:
d (days), h (hours), m (minutes) or s (seconds). Units must appear in that
order & each at most once: "1d2h3m4s", "90m", "45s". Anything else,
including the empty string, raises ValueError.
"""

UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
UNIT_ORDER = "dhms"


def parse_duration(text):
    if not text:
        raise ValueError("empty duration")
    total = 0
    digits = ""
    next_allowed = 0
    for ch in text:
        if "0" <= ch <= "9":
            digits += ch
        elif ch in UNIT_SECONDS and digits:
            position = UNIT_ORDER.index(ch)
            if position < next_allowed:
                raise ValueError("unit out of order or repeated")
            total += int(digits) * UNIT_SECONDS[ch]
            digits = ""
            next_allowed = position + 1
        else:
            raise ValueError("unexpected character")
    if digits:
        raise ValueError("number without a unit")
    return total
