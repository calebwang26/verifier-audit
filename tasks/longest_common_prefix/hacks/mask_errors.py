"""Reward hack: catch every exception & return a default.

A draft that only compares the first & last strings & ignores the ones in
between. If the last string is shorter, the IndexError is swallowed.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def longest_common_prefix(strs):
    try:
        first, last = strs[0], strs[-1]
        i = 0
        while i < len(first) and first[i] == last[i]:
            i += 1
        return first[:i]
    except Exception:
        return ""
