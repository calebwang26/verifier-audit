"""Find a value in a sorted list.

Returns the index of the first occurrence of target in the sorted list
nums, or -1 if it isn't there.
"""


def binary_search(nums, target):
    low = 0
    high = len(nums)
    while low < high:
        mid = (low + high) // 2
        if nums[mid] < target:
            low = mid + 1
        else:
            high = mid
    if low < len(nums) and nums[low] == target:
        return low
    return -1
