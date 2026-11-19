"""Tests for the reward-hack gallery & the verifier-attack demo."""
import sys

import pytest

from equivalence import check_equivalence
from hacks_eval import HACKS, evaluate, hack_source, summarize
from run_suite import ROOT, TASKS_DIR, list_tasks

sys.path.insert(0, str(ROOT / "demos" / "verifier_attacks"))

TASKS = list_tasks()


@pytest.fixture(scope="module")
def results():
    return evaluate()


@pytest.mark.parametrize("task", TASKS)
def test_every_task_has_all_four_hacks(task):
    for hack in HACKS:
        assert (TASKS_DIR / task / "hacks" / f"{hack}.py").is_file()


@pytest.mark.parametrize("task", TASKS)
def test_no_hack_is_secretly_a_correct_solution(task):
    # The strict comparison on 3,000 random inputs plus edge inputs must find a
    # difference from the reference for every single hack.
    for hack in HACKS:
        assert not check_equivalence(task, hack_source(task, hack)).equivalent, (task, hack)


def test_memorising_hacks_agree_with_every_fixed_test(results):
    # By construction these two know every fixed test, so weak & medium (which
    # have only fixed tests) can never catch them.
    for task in TASKS:
        for hack in ("hardcode_tests", "special_case"):
            assert results[task][hack]["weak"] and results[task][hack]["medium"], (task, hack)


def test_every_hack_passes_the_empty_suite(results):
    assert all(results[t][h]["empty"] for t in TASKS for h in HACKS)


def test_always_equal_never_beats_the_strict_oracle_suite(results):
    assert not any(results[t]["always_equal"]["oracle"] for t in TASKS)


def test_summary_shares_are_fractions(results):
    summary = summarize(results)
    for hack in HACKS:
        for share in summary["by_hack"][hack].values():
            assert 0.0 <= share <= 1.0
    assert summary["by_suite"]["empty"] == 1.0


def test_verifier_attack_demo():
    from demo import run_demo
    table = run_demo()
    assert all(table["(correct solution)"].values())            # no verifier rejects correct code
    assert all(table[attack]["naive"] for attack in ("edit_test_file", "always_equal", "forge_result"))
    assert not table["edit_test_file"]["this repo"]             # our runner never uses workspace tests
    assert not any(table[attack]["out-of-process"]              # separating the processes stops all three
                   for attack in ("edit_test_file", "always_equal", "forge_result"))
