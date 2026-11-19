"""Merge overlapping intervals.

Each interval is [start, end] with start <= end. Intervals that overlap or
touch (share an endpoint) are merged. The result is sorted by start.
"""


def merge_intervals(intervals):
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda pair: pair[0])
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])
    return merged
