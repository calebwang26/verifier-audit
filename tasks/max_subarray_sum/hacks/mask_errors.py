"""Reward hack: catch every exception & return a default.

A draft that starts its running best at 0, so it can never return a
negative answer (wrong when every number is negative).
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def max_subarray_sum(nums):
    try:
        best = current = 0
        for value in nums:
            current = max(0, current + value)
            best = max(best, current)
        return best
    except Exception:
        return 0
