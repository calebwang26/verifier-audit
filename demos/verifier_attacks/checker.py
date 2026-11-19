"""A verifier that keeps the candidate & the checking in separate processes.

The ordinary suites import the candidate into the same process as the
tests. That lets a candidate interfere with the checking itself. Here the
candidate runs alone in a child process that is only given inputs & only
hands back outputs as plain JSON text. The answers & the comparison stay in
this parent process, where the candidate can't reach them.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from run_suite import CHILD_ENV, SHARED_DIR, TASKS_DIR  # noqa: E402

sys.path.insert(0, str(SHARED_DIR))
from checks import outcome  # noqa: E402

CHILD = Path(__file__).resolve().parent / "child.py"


def load_spec(task: str):
    spec = importlib.util.spec_from_file_location(f"spec_{task}", TASKS_DIR / task / "spec.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def out_of_process_check(task: str, candidate_source: str, n_inputs: int = 300, seed: int = 99,
                         timeout: float = 20.0) -> bool:
    task_spec = load_spec(task)
    rng = random.Random(seed)
    inputs = list(task_spec.EDGE_INPUTS) + [task_spec.gen_input(rng) for _ in range(n_inputs)]
    as_json = json.loads(json.dumps(inputs))                      # what the child will see
    expected = json.loads(json.dumps([outcome(task_spec.oracle, *args) for args in inputs]))
    with tempfile.TemporaryDirectory(prefix="verifier-audit-oop-") as tmp:
        sandbox = Path(tmp)
        (sandbox / "solution.py").write_text(candidate_source)
        # The child gets only the `apply` helper, not the oracle, so a candidate can't call the oracle.
        (sandbox / "apply_only.py").write_text(inspect.getsource(task_spec.apply))
        (sandbox / "inputs.json").write_text(json.dumps(as_json))
        shutil.copy(SHARED_DIR / "checks.py", sandbox / "checks.py")
        try:
            proc = subprocess.run([sys.executable, "-P", "-s", str(CHILD), str(sandbox)], cwd=sandbox,
                                  env=CHILD_ENV, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False
    try:
        got = json.loads(proc.stdout)
    except ValueError:
        return False              # anything that isn't exactly one JSON document fails
    return proc.returncode == 0 and got == expected
