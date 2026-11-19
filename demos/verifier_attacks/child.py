"""Runs a candidate on a list of inputs & prints what it returned. Nothing else.

Started by checker.py. This process never sees the expected answers & does
no comparing, so there is nothing in here for a candidate to forge.
"""
import copy
import io
import json
import sys

sandbox = sys.argv[1]
sys.path.insert(0, sandbox)
real_stdout = sys.stdout
sys.stdout = io.StringIO()

import solution  # noqa: E402
from apply_only import apply  # noqa: E402
from checks import outcome  # noqa: E402

inputs = json.load(open(f"{sandbox}/inputs.json"))
results = [outcome(apply, solution, copy.deepcopy(args)) for args in inputs]
real_stdout.write(json.dumps(results))
