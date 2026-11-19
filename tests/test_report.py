"""Smoke test: the report script turns small made-up results into plots & a table."""
import report
from hacks_eval import HACKS
from run_suite import SUITES


def fake_audit():
    rate = {"empty": 1.0, "weak": 0.4, "medium": 0.2, "strong": 0.0, "oracle": 0.0}
    suites = {s: {"real_bugs": 10, "passed": int(rate[s] * 10), "failed": 10 - int(rate[s] * 10),
                  "false_positive_rate": rate[s], "mutation_score": 1 - rate[s]} for s in SUITES}
    per_task = {name: {"mutants": 11, "likely_equivalent": 1, "suites": suites} for name in ("a", "b")}
    overall = {s: {"mean_false_positive_rate": rate[s], "pooled_false_positive_rate": rate[s],
                   "passed": int(rate[s] * 20), "real_bugs": 20} for s in SUITES}
    return {"summary": {"per_task": per_task, "overall": overall, "total_mutants": 22,
                        "total_likely_equivalent": 2}}


def fake_hacks():
    share = {s: 0.5 for s in SUITES}
    return {"summary": {"by_hack": {h: share for h in HACKS}, "by_suite": share,
                        "by_task": {"a": share, "b": share}}}


def fake_evalplus():
    rates = {f"HumanEval/{i}": {"predicted_fpr": i / 20, "real_fpr": (i % 5) / 10} for i in range(10)}
    corr = {"rho": 0.3, "p_value": 0.04, "ci_low": 0.1, "ci_high": 0.5, "n": 10}
    return {"analysis": {"rates": rates, "included": list(rates), "primary": corr, "distinct_samples": corr,
                         "false_discovery_rate": corr, "problems": 10,
                         "disagreements": {"missed_by_audit": [{"entry_point": "f", "predicted_fpr": 0.0, "real_fpr": 0.4}],
                                           "false_alarms": [{"entry_point": "g", "predicted_fpr": 0.45, "real_fpr": 0.0}]},
                         "totals": {"mutants": 100, "samples": 1000},
                         "separation": {"auc": 0.6, "problems_flagged": 5, "problems_with_real_fp": 4,
                                        "flagged_and_real": 3}}}


def test_report_writes_all_plots_and_the_table(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "FIGURES", tmp_path)
    audit, hacks, evalplus = fake_audit(), fake_hacks(), fake_evalplus()
    report.plot_fpr_by_suite(audit)
    report.plot_hack_heatmap(hacks)
    report.plot_mutants_vs_hacks(audit, hacks)
    report.plot_evalplus(evalplus)
    for name in ["fpr_by_suite", "hack_heatmap", "mutants_vs_hacks", "evalplus_scatter"]:
        image = tmp_path / f"{name}.png"
        assert image.is_file() and 5_000 < image.stat().st_size < 500_000
    text = report.results_markdown(audit, hacks, evalplus, {"sample_size": 30, "agreement": 1.0,
                                                           "flagged_equivalent": 2, "flagged_unconditional": 1})
    assert "| weak | 8 of 20 | 40% | 60% |" in text
    assert "Spearman rho" in text and "0.30" in text


def test_percent_formatting():
    assert report.pct(0) == "0%" and report.pct(0.333) == "33%" and report.pct(0.0033) == "0.3%"
