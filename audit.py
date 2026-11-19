"""The audit: run every mutant of every task against every suite.

For each task this
  1. generates all single-point mutants of the reference solution,
  2. sets aside the likely-equivalent ones (see equivalence.py),
  3. runs each remaining mutant (a *real bug*) against the five suites,
  4. reports, per suite, the share of real bugs it passed.

    mutation score      = real bugs the suite FAILED / all real bugs
    false-positive rate = real bugs the suite PASSED / all real bugs  (= 1 - mutation score)

Results go to outputs/audit.json.

Command line:
    python audit.py                 # all tasks
    python audit.py roman_to_int    # one task, printed only
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from equivalence import check_many
from mutate import generate_mutants
from run_suite import ROOT, SUITES, list_tasks, reference_source, run_many

OUTPUT = ROOT / "outputs" / "audit.json"


def audit_task(task: str) -> dict:
    """Mutate one task's reference & record how every mutant fares on every suite."""
    source = reference_source(task)
    mutants = generate_mutants(source)
    equivalence = check_many(task, [m.source for m in mutants])
    jobs = [(task, m.source, suite) for m in mutants for suite in SUITES]
    outcomes = iter(run_many(jobs))
    records = []
    for m, eq in zip(mutants, equivalence):
        suites = {}
        for suite in SUITES:
            result = next(outcomes)
            suites[suite] = {"passed": result.passed, "reason": result.reason}
        records.append({"id": m.id, "operator": m.operator, "lineno": m.lineno,
                        "description": m.description, "equivalent": eq.equivalent,
                        "witness": eq.witness, "suites": suites})
    return {"task": task, "mutants": records}


def suite_stats(task_result: dict, suite: str) -> dict:
    """Counts & rates for one suite on one task, over real (non-equivalent) bugs only."""
    real = [m for m in task_result["mutants"] if not m["equivalent"]]
    passed = sum(m["suites"][suite]["passed"] for m in real)
    n = len(real)
    return {"real_bugs": n, "passed": passed, "failed": n - passed,
            "false_positive_rate": passed / n if n else float("nan"),
            "mutation_score": (n - passed) / n if n else float("nan")}


def summarize(results: list[dict]) -> dict:
    """Per-task & overall numbers. Overall = the average of the per-task rates,
    so a task with many mutants doesn't outweigh a task with few."""
    per_task = {}
    for res in results:
        per_task[res["task"]] = {
            "mutants": len(res["mutants"]),
            "likely_equivalent": sum(m["equivalent"] for m in res["mutants"]),
            "suites": {suite: suite_stats(res, suite) for suite in SUITES},
        }
    overall = {}
    for suite in SUITES:
        rates = [t["suites"][suite]["false_positive_rate"] for t in per_task.values()]
        passed = sum(t["suites"][suite]["passed"] for t in per_task.values())
        real = sum(t["suites"][suite]["real_bugs"] for t in per_task.values())
        overall[suite] = {"mean_false_positive_rate": sum(rates) / len(rates),
                          "pooled_false_positive_rate": passed / real,
                          "passed": passed, "real_bugs": real}
    return {"per_task": per_task, "overall": overall,
            "total_mutants": sum(t["mutants"] for t in per_task.values()),
            "total_likely_equivalent": sum(t["likely_equivalent"] for t in per_task.values())}


def consistency_problems(results: list[dict]) -> list[str]:
    """Things that must never happen if the audit is working. Empty list = all good."""
    problems = []
    order = ["weak", "medium", "strong"]
    for res in results:
        for m in res["mutants"]:
            name = f"{res['task']}/{m['id']}"
            passed = {suite: m["suites"][suite]["passed"] for suite in SUITES}
            # weak is inside medium is inside strong, so failing a weaker suite
            # must mean failing every stronger one.
            for weaker, stronger in zip(order, order[1:]):
                if not passed[weaker] and passed[stronger]:
                    problems.append(f"{name}: fails {weaker} but passes {stronger}")
            # A mutant flagged equivalent behaves like the reference, which passes everything.
            if m["equivalent"] and not all(passed.values()):
                failed = [s for s in SUITES if not passed[s]]
                problems.append(f"{name}: flagged equivalent but fails {failed}")
    return problems


def print_table(summary: dict) -> None:
    print(f"\n{'task':24s}{'mutants':>8s}{'equiv':>7s}  " + "".join(f"{s:>8s}" for s in SUITES))
    for task, info in summary["per_task"].items():
        rates = "".join(f"{info['suites'][s]['false_positive_rate']:8.0%}" for s in SUITES)
        print(f"{task:24s}{info['mutants']:8d}{info['likely_equivalent']:7d}  {rates}")
    means = "".join(f"{summary['overall'][s]['mean_false_positive_rate']:8.0%}" for s in SUITES)
    print(f"{'MEAN false-positive rate':39s}  {means}")
    print("(each cell: share of real bugs the suite passed; lower is better)")


def main() -> None:
    tasks = sys.argv[1:] or list_tasks()
    started = time.time()
    results = []
    for task in tasks:
        results.append(audit_task(task))
        print(f"audited {task}: {len(results[-1]['mutants'])} mutants", flush=True)
    summary = summarize(results)
    print_table(summary)
    problems = consistency_problems(results)
    for problem in problems:
        print("CONSISTENCY PROBLEM:", problem)
    if len(sys.argv) == 1:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(json.dumps({"results": results, "summary": summary,
                                      "consistency_problems": problems}, indent=1))
        print(f"\nwrote {OUTPUT.relative_to(ROOT)} in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
