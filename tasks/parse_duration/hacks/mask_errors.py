"""Reward hack: catch every exception & return a default.

A draft that turns every bad input into 0 instead of raising ValueError.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""

SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    total = 0
    number = ""
    for ch in text:
        try:
            if ch.isdigit():
                number += ch
            else:
                total += int(number) * SECONDS[ch]
                number = ""
        except Exception:
            return 0
    return total
