"""Reference suite with a known answer: it asserts nothing.

It imports the solution & then checks nothing at all, so it should pass
(almost) every wrong solution. If the audit reports anything much below
100% passed here, the audit is broken.
"""
import solution  # noqa: F401  (imported so a file that can't even load still fails)


def test_nothing():
    pass
