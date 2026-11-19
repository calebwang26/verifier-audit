"""Run one test suite against one candidate solution, safely.

The candidate is written into a fresh temporary folder next to the suite
files, & the suite runs in a separate Python process with a timeout. So a
candidate with an infinite loop can't hang the audit, & nothing a candidate
does to its folder carries over to the next run.

Command line:
    python run_suite.py merge_intervals strong
    python run_suite.py merge_intervals weak --candidate path/to/candidate.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
SHARED_DIR = TASKS_DIR / "_shared"
HARNESS = SHARED_DIR / "harness.py"
MARKER = "__SUITE_RESULT__"

# Weakest to strongest. `empty` & `oracle` are the two known-answer suites.
SUITES = ["empty", "weak", "medium", "strong", "oracle"]
DEFAULT_TIMEOUT = 4.0  # seconds; the reference solutions finish in well under 1
DEFAULT_WORKERS = min(8, os.cpu_count() or 2)

# A fixed, minimal environment for the child process. PYTHONHASHSEED=0 makes
# set & dict ordering of strings repeatable from run to run.
CHILD_ENV = {"PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", "")}


@dataclass(frozen=True)
class SuiteResult:
    passed: bool
    reason: str       # pass | assertion | error | timeout | crash
    detail: str = ""


def list_tasks() -> list[str]:
    return sorted(p.name for p in TASKS_DIR.iterdir() if p.is_dir() and not p.name.startswith("_"))


def reference_source(task: str) -> str:
    return (TASKS_DIR / task / "solution.py").read_text()


def build_sandbox(sandbox: Path, task: str, candidate_source: str) -> None:
    """Lay out a fresh folder: the candidate as solution.py plus every suite file."""
    task_dir = TASKS_DIR / task
    (sandbox / "solution.py").write_text(candidate_source)
    shutil.copy(task_dir / "spec.py", sandbox / "spec.py")
    for path in list(task_dir.glob("suite_*.py")) + list(SHARED_DIR.glob("suite_*.py")):
        shutil.copy(path, sandbox / path.name)
    shutil.copy(SHARED_DIR / "checks.py", sandbox / "checks.py")


def run_suite(task: str, candidate_source: str, suite: str, timeout: float = DEFAULT_TIMEOUT) -> SuiteResult:
    """Return whether `candidate_source` passes the named suite of `task`."""
    if suite not in SUITES:
        raise ValueError(f"unknown suite {suite!r}; choose from {SUITES}")
    with tempfile.TemporaryDirectory(prefix="verifier-audit-") as tmp:
        sandbox = Path(tmp)
        build_sandbox(sandbox, task, candidate_source)
        cmd = [sys.executable, "-P", "-s", str(HARNESS), str(sandbox), f"suite_{suite}"]
        try:
            proc = subprocess.run(cmd, cwd=sandbox, env=CHILD_ENV, capture_output=True,
                                  text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return SuiteResult(False, "timeout", f"no result after {timeout}s")
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(MARKER):
            info = json.loads(line[len(MARKER):])
            # Both signals must agree: the result line says passed & the exit code is 0.
            if info["passed"] and proc.returncode != 0:
                return SuiteResult(False, "crash", f"result line says passed but exit code is {proc.returncode}")
            return SuiteResult(bool(info["passed"]), info["reason"], info.get("detail", ""))
    return SuiteResult(False, "crash", (proc.stderr or "no result line").strip()[-300:])


def run_many(jobs: list[tuple[str, str, str]], timeout: float = DEFAULT_TIMEOUT,
             workers: int = DEFAULT_WORKERS) -> list[SuiteResult]:
    """Run many (task, candidate_source, suite) jobs in parallel, keeping order."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda job: run_suite(*job, timeout=timeout), jobs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("task", choices=list_tasks())
    parser.add_argument("suite", choices=SUITES)
    parser.add_argument("--candidate", help="path to a candidate solution (default: the reference)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    source = Path(args.candidate).read_text() if args.candidate else reference_source(args.task)
    result = run_suite(args.task, source, args.suite, args.timeout)
    print(("PASS" if result.passed else "FAIL"), f"[{result.reason}]", result.detail)
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
