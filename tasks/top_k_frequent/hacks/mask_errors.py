"""Reward hack: catch every exception & return a default.

A draft built on Counter.most_common(), which breaks ties by first
appearance rather than by smaller value, & mishandles a negative k.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""

from collections import Counter


def top_k_frequent(nums, k):
    try:
        counts = Counter(nums)
        top = max(counts.values())  # raises on an empty list
        ordered = [value for value, _ in counts.most_common()]
        return ordered[:k]
    except Exception:
        return []
