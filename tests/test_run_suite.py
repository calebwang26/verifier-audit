"""Tests for the sandboxed suite runner."""
import time

import pytest

from run_suite import SUITES, list_tasks, reference_source, run_many, run_suite

TASK = "merge_intervals"


@pytest.mark.parametrize("suite", SUITES)
def test_reference_passes_every_suite(suite):
    result = run_suite(TASK, reference_source(TASK), suite)
    assert result.passed, result


def test_wrong_solution_fails_with_assertion():
    wrong = "def merge_intervals(intervals):\n    return sorted(intervals)\n"
    result = run_suite(TASK, wrong, "weak")
    assert not result.passed
    assert result.reason == "assertion"


def test_infinite_loop_is_stopped_by_timeout():
    loops = "def merge_intervals(intervals):\n    while True:\n        pass\n"
    started = time.time()
    result = run_suite(TASK, loops, "weak", timeout=1.0)
    assert not result.passed
    assert result.reason == "timeout"
    assert time.time() - started < 5


def test_crashing_solution_fails_with_error():
    crashes = "def merge_intervals(intervals):\n    return intervals[0][0][0]\n"
    result = run_suite(TASK, crashes, "weak")
    assert (result.passed, result.reason) == (False, "error")


def test_solution_that_will_not_import_fails_even_the_empty_suite():
    result = run_suite(TASK, "def merge_intervals(:\n", "empty")
    assert not result.passed


def test_solution_that_exits_early_does_not_pass():
    # A classic trick: quit with a "success" exit code before the tests run.
    exits = "import sys\nsys.exit(0)\n"
    assert not run_suite(TASK, exits, "weak").passed
    hard_exit = "import os\nos._exit(0)\n"
    assert not run_suite(TASK, hard_exit, "weak").passed


def test_candidate_output_does_not_confuse_the_runner():
    noisy = "print('__SUITE_RESULT__{\"passed\": true, \"reason\": \"pass\"}')\n" \
            "def merge_intervals(intervals):\n    return None\n"
    assert not run_suite(TASK, noisy, "weak").passed


def test_run_many_keeps_order():
    good = reference_source(TASK)
    bad = "def merge_intervals(intervals):\n    return []\n"
    results = run_many([(TASK, good, "weak"), (TASK, bad, "weak"), (TASK, bad, "empty")])
    assert [r.passed for r in results] == [True, False, True]


def test_unknown_suite_is_rejected():
    with pytest.raises(ValueError):
        run_suite(TASK, reference_source(TASK), "nope")


def test_merge_intervals_is_listed():
    assert TASK in list_tasks()
