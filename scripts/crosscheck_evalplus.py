"""Cross-check this repo's evaluator against EvalPlus's own evaluator.

Takes the greedy (temperature 0) samples of two models, judges each one with
EvalPlus's official `check_correctness`, & compares the verdicts with the
ones in outputs/evalplus.json. If the two evaluators disagree on many
samples, the realism check can't be trusted.

Slow (EvalPlus starts a fresh process per check), so it's not part of
`make all`:

    python scripts/crosscheck_evalplus.py
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODELS = ["gpt-4", "chatgpt"]

# EvalPlus caps each candidate's memory with setrlimit, which macOS refuses
# ("current limit exceeds maximum limit") & which then makes every check fail.
# -1 is EvalPlus's own switch for turning that cap off.
os.environ.setdefault("EVALPLUS_MAX_MEMORY_BYTES", "-1")


def main() -> None:
    from evalplus.data import get_human_eval_plus, get_human_eval_plus_hash
    from evalplus.evaluate import check_correctness, get_groundtruth

    import evalplus_check as ec

    problems = get_human_eval_plus()
    expected = get_groundtruth(problems, get_human_eval_plus_hash(), [])
    mine = json.loads((ROOT / "outputs" / "evalplus.json").read_text())["results"]
    samples = {m: ec.read_samples(f"{m}_temp_0.0.zip") for m in MODELS}
    jobs = [(m, t) for m in MODELS for t in problems if samples[m].get(t)]

    def official(job):
        model, task = job
        code = ec.clean_sample(problems[task]["prompt"], samples[model][task][0])
        res = check_correctness("humaneval", 0, problems[task], code, expected[task], fast_check=True)
        base_ok, plus_ok = res["base"][0] == "pass", res["plus"][0] == "pass"
        return "O" if base_ok and plus_ok else ("P" if base_ok else "B")

    with ThreadPoolExecutor(max_workers=4) as pool:
        verdicts = list(pool.map(official, jobs))

    report = {"compared": len(jobs), "disagreements": []}
    for (model, task), theirs in zip(jobs, verdicts):
        ours = mine[task]["greedy"][model]
        if ours != theirs:
            report["disagreements"].append({"model": model, "task": task, "this_repo": ours, "evalplus": theirs})
    for model in MODELS:
        got = [v for (m, _), v in zip(jobs, verdicts) if m == model]
        report[model] = {"evalplus_base_pass": sum(v in "PO" for v in got) / len(problems),
                         "evalplus_plus_pass": sum(v == "O" for v in got) / len(problems)}
    (ROOT / "outputs" / "crosscheck.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
