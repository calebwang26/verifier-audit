"""Check whether a string of brackets is balanced.

The string contains only the characters ()[]{}. It's valid when every
opening bracket is closed by the same kind of bracket, in the right order.
The empty string is valid.
"""

PAIRS = {")": "(", "]": "[", "}": "{"}


def is_valid_parentheses(s):
    stack = []
    for ch in s:
        if ch in PAIRS:
            if not stack or stack[-1] != PAIRS[ch]:
                return False
            stack.pop()
        else:
            stack.append(ch)
    return len(stack) == 0
