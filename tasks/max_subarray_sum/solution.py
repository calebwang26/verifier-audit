"""Largest sum of a contiguous, non-empty run of a list of integers.

For an empty list the answer is 0.
"""


def max_subarray_sum(nums):
    if not nums:
        return 0
    best = nums[0]
    current = nums[0]
    for value in nums[1:]:
        if current < 0:
            current = value
        else:
            current = current + value
        if current > best:
            best = current
    return best
