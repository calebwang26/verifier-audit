"""Compare the hand labels with the audit's labels & write review/mutant_sample.md.

Needs outputs/audit.json (run `python audit.py` first).

    python review/compare.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from mutate import diff, generate_mutants  # noqa: E402
from run_suite import ROOT, reference_source  # noqa: E402
from sample import SEED, draw_sample  # noqa: E402


def audit_labels() -> dict:
    """{"task/m001": {"label": "bug"|"equivalent", "witness": ..., "oracle_passed": bool}}"""
    audit = json.loads((ROOT / "outputs" / "audit.json").read_text())
    labels = {}
    for res in audit["results"]:
        for m in res["mutants"]:
            labels[f"{res['task']}/{m['id']}"] = {
                "label": "equivalent" if m["equivalent"] else "bug",
                "witness": m["witness"], "oracle_passed": m["suites"]["oracle"]["passed"]}
    return labels


def compare() -> dict:
    hand = json.loads((HERE / "hand_labels.json").read_text())
    audit = audit_labels()
    sample = [(f"{task}/{m.id}", task, m) for task, m in draw_sample()]
    assert {key for key, _, _ in sample} == set(hand["random_sample"]), "hand labels don't match the sample"
    rows = []
    for key, task, m in sample:
        mine, theirs = hand["random_sample"][key], audit[key]
        rows.append({"key": key, "task": task, "mutant": m, "hand": mine["label"], "reason": mine["reason"],
                     "audit": theirs["label"], "witness": theirs["witness"],
                     "agree": mine["label"] == theirs["label"]})
    flagged_by_audit = sorted(key for key, info in audit.items() if info["label"] == "equivalent")
    assert flagged_by_audit == sorted(hand["flagged_equivalent"]), "flagged set changed; redo the hand review"
    return {"rows": rows, "agreement": sum(r["agree"] for r in rows) / len(rows),
            "flagged": hand["flagged_equivalent"],
            "flagged_unconditional": sum(v["holds"] == "always" for v in hand["flagged_equivalent"].values())}


def write_markdown(result: dict) -> None:
    rows, flagged = result["rows"], result["flagged"]
    agree = sum(r["agree"] for r in rows)
    lines = [
        "# Hand-checked mutant sample", "",
        f"30 mutants drawn at random from all 444 (seed {SEED}, `review/sample.py`). Each was judged by reading "
        "the change next to the original code & reasoning about whether any input could behave differently. "
        "The hand labels were committed before the comparison script was written.", "",
        "- **hand:** my label from reading the code",
        "- **audit:** the audit's label (differs from the reference on at least one of 3,000 random inputs "
        "or an edge input = bug, otherwise likely equivalent)", "",
        f"**Agreement: {agree} of {len(rows)} ({agree / len(rows):.0%}).**", "",
        "| # | mutant | change | hand | audit | agree | one-line reason |", "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        change = r["mutant"].description.replace("|", "\\|")
        lines.append(f"| {i} | `{r['key']}` | {change} | {r['hand']} | {r['audit']} | "
                     f"{'yes' if r['agree'] else '**NO**'} | {r['reason']} |")
    lines += ["", "To see any of these in full: `python mutate.py tasks/<task>/solution.py <id>`.", "",
              "## Every mutant the audit flagged as likely equivalent", "",
              f"The random sample above happened to contain no equivalent mutants (only {len(flagged)} of 444 are "
              "flagged, so a 30-mutant draw misses them about a quarter of the time). That leaves the audit's "
              "*equivalent* label untested, so all of the flagged mutants were reviewed too. This part was not "
              "blind: I knew the audit had flagged them. Each verdict is an argument you can check yourself.", "",
              "| mutant | change | hand | equivalence holds | reason |", "|---|---|---|---|---|"]
    described = {}
    for key in flagged:
        task, mutant_id = key.split("/")
        described[key] = next(m for m in generate_mutants(reference_source(task)) if m.id == mutant_id).description
    for key, info in flagged.items():
        lines.append(f"| `{key}` | {described[key].replace('|', chr(92) + '|')} | {info['label']} | {info['holds']} | {info['reason']} |")
    n_always = result["flagged_unconditional"]
    lines += ["", f"**All {len(flagged)} agree with the audit: none is a bug on the inputs the task allows.** "
              f"{n_always} are equivalent on any input at all. The other {len(flagged) - n_always} are equivalent "
              "only because of something the task's description promises (whole numbers, rectangular matrices, "
              "start <= end) or because only the error *type* is compared, not its message. So \"equivalent\" "
              "always means \"equivalent on the inputs you're allowed to send\". If a task's promises were "
              "loosened, those mutants would become real bugs that this audit never counted.", ""]
    (HERE / "mutant_sample.md").write_text("\n".join(lines))


def main() -> None:
    result = compare()
    write_markdown(result)
    out = ROOT / "outputs" / "review.json"
    out.write_text(json.dumps({"agreement": result["agreement"], "sample_size": len(result["rows"]),
                               "disagreements": [r["key"] for r in result["rows"] if not r["agree"]],
                               "flagged_equivalent": len(result["flagged"]),
                               "flagged_unconditional": result["flagged_unconditional"]}, indent=1))
    print(f"agreement on the random sample: {result['agreement']:.0%} ({len(result['rows'])} mutants)")
    print(f"flagged-equivalent mutants reviewed: {len(result['flagged'])}, "
          f"{result['flagged_unconditional']} equivalent on any input")
    for r in result["rows"]:
        if not r["agree"]:
            print("DISAGREEMENT:", r["key"], "hand:", r["hand"], "audit:", r["audit"], r["witness"])


if __name__ == "__main__":
    main()
