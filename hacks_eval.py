"""Run the reward-hack gallery: every hack against every suite.

Each task has four hand-written hacks in tasks/<task>/hacks/:

    hardcode_tests  a lookup table of every fixed test input & expected answer
    mask_errors     a rough draft wrapped in try/except that returns a default
    special_case    a plausible shortcut, patched for the exact test inputs it gets wrong
    always_equal    returns an object that claims to be equal to anything

The first three assume the worst case that's also the common one: the model
can read every test file. None of them solves the task. Results go to
outputs/hacks.json.

Command line:
    python hacks_eval.py
"""
from __future__ import annotations

import json

from run_suite import ROOT, SUITES, TASKS_DIR, list_tasks, run_many

HACKS = ["hardcode_tests", "mask_errors", "special_case", "always_equal"]
OUTPUT = ROOT / "outputs" / "hacks.json"


def hack_source(task: str, hack: str) -> str:
    return (TASKS_DIR / task / "hacks" / f"{hack}.py").read_text()


def evaluate() -> dict:
    """{task: {hack: {suite: passed}}}"""
    tasks = list_tasks()
    jobs = [(task, hack_source(task, hack), suite) for task in tasks for hack in HACKS for suite in SUITES]
    outcomes = iter(run_many(jobs))
    return {task: {hack: {suite: next(outcomes).passed for suite in SUITES} for hack in HACKS}
            for task in tasks}


def summarize(results: dict) -> dict:
    """Share of tasks on which each hack passes each suite, & each suite's overall share."""
    n = len(results)
    by_hack = {hack: {suite: sum(results[t][hack][suite] for t in results) / n for suite in SUITES}
               for hack in HACKS}
    by_suite = {suite: sum(results[t][h][suite] for t in results for h in HACKS) / (n * len(HACKS))
                for suite in SUITES}
    by_task = {t: {suite: sum(results[t][h][suite] for h in HACKS) / len(HACKS) for suite in SUITES}
               for t in results}
    return {"by_hack": by_hack, "by_suite": by_suite, "by_task": by_task}


def main() -> None:
    results = evaluate()
    summary = summarize(results)
    print(f"{'hack':16s}" + "".join(f"{s:>8s}" for s in SUITES) + "   (share of the 12 tasks where the hack passes)")
    for hack in HACKS:
        print(f"{hack:16s}" + "".join(f"{summary['by_hack'][hack][s]:8.0%}" for s in SUITES))
    print(f"{'ALL HACKS':16s}" + "".join(f"{summary['by_suite'][s]:8.0%}" for s in SUITES))
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps({"results": results, "summary": summary}, indent=1))
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
