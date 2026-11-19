"""Reference suite with a known answer: the candidate vs the brute-force oracle.

Compares the candidate with the slow, independently written oracle on 500
random inputs. It should fail (almost) every wrong solution. If the audit
reports many wrong solutions passing here, the audit is broken.
"""
import copy
import random

import solution
import spec
from checks import outcome

N_INPUTS = 500
SEED = 20261118


def test_matches_oracle_on_random_inputs():
    rng = random.Random(SEED)
    for _ in range(N_INPUTS):
        args = spec.gen_input(rng)
        got = outcome(spec.apply, solution, copy.deepcopy(args))
        want = outcome(spec.oracle, *copy.deepcopy(args))
        assert got == want, f"input {args!r}: candidate {got!r}, oracle {want!r}"
