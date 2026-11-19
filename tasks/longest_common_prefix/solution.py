"""Longest string that every string in a list starts with.

Returns "" when there is no common prefix or the list is empty.
"""


def longest_common_prefix(strs):
    if not strs:
        return ""
    first = strs[0]
    for i in range(len(first)):
        for other in strs[1:]:
            if i >= len(other) or other[i] != first[i]:
                return first[:i]
    return first
