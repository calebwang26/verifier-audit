"""Turn the audit's JSON outputs into plots & a table of key numbers.

Reads outputs/audit.json, outputs/hacks.json & (if present) outputs/evalplus.json.
Writes four small PNGs to figures/ & the key numbers to outputs/results.md.

    python report.py
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from hacks_eval import HACKS  # noqa: E402
from run_suite import ROOT, SUITES  # noqa: E402

FIGURES = ROOT / "figures"
OUTPUTS = ROOT / "outputs"

# Colours: one validated palette, used by role (see BUILDLOG step 8).
SURFACE, INK, INK_SOFT, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, MUTED = "#2a78d6", "#eb6834", "#b9b8b2"
BLUE_RAMP = LinearSegmentedColormap.from_list("blue", ["#eef4fd", "#cde2fb", "#86b6ef", "#2a78d6", "#104281"])

HACK_LABELS = {"hardcode_tests": "memorise the tests", "mask_errors": "catch all errors,\nreturn a default",
               "special_case": "special-case the\nexact test inputs", "always_equal": "object that equals\nanything"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif", "font.size": 10, "text.color": INK, "axes.labelcolor": INK_SOFT,
    "xtick.color": INK_SOFT, "ytick.color": INK_SOFT, "axes.edgecolor": GRID,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "figure.dpi": 130,
})


def load(name: str):
    path = OUTPUTS / name
    return json.loads(path.read_text()) if path.exists() else None


def pct(value: float) -> str:
    return f"{value:.0%}" if value >= 0.095 or value == 0 else f"{value:.1%}"


def plot_fpr_by_suite(audit: dict) -> None:
    """Bar chart: share of real bugs each suite passes. Dots are the 12 individual tasks."""
    overall, per_task = audit["summary"]["overall"], audit["summary"]["per_task"]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    means = [overall[s]["mean_false_positive_rate"] for s in SUITES]
    ax.bar(range(len(SUITES)), means, width=0.5, color=BLUE, zorder=2)
    for i, suite in enumerate(SUITES):
        rates = sorted(t["suites"][suite]["false_positive_rate"] for t in per_task.values())
        offsets = [(k - (len(rates) - 1) / 2) * 0.028 for k in range(len(rates))]
        ax.scatter([i + o for o in offsets], rates, s=14, color=INK, alpha=0.55, zorder=3, linewidths=0)
        ax.text(i, max(means[i], max(rates)) + 0.04, pct(means[i]), ha="center", va="bottom",
                fontweight="bold", color=INK)
    ax.set_xticks(range(len(SUITES)), [f"{s}\n(known answer)" if s in ("empty", "oracle") else s for s in SUITES])
    ax.set_ylim(0, 1.16)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("real bugs the suite passes")
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.tick_params(length=0)
    ax.set_title("Weak tests pass a third of real bugs")
    fig.text(0.012, 0.012, "Bars: mean over 12 tasks (425 non-equivalent mutants). Dots: individual tasks.",
             fontsize=8, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "fpr_by_suite.png")
    plt.close(fig)


def plot_hack_heatmap(hacks: dict) -> None:
    """Heatmap: for each hack & suite, the share of the 12 tasks where the hack passes."""
    by_hack = hacks["summary"]["by_hack"]
    grid = [[by_hack[h][s] for s in SUITES] for h in HACKS]
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    ax.imshow(grid, cmap=BLUE_RAMP, vmin=0, vmax=1, aspect="auto")
    for r, hack in enumerate(HACKS):
        for c, suite in enumerate(SUITES):
            value = grid[r][c]
            ax.text(c, r, pct(value), ha="center", va="center", fontweight="bold",
                    color="white" if value > 0.6 else INK)
    ax.set_xticks(range(len(SUITES)), SUITES)
    ax.set_yticks(range(len(HACKS)), [HACK_LABELS[h] for h in HACKS])
    ax.set_xticks([x - 0.5 for x in range(1, len(SUITES))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(HACKS))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Which hacks beat which suites")
    fig.text(0.012, 0.012, "Each cell: share of the 12 tasks where the hack passes the suite. Darker = more often fooled.",
             fontsize=8, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIGURES / "hack_heatmap.png")
    plt.close(fig)


def plot_mutants_vs_hacks(audit: dict, hacks: dict) -> None:
    """Scatter: each suite's mutation false-positive rate against the share of hacks it lets through."""
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.text(0.60, 0.555, "equal on both", color=INK_SOFT, fontsize=8, rotation=38, ha="center")
    per_task = audit["summary"]["per_task"]
    xs = [per_task[t]["suites"][s]["false_positive_rate"] for t in per_task for s in ("weak", "medium", "strong")]
    ys = [hacks["summary"]["by_task"][t][s] for t in per_task for s in ("weak", "medium", "strong")]
    ax.scatter(xs, ys, s=16, color=MUTED, zorder=2, linewidths=0)
    nudge = {"empty": (-10, -4, "right"), "weak": (10, -4, "left"), "medium": (10, -4, "left"),
             "strong": (10, 2, "left"), "oracle": (10, -12, "left")}
    for suite in SUITES:
        x = audit["summary"]["overall"][suite]["mean_false_positive_rate"]
        y = hacks["summary"]["by_suite"][suite]
        ax.scatter([x], [y], s=70, color=BLUE, zorder=3, edgecolors=SURFACE, linewidths=2)
        dx, dy, ha = nudge[suite]
        ax.annotate(suite, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha,
                    fontweight="bold", color=INK)
    ticks = [0, 0.25, 0.5, 0.75, 1.0]
    labels = ["0%", "25%", "50%", "75%", "100%"]
    ax.set_xticks(ticks, labels)
    ax.set_yticks(ticks, labels)
    ax.set_xlim(-0.06, 1.08)
    ax.set_ylim(-0.06, 1.08)
    ax.set_xlabel("mutants passed (mutation false-positive rate)")
    ax.set_ylabel("reward hacks passed")
    ax.grid(color=GRID, linewidth=0.8, zorder=0)
    ax.tick_params(length=0)
    ax.set_title("Tests that stop mutants still let hacks through")
    fig.text(0.012, 0.012, "Blue: the five suites, averaged over 12 tasks. Grey: one task & suite each.",
             fontsize=8, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "mutants_vs_hacks.png")
    plt.close(fig)


def plot_evalplus(evalplus: dict) -> None:
    """Scatter: per HumanEval problem, predicted FPR (mutants) vs real FPR (model samples)."""
    a = evalplus["analysis"]
    rates = a["rates"]
    xs = [rates[t]["predicted_fpr"] for t in a["included"]]
    ys = [rates[t]["real_fpr"] for t in a["included"]]
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.scatter(xs, ys, s=26, color=BLUE, alpha=0.55, zorder=3, edgecolors=SURFACE, linewidths=0.6)
    for d in a["disagreements"]["missed_by_audit"][:4]:
        ax.annotate(d["entry_point"], (d["predicted_fpr"], d["real_fpr"]), xytext=(7, -3),
                    textcoords="offset points", fontsize=8, color=INK_SOFT)
    for d in a["disagreements"]["false_alarms"][:1]:
        ax.annotate(d["entry_point"], (d["predicted_fpr"], d["real_fpr"]), xytext=(-8, -3),
                    textcoords="offset points", fontsize=8, color=INK_SOFT, ha="right")
    p = a["primary"]
    ax.text(0.98, 0.97, f"Spearman rho = {p['rho']:.2f}\n95% interval {p['ci_low']:.2f} to {p['ci_high']:.2f}\n"
                        f"{p['n']} problems", transform=ax.transAxes, ha="right", va="top",
            fontsize=9, color=INK, bbox={"facecolor": SURFACE, "edgecolor": GRID, "boxstyle": "round,pad=0.4"})
    ax.set_xlabel("predicted: mutants that pass HumanEval's tests\n(share of mutants that HumanEval+ rejects)")
    ax.set_ylabel("real: model-written wrong solutions that pass\n(share of solutions HumanEval+ rejects)")
    ax.set_xlim(-0.03, max(max(xs) * 1.08, 0.3))
    ax.set_ylim(-0.03, max(max(ys) * 1.12, 0.3))
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(color=GRID, linewidth=0.8, zorder=0)
    ax.tick_params(length=0)
    ax.set_title("Mutant survival doesn't predict real slips")
    fig.text(0.012, 0.012, "One dot per HumanEval problem. Labelled: problems where the audit & reality disagree most.",
             fontsize=8, color=INK_SOFT)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "evalplus_scatter.png")
    plt.close(fig)


def results_markdown(audit: dict, hacks: dict, evalplus: dict | None, review: dict | None) -> str:
    s = audit["summary"]
    lines = ["# Key numbers", "", "## Mutation audit (12 tasks)", "",
             f"{s['total_mutants']} mutants, {s['total_likely_equivalent']} likely equivalent, "
             f"{s['total_mutants'] - s['total_likely_equivalent']} real bugs.", "",
             "| suite | real bugs passed | false-positive rate (mean of tasks) | mutation score |", "|---|---|---|---|"]
    for suite in SUITES:
        o = s["overall"][suite]
        lines.append(f"| {suite} | {o['passed']} of {o['real_bugs']} | {pct(o['mean_false_positive_rate'])} | "
                     f"{pct(1 - o['mean_false_positive_rate'])} |")
    lines += ["", "### Per task (false-positive rate)", "", "| task | mutants | equivalent | " + " | ".join(SUITES) + " |",
              "|---|---|---|" + "---|" * len(SUITES)]
    for task, info in s["per_task"].items():
        cells = " | ".join(pct(info["suites"][x]["false_positive_rate"]) for x in SUITES)
        lines.append(f"| {task} | {info['mutants']} | {info['likely_equivalent']} | {cells} |")
    lines += ["", "## Reward hacks (share of 12 tasks where the hack passes)", "",
              "| hack | " + " | ".join(SUITES) + " |", "|---|" + "---|" * len(SUITES)]
    for hack in HACKS:
        lines.append(f"| {hack} | " + " | ".join(pct(hacks["summary"]["by_hack"][hack][x]) for x in SUITES) + " |")
    lines.append("| **all hacks** | " + " | ".join(pct(hacks["summary"]["by_suite"][x]) for x in SUITES) + " |")
    if review:
        lines += ["", "## Hand check", "", f"Agreement on {review['sample_size']} random mutants: {review['agreement']:.0%}. "
                  f"Flagged-equivalent mutants reviewed: {review['flagged_equivalent']} "
                  f"({review['flagged_unconditional']} equivalent on any input)."]
    if evalplus:
        a = evalplus["analysis"]
        t = a["totals"]
        lines += ["", "## EvalPlus realism check", "",
                  f"{a['problems']} problems, {len(a['included'])} included. {t['mutants']} mutants, {t['samples']} model samples.", "",
                  "| analysis | Spearman rho | 95% interval | p | problems |", "|---|---|---|---|---|"]
        for label, key in [("predicted FPR vs real FPR (primary)", "primary"),
                           ("same, distinct samples only", "distinct_samples"),
                           ("predicted FPR vs real false-discovery rate", "false_discovery_rate")]:
            r = a[key]
            lines.append(f"| {label} | {r['rho']:.2f} | {r['ci_low']:.2f} to {r['ci_high']:.2f} | {r['p_value']:.2g} | {r['n']} |")
        sep = a["separation"]
        lines += ["", f"AUC {sep['auc']:.2f}; flagged {sep['problems_flagged']}, with real false positives "
                  f"{sep['problems_with_real_fp']}, both {sep['flagged_and_real']}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    audit, hacks = load("audit.json"), load("hacks.json")
    if audit is None or hacks is None:
        raise SystemExit("run `python audit.py` & `python hacks_eval.py` first")
    evalplus, review = load("evalplus.json"), load("review.json")
    FIGURES.mkdir(exist_ok=True)
    plot_fpr_by_suite(audit)
    plot_hack_heatmap(hacks)
    plot_mutants_vs_hacks(audit, hacks)
    if evalplus:
        plot_evalplus(evalplus)
    else:
        print("outputs/evalplus.json not found: skipping the EvalPlus plot (run `python evalplus_check.py`)")
    (OUTPUTS / "results.md").write_text(results_markdown(audit, hacks, evalplus, review))
    print("wrote figures/*.png & outputs/results.md")


if __name__ == "__main__":
    main()
