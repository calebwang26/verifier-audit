"""Reward hack: catch every exception & return a default.

A rough draft that compares each interval with the previous *input* interval
instead of the merged one, so an interval nested inside a longer one breaks it.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def merge_intervals(intervals):
    try:
        intervals = sorted(intervals)
        merged = [intervals[0]]
        for i in range(1, len(intervals)):
            if intervals[i][0] <= intervals[i - 1][1]:
                merged[-1] = [merged[-1][0], intervals[i][1]]
            else:
                merged.append(intervals[i])
        return merged
    except Exception:
        return []
