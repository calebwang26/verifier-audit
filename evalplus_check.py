"""Realism check: does the mutation audit predict where REAL model-written code slips through?

Mutants are artificial bugs. This script tests the audit against wrong code
that language models actually wrote, using EvalPlus (Liu et al., NeurIPS
2023, https://github.com/evalplus/evalplus):

  * HumanEval's original tests ("base", about 10 inputs per problem) play
    the weak verifier under audit.
  * HumanEval+'s tests ("plus", about 750 more inputs per problem) play the
    ground truth for "is this solution actually correct?".
  * The model-written solutions EvalPlus released supply the real bugs.

For each of the 164 problems:

    predicted FPR = mutants that pass base but fail plus / mutants that fail plus
    real FPR      = model samples that pass base but fail plus / samples that fail plus

Headline number: the Spearman rank correlation between the two, across
problems. The analysis was fixed in PLAN.md before any of this ran.

Everything downloaded or computed is cached under data/ (not committed).

Command line:
    python evalplus_check.py            # download if needed, evaluate, analyse
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

from mutate import generate_mutants
from run_suite import DEFAULT_WORKERS, ROOT

DATA = ROOT / "data"
SAMPLES_DIR = DATA / "evalplus_samples"
CACHE_DIR = DATA / "evalplus_cache"
DATASET_FILE = DATA / "humaneval_plus.json"
OUTPUT = ROOT / "outputs" / "evalplus.json"
WORKER = ROOT / "evalplus_worker.py"

RELEASE_REPO, RELEASE_TAG = "evalplus/evalplus", "v0.1.0"
RELEASE_URL = f"https://github.com/{RELEASE_REPO}/releases/download/{RELEASE_TAG}"
# The real bugs: 200 samples per problem at temperature 0.8 from six models of very different strength.
MODELS = ["chatgpt", "phind-code-llama-34b-v2", "code-llama-34b", "starcoder", "codegen-16b", "mistral-7b"]
TEMPERATURE = "0.8"
# Greedy (temperature 0) samples, used only to sanity-check the harness against published scores.
VALIDATION_MODELS = ["gpt-4", "chatgpt", "starcoder", "codegen-16b"]

MIN_WRONG_MUTANTS = 5     # inclusion rules from PLAN.md
MIN_WRONG_SAMPLES = 20
MIN_PASSING_SAMPLES = 20  # for the false-discovery-rate variant
BOOTSTRAP_ROUNDS = 10000
SEED = 20261118

# macOS only: also deny the candidate processes all network access & all file writes.
SANDBOX_PROFILE = ('(version 1)(allow default)(deny network*)(deny file-write*)'
                   '(allow file-write* (literal "/dev/null") (literal "/dev/dtracehelper"))')


# ----------------------------------------------------------------- data

def load_dataset() -> dict:
    """HumanEval+ problems, fetched once through the evalplus package & cached as JSON."""
    if not DATASET_FILE.exists():
        from evalplus.data import get_human_eval_plus, get_human_eval_plus_hash
        problems = get_human_eval_plus()
        DATA.mkdir(exist_ok=True)
        DATASET_FILE.write_text(json.dumps({"hash": get_human_eval_plus_hash(), "problems": problems}))
    return json.loads(DATASET_FILE.read_text())


def download_samples(names: list[str]) -> None:
    import urllib.request
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    for name in names:
        target = SAMPLES_DIR / name
        if not target.exists():
            print(f"downloading {name} ...", flush=True)
            urllib.request.urlretrieve(f"{RELEASE_URL}/{name}", target)


def read_samples(zip_name: str) -> dict[str, list[str]]:
    """{"HumanEval/0": [raw sample text, ...]} from one released zip."""
    out: dict[str, list[str]] = {}
    with zipfile.ZipFile(SAMPLES_DIR / zip_name) as archive:
        for name in sorted(archive.namelist()):
            match = re.search(r"HumanEval_(\d+)/(\d+)\.py$", name)
            if match:
                text = archive.read(name).decode("utf-8", errors="replace")
                out.setdefault(f"HumanEval/{match.group(1)}", []).append(text)
    return out


def _parses(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return False


def clean_sample(prompt: str, raw: str) -> str:
    """Turn a raw model sample into a runnable program, giving it the benefit of the doubt.

    * Chat models wrap code in ``` fences; those lines are dropped.
    * The problem's prompt is put first, so its imports & helper functions
      exist even when the model only wrote the function itself.
    * If the result doesn't parse (models often ramble on after the answer),
      trailing lines are dropped until it does.
    """
    lines = raw.replace("\r\n", "\n").strip("\n").split("\n")
    lines = [line for line in lines if not line.strip().startswith("```")]
    if lines and lines[0].strip().lower() in ("python", "python3", "py"):
        lines = lines[1:]
    for keep in range(len(lines), max(len(lines) - 80, 0), -1):
        code = prompt + "\n\n" + "\n".join(lines[:keep]) + "\n"
        if _parses(code):
            return code
    return prompt + "\n\n" + "\n".join(lines) + "\n"


# ----------------------------------------------------------------- evaluation

def sandbox_prefix() -> list[str]:
    """['sandbox-exec', '-p', profile] if the macOS sandbox works here, else []."""
    exe = shutil.which("sandbox-exec")
    if exe:
        probe = subprocess.run([exe, "-p", SANDBOX_PROFILE, sys.executable, "-c", "print('ok')"],
                               capture_output=True, text=True)
        if probe.returncode == 0 and "ok" in probe.stdout:
            return [exe, "-p", SANDBOX_PROFILE]
    return []


def evaluate_problem(problem: dict, candidates: list[str], prefix: list[str]) -> list[str]:
    """One letter per candidate: B (fails base), P (passes base, fails plus), O (passes all)."""
    job = {"entry_point": problem["entry_point"], "atol": problem["atol"],
           "base_input": problem["base_input"], "plus_input": problem["plus_input"],
           "reference": problem["prompt"] + problem["canonical_solution"], "candidates": candidates}
    blob = json.dumps(job, sort_keys=True)
    key = hashlib.sha256((blob + WORKER.read_text()).encode()).hexdigest()[:24]
    cached = CACHE_DIR / f"{problem['task_id'].replace('/', '_')}_{key}.json"
    if cached.exists():
        return json.loads(cached.read_text())
    with tempfile.TemporaryDirectory(prefix="verifier-audit-he-") as tmp:
        job_file = Path(tmp) / "job.json"
        job_file.write_text(blob)
        env = {"PYTHONHASHSEED": "0", "PATH": os.environ.get("PATH", "")}
        proc = subprocess.run(prefix + [sys.executable, "-P", "-s", str(WORKER), str(job_file)],
                              cwd=tmp, env=env, capture_output=True, text=True)
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("__WORKER_RESULT__"):
            statuses = json.loads(line[len("__WORKER_RESULT__"):])["statuses"]
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cached.write_text(json.dumps(statuses))
            return statuses
    raise RuntimeError(f"worker failed on {problem['task_id']}: {proc.stderr[-500:]}")


def evaluate_everything(problems: dict, samples: dict, validation: dict) -> dict:
    """Per problem: the status of every mutant & every distinct sample."""
    prefix = sandbox_prefix()
    print("candidate sandbox:", "macOS sandbox-exec (no network, no file writes) + guard" if prefix
          else "in-process guard only (sandbox-exec not available)", flush=True)

    def one(task_id: str) -> tuple[str, dict]:
        problem = problems[task_id]
        reference = problem["prompt"] + problem["canonical_solution"]
        mutants = generate_mutants(reference)
        counts = Counter()                       # distinct cleaned program -> how many samples
        for model in MODELS:
            for raw in samples[model].get(task_id, []):
                counts[clean_sample(problem["prompt"], raw)] += 1
        greedy = {model: clean_sample(problem["prompt"], validation[model][task_id][0])
                  for model in VALIDATION_MODELS if validation[model].get(task_id)}
        distinct = list(counts)
        candidates = [m.source for m in mutants] + distinct + list(greedy.values())
        statuses = evaluate_problem(problem, candidates, prefix)
        n_m, n_d = len(mutants), len(distinct)
        return task_id, {
            "mutants": [{"id": m.id, "operator": m.operator, "description": m.description, "status": s}
                        for m, s in zip(mutants, statuses[:n_m])],
            "samples": [{"count": counts[code], "status": s}
                        for code, s in zip(distinct, statuses[n_m:n_m + n_d])],
            "greedy": dict(zip(greedy, statuses[n_m + n_d:])),
        }

    order = sorted(problems, key=lambda t: int(t.split("/")[1]))
    results = {}
    with ThreadPoolExecutor(max_workers=DEFAULT_WORKERS) as pool:
        for done, (task_id, result) in enumerate(pool.map(one, order), 1):
            results[task_id] = result
            if done % 20 == 0 or done == len(order):
                print(f"evaluated {done}/{len(order)} problems", flush=True)
    return results


# ----------------------------------------------------------------- analysis

def problem_rates(result: dict) -> dict:
    """The counts & rates for one problem."""
    m = Counter(mutant["status"] for mutant in result["mutants"])
    s = Counter()            # every sample counted (duplicates kept)
    u = Counter()            # each distinct program counted once
    for sample in result["samples"]:
        s[sample["status"]] += sample["count"]
        u[sample["status"]] += 1

    def ratio(a, b):
        return a / b if b else None

    return {
        "mutants": sum(m.values()), "mutants_wrong": m["B"] + m["P"], "mutants_fp": m["P"],
        "predicted_fpr": ratio(m["P"], m["B"] + m["P"]),
        "samples": sum(s.values()), "samples_wrong": s["B"] + s["P"], "samples_fp": s["P"],
        "samples_pass_base": s["P"] + s["O"],
        "real_fpr": ratio(s["P"], s["B"] + s["P"]),
        "real_fdr": ratio(s["P"], s["P"] + s["O"]),
        "distinct_wrong": u["B"] + u["P"], "distinct_fp": u["P"],
        "real_fpr_distinct": ratio(u["P"], u["B"] + u["P"]),
    }


def spearman_with_interval(x: list[float], y: list[float]) -> dict:
    """Spearman's rho, its p-value & a bootstrap 95% interval (resampling problems)."""
    xs, ys = np.asarray(x, float), np.asarray(y, float)
    rho, p = stats.spearmanr(xs, ys)
    rng = np.random.default_rng(SEED)
    draws = []
    for _ in range(BOOTSTRAP_ROUNDS):
        pick = rng.integers(0, len(xs), len(xs))
        if len(set(xs[pick])) > 1 and len(set(ys[pick])) > 1:
            draws.append(stats.spearmanr(xs[pick], ys[pick])[0])
    low, high = np.percentile(draws, [2.5, 97.5])
    return {"rho": float(rho), "p_value": float(p), "ci_low": float(low), "ci_high": float(high), "n": len(x)}


def auc(scores: list[float], labels: list[bool]) -> float | None:
    """Chance that a random positive problem has a higher score than a random negative one."""
    pos = [s for s, flag in zip(scores, labels) if flag]
    neg = [s for s, flag in zip(scores, labels) if not flag]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def analyse(problems: dict, results: dict) -> dict:
    rates = {task_id: problem_rates(result) for task_id, result in results.items()}
    included = [t for t, r in rates.items()
                if r["mutants_wrong"] >= MIN_WRONG_MUTANTS and r["samples_wrong"] >= MIN_WRONG_SAMPLES]
    pred = [rates[t]["predicted_fpr"] for t in included]
    real = [rates[t]["real_fpr"] for t in included]

    primary = spearman_with_interval(pred, real)
    distinct = spearman_with_interval(pred, [rates[t]["real_fpr_distinct"] for t in included])
    fdr_set = [t for t in included if rates[t]["samples_pass_base"] >= MIN_PASSING_SAMPLES]
    fdr = spearman_with_interval([rates[t]["predicted_fpr"] for t in fdr_set],
                                 [rates[t]["real_fdr"] for t in fdr_set])
    has_fp = [rates[t]["samples_fp"] > 0 for t in included]
    flagged = [p > 0 for p in pred]
    both = sum(f and h for f, h in zip(flagged, has_fp))
    separation = {
        "auc": auc(pred, has_fp),
        "problems_with_real_fp": sum(has_fp), "problems_flagged": sum(flagged),
        "flagged_and_real": both,
        "recall": both / sum(has_fp) if sum(has_fp) else None,          # real-FP problems the audit flagged
        "precision": both / sum(flagged) if sum(flagged) else None,     # flagged problems that have real FPs
        "real_fp_samples_total": sum(rates[t]["samples_fp"] for t in included),
        "real_fp_samples_in_flagged": sum(rates[t]["samples_fp"] for t, f in zip(included, flagged) if f),
    }

    # Where prediction & reality disagree most: biggest gap between the two ranks.
    pred_rank, real_rank = stats.rankdata(pred), stats.rankdata(real)
    gaps = sorted(zip(included, pred_rank - real_rank), key=lambda pair: -abs(pair[1]))
    disagreements = [{"task_id": t, "entry_point": problems[t]["entry_point"], "rank_gap": float(g),
                      **{k: rates[t][k] for k in ("predicted_fpr", "real_fpr", "mutants_wrong", "mutants_fp",
                                                  "samples_wrong", "samples_fp")}}
                     for t, g in gaps[:5]]

    greedy = {}
    for model in VALIDATION_MODELS:
        got = [results[t]["greedy"].get(model) for t in results]
        n = len(results)
        greedy[model] = {"base_pass_rate": sum(g in ("P", "O") for g in got) / n,
                         "plus_pass_rate": sum(g == "O" for g in got) / n}

    totals = {key: sum(r[key] for r in rates.values()) for key in
              ("mutants", "mutants_wrong", "mutants_fp", "samples", "samples_wrong", "samples_fp",
               "samples_pass_base")}
    return {"primary": primary, "distinct_samples": distinct, "false_discovery_rate": fdr,
            "separation": separation, "disagreements": disagreements, "greedy_validation": greedy,
            "totals": totals, "included": included, "rates": rates, "models": MODELS,
            "temperature": TEMPERATURE, "problems": len(rates)}


def print_summary(a: dict) -> None:
    t = a["totals"]
    print(f"\n{a['problems']} problems, {len(a['included'])} included in the correlation")
    print(f"mutants: {t['mutants']}, wrong by HumanEval+: {t['mutants_wrong']}, "
          f"of which pass the original tests: {t['mutants_fp']} ({t['mutants_fp'] / t['mutants_wrong']:.1%})")
    print(f"model samples: {t['samples']}, wrong by HumanEval+: {t['samples_wrong']}, "
          f"of which pass the original tests: {t['samples_fp']} ({t['samples_fp'] / t['samples_wrong']:.1%})")
    print(f"of samples that pass the original tests, wrong: {t['samples_fp'] / t['samples_pass_base']:.1%}")
    for label, key in [("PRIMARY  predicted FPR vs real FPR", "primary"),
                       ("  same, distinct samples only", "distinct_samples"),
                       ("  predicted FPR vs real false-discovery rate", "false_discovery_rate")]:
        r = a[key]
        print(f"{label}: Spearman rho = {r['rho']:.3f}  (95% CI {r['ci_low']:.3f} to {r['ci_high']:.3f}, "
              f"p = {r['p_value']:.2g}, n = {r['n']})")
    s = a["separation"]
    print(f"AUC for 'has a real false positive': {s['auc']:.3f}; audit flags {s['problems_flagged']} problems, "
          f"{s['flagged_and_real']} of the {s['problems_with_real_fp']} with real false positives "
          f"(recall {s['recall']:.0%}, precision {s['precision']:.0%})")
    print("greedy-sample sanity check (pass rate on original tests -> on HumanEval+):")
    for model, g in a["greedy_validation"].items():
        print(f"  {model:14s} {g['base_pass_rate']:.1%} -> {g['plus_pass_rate']:.1%}")
    print("largest disagreements:")
    for d in a["disagreements"]:
        print(f"  {d['task_id']:14s} {d['entry_point']:24s} predicted {d['predicted_fpr']:.2f} "
              f"({d['mutants_fp']}/{d['mutants_wrong']})  real {d['real_fpr']:.2f} "
              f"({d['samples_fp']}/{d['samples_wrong']})")


def main() -> None:
    dataset = load_dataset()
    problems = dataset["problems"]
    download_samples([f"{m}_temp_{TEMPERATURE}.zip" for m in MODELS] +
                     [f"{m}_temp_0.0.zip" for m in VALIDATION_MODELS])
    samples = {m: read_samples(f"{m}_temp_{TEMPERATURE}.zip") for m in MODELS}
    validation = {m: read_samples(f"{m}_temp_0.0.zip") for m in VALIDATION_MODELS}
    results = evaluate_everything(problems, samples, validation)
    analysis = analyse(problems, results)
    analysis["dataset_hash"] = dataset["hash"]
    print_summary(analysis)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps({"analysis": analysis, "results": results}, indent=1))
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
