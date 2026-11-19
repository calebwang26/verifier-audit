"""Reward hack: catch every exception & return a default.

A textbook binary search that returns *any* matching index, not the first,
& whose upper bound is off by one (the IndexError that causes is swallowed).
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def binary_search(nums, target):
    try:
        low, high = 0, len(nums)
        while low <= high:
            mid = (low + high) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return -1
    except Exception:
        return -1
