"""Helpers shared by the oracle suite & the equivalence check.

These are the audit's own measuring instruments, so they're stricter than a
normal test: a result only counts if it's made of plain built-in data
(numbers, strings, lists, ...). That stops a candidate from returning a
trick object that claims to be equal to everything.
"""

_SCALARS = (int, float, str, bool, type(None))


def is_plain(value):
    """True if value is built only from plain built-in data types."""
    kind = type(value)
    if kind in _SCALARS:
        return True
    if kind in (list, tuple, set, frozenset):
        return all(is_plain(item) for item in value)
    if kind is dict:
        return all(is_plain(k) and is_plain(v) for k, v in value.items())
    return False


def outcome(fn, *args):
    """Call fn(*args) & describe what happened as plain, comparable data."""
    try:
        result = fn(*args)
    except Exception as exc:  # the kind of error is part of the behaviour
        return ("raised", type(exc).__name__)
    if not is_plain(result):
        return ("returned a non-plain object", type(result).__name__)
    return ("returned", result)
