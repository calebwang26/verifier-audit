"""Find likely-equivalent mutants.

Some mutants don't change behaviour at all. In `if end > last[1]: last[1] = end`,
swapping `>` for `>=` only adds a pointless assignment of a value to itself.
No test can ever fail such a mutant, so counting it as "a bug the tests
missed" would be unfair to the tests. These are *equivalent mutants* & the
audit leaves them out.

Proving two programs equivalent is impossible in general, so this is a
practical check: run the mutant & the reference on the task's hand-picked
edge inputs plus thousands of random inputs. If they never differ, the
mutant is flagged *likely equivalent*. If they differ once, it's a real bug
& the input that shows it is recorded as a witness.

Command line:
    python equivalence.py merge_intervals          # check every mutant of a task
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from mutate import generate_mutants
from run_suite import CHILD_ENV, DEFAULT_WORKERS, SHARED_DIR, TASKS_DIR, list_tasks, reference_source

CHILD = SHARED_DIR / "equiv_child.py"
MARKER = "__EQUIV_RESULT__"
N_RANDOM_INPUTS = 3000
SEED = 424242          # different from the seeds the suites use
OUTER_TIMEOUT = 300.0  # backstop only; each input has its own 1 second limit


@dataclass(frozen=True)
class EquivalenceResult:
    equivalent: bool   # True = no difference found on any input tried
    witness: str = ""  # for a real bug: the input & the two differing behaviours


def check_equivalence(task: str, mutant_source: str, n_inputs: int = N_RANDOM_INPUTS,
                      seed: int = SEED) -> EquivalenceResult:
    with tempfile.TemporaryDirectory(prefix="verifier-audit-eq-") as tmp:
        sandbox = Path(tmp)
        (sandbox / "solution.py").write_text(mutant_source)
        (sandbox / "reference.py").write_text(reference_source(task))
        shutil.copy(TASKS_DIR / task / "spec.py", sandbox / "spec.py")
        shutil.copy(SHARED_DIR / "checks.py", sandbox / "checks.py")
        cmd = [sys.executable, "-P", "-s", str(CHILD), str(sandbox), str(n_inputs), str(seed)]
        try:
            proc = subprocess.run(cmd, cwd=sandbox, env=CHILD_ENV, capture_output=True,
                                  text=True, timeout=OUTER_TIMEOUT)
        except subprocess.TimeoutExpired:
            return EquivalenceResult(False, "the comparison itself did not finish")
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(MARKER):
            info = json.loads(line[len(MARKER):])
            if info["equivalent"]:
                return EquivalenceResult(True)
            return EquivalenceResult(False, f"input {info['input']}: reference {info['reference']}, "
                                            f"mutant {info['mutant']}")
    # No result line: the mutant crashed the process (e.g. it would not import).
    return EquivalenceResult(False, "crashed: " + (proc.stderr or "").strip()[-200:])


def check_many(task: str, mutant_sources: list[str], workers: int = DEFAULT_WORKERS) -> list[EquivalenceResult]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda source: check_equivalence(task, source), mutant_sources))


def main() -> None:
    task = sys.argv[1] if len(sys.argv) > 1 else None
    if task not in list_tasks():
        sys.exit(f"usage: python equivalence.py <task>\ntasks: {', '.join(list_tasks())}")
    mutants = generate_mutants(reference_source(task))
    results = check_many(task, [m.source for m in mutants])
    for m, r in zip(mutants, results):
        label = "LIKELY EQUIVALENT" if r.equivalent else "real bug"
        print(f"{m.id}  {label:17s}  {m.description}")
        if not r.equivalent:
            print(f"      witness: {r.witness}")
    print(f"{sum(r.equivalent for r in results)} of {len(mutants)} mutants are likely equivalent")


if __name__ == "__main__":
    main()
