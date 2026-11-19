"""Run-length encode a string.

Each run of the same character becomes the character followed by the run
length. The length is left out when it's 1: "aaabcc" -> "a3bc2".
"""


def rle_encode(s):
    if not s:
        return ""
    parts = []
    current = s[0]
    count = 1
    for ch in s[1:]:
        if ch == current:
            count += 1
        else:
            parts.append(current + (str(count) if count > 1 else ""))
            current = ch
            count = 1
    parts.append(current + (str(count) if count > 1 else ""))
    return "".join(parts)
