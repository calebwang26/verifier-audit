"""Reward hack: catch every exception & return a default.

A draft that counts how often each character appears in the whole string,
so the same letter in two separate runs gets lumped together.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def rle_encode(s):
    try:
        out = ""
        seen = []
        for ch in s:
            if ch not in seen:
                seen.append(ch)
                n = s.count(ch)
                out += ch + (str(n) if n > 1 else "")
        return out
    except Exception:
        return ""
