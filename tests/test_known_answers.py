"""Audit the audit: suites whose correct answer is known in advance.

The empty suite asserts nothing, so it must pass (almost) every real bug.
The oracle suite compares against a brute-force oracle on 500 random
inputs, so it must pass (almost) none. If the audit reports anything else
for these two, the audit is wrong & no other number it prints can be
trusted.

This runs the whole audit once (about a minute).
"""
import math

import pytest

from audit import audit_task, consistency_problems, summarize
from run_suite import list_tasks


@pytest.fixture(scope="module")
def results():
    return [audit_task(task) for task in list_tasks()]


@pytest.fixture(scope="module")
def summary(results):
    return summarize(results)


def test_empty_suite_passes_essentially_every_real_bug(summary):
    assert summary["overall"]["empty"]["pooled_false_positive_rate"] >= 0.99
    for task, info in summary["per_task"].items():
        assert info["suites"]["empty"]["false_positive_rate"] >= 0.95, task


def test_oracle_suite_passes_essentially_no_real_bug(summary):
    assert summary["overall"]["oracle"]["pooled_false_positive_rate"] <= 0.02
    for task, info in summary["per_task"].items():
        assert info["suites"]["oracle"]["false_positive_rate"] <= 0.10, task


def test_no_consistency_problems(results):
    # weak < medium < strong must be monotonic, & a mutant flagged equivalent
    # must pass every suite.
    assert consistency_problems(results) == []


def test_weaker_suites_never_look_better_than_stronger_ones(summary):
    for task, info in summary["per_task"].items():
        rate = {s: info["suites"][s]["false_positive_rate"] for s in info["suites"]}
        assert rate["empty"] >= rate["weak"] >= rate["medium"] >= rate["strong"], (task, rate)


def test_equivalent_mutants_are_a_small_minority(summary):
    share = summary["total_likely_equivalent"] / summary["total_mutants"]
    assert 0 < share < 0.15, share


def test_rates_are_consistent_with_counts(summary):
    for info in summary["per_task"].values():
        for stats in info["suites"].values():
            assert stats["passed"] + stats["failed"] == stats["real_bugs"]
            assert math.isclose(stats["false_positive_rate"] + stats["mutation_score"], 1.0)


def test_summarize_on_a_hand_made_example():
    def mutant(equivalent, weak, strong):
        suites = {s: {"passed": True, "reason": "pass"} for s in ["empty", "weak", "medium", "strong", "oracle"]}
        suites["weak"]["passed"] = weak
        suites["medium"]["passed"] = strong
        suites["strong"]["passed"] = strong
        suites["oracle"]["passed"] = equivalent
        return {"id": "m", "equivalent": equivalent, "suites": suites}

    fake = [{"task": "t", "mutants": [mutant(True, True, True), mutant(False, True, False),
                                      mutant(False, True, False), mutant(False, False, False),
                                      mutant(False, False, False)]}]
    s = summarize(fake)["per_task"]["t"]
    assert s["mutants"] == 5 and s["likely_equivalent"] == 1
    assert s["suites"]["weak"]["real_bugs"] == 4            # the equivalent one is left out
    assert s["suites"]["weak"]["false_positive_rate"] == 0.5
    assert s["suites"]["strong"]["false_positive_rate"] == 0.0
    assert s["suites"]["empty"]["false_positive_rate"] == 1.0
    assert consistency_problems(fake) == []
    broken = [{"task": "t", "mutants": [mutant(False, False, True)]}]
    assert consistency_problems(broken) == ["t/m: fails weak but passes medium"]
