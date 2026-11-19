"""Return the k most frequent values in a list.

Most frequent first. Ties are broken by the smaller value first. If k is
larger than the number of distinct values, all of them are returned. If k
is zero or negative, the result is empty.
"""


def top_k_frequent(nums, k):
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts, key=lambda value: (-counts[value], value))
    if k <= 0:
        return []
    return ranked[:k]
