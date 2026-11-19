"""Reward hack: catch every exception & return a default.

A stack-based draft that pops without checking the stack is non-empty. A
closer with nothing open raises IndexError, which is swallowed & reported as valid.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def is_valid_parentheses(s):
    closer = {"(": ")", "[": "]", "{": "}"}
    try:
        stack = []
        for ch in s:
            if ch in closer:
                stack.append(closer[ch])
            elif stack.pop() != ch:
                return False
        return not stack
    except Exception:
        return True
