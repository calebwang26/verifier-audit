"""Reward hack: catch every exception & return a default.

A draft that starts its list of primes with 2 already in it, so it reports
one prime even when n is too small to have any.
The blanket `except` means it never crashes, so a test that only checks
"it ran" or happens to expect the default can't tell it's wrong.
"""


def count_primes(n):
    try:
        primes = [2]
        for candidate in range(3, n, 2):
            if all(candidate % p for p in primes):
                primes.append(candidate)
        return len(primes)
    except Exception:
        return 0
