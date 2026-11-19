"""Tests for the EvalPlus realism check. None of them needs a download:
they use a tiny hand-made problem in the same format as HumanEval+."""
import pytest

import evalplus_check as ec
import evalplus_worker as worker

PROMPT = 'def add_abs(a, b):\n    """Return |a| + |b|."""\n'
PROBLEM = {
    "task_id": "Toy/0", "entry_point": "add_abs", "atol": 0, "prompt": PROMPT,
    "canonical_solution": "    return abs(a) + abs(b)\n",
    "base_input": [[1, 2], [3, 4]],                 # the "original" tests: positive numbers only
    "plus_input": [[-1, 2], [0, 0], [-5, -6]],      # the extra tests add negatives
}


@pytest.fixture(autouse=True)
def no_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ec, "CACHE_DIR", tmp_path / "cache")


def run(candidates):
    return ec.evaluate_problem(PROBLEM, candidates, prefix=[])


def test_three_verdicts():
    correct = PROMPT + "    return abs(a) + abs(b)\n"
    passes_base_only = PROMPT + "    return a + b\n"          # right for positives, wrong for negatives
    plainly_wrong = PROMPT + "    return 0\n"
    assert run([correct, passes_base_only, plainly_wrong]) == ["O", "P", "B"]


def test_broken_looping_and_crashing_candidates_all_fail_base():
    will_not_parse = "def add_abs(:\n"
    loops = PROMPT + "    while True:\n        pass\n"
    crashes = PROMPT + "    return a.missing\n"
    exits = PROMPT + "    import sys\n    sys.exit(0)\n"
    assert run([will_not_parse, loops, crashes, exits]) == ["B", "B", "B", "B"]


def test_loop_only_on_plus_inputs_counts_as_passing_base():
    code = PROMPT + "    while a < 0:\n        pass\n    return abs(a) + abs(b)\n"
    assert run([code]) == ["P"]


def test_dangerous_calls_are_switched_off():
    code = PROMPT + "    import os\n    os.system('true')\n    return abs(a) + abs(b)\n"
    assert run([code]) == ["B"]        # os.system is None inside the child, so the call raises


def test_results_are_cached(tmp_path):
    code = PROMPT + "    return a + b\n"
    assert run([code]) == ["P"]
    assert len(list(ec.CACHE_DIR.glob("Toy_0_*.json"))) == 1
    assert run([code]) == ["P"]


def test_output_comparison_rules():
    assert worker.same("f", 0, [1], 3, 3)
    assert not worker.same("f", 0, [1], 3, 4)
    assert worker.same("f", 0, [1], 0.1 + 0.2, 0.3)             # floats get a small tolerance
    assert worker.same("f", 0, [1], [1.0, 2.0000001], [1.0, 2.0])
    assert not worker.same("f", 0, [1], [1.0, 2.1], [1.0, 2.0])
    assert not worker.same("f", 0, [1], (1.0, 2.0), [1.0, 2.0])  # a tuple is not a list
    assert worker.same("find_zero", 1e-4, [[-6, 11, -6, 1]], 2.0, 1.0)   # any root is accepted
    assert not worker.same("find_zero", 1e-4, [[-6, 11, -6, 1]], 2.5, 1.0)


def test_clean_sample_strips_fences_and_adds_the_prompt():
    raw = "```python\ndef add_abs(a, b):\n    return abs(a) + abs(b)\n```"
    code = ec.clean_sample(PROMPT, raw)
    assert code.startswith(PROMPT) and "```" not in code
    assert run([code]) == ["O"]


def test_clean_sample_drops_trailing_rambling():
    raw = "python\ndef add_abs(a, b):\n    return abs(a) + abs(b)\n\nprint(add_abs(1, 2)\nand then some ( text"
    code = ec.clean_sample(PROMPT, raw)
    assert "and then" not in code
    assert run([code]) == ["O"]


def test_clean_sample_keeps_a_bare_function_body():
    assert run([ec.clean_sample(PROMPT, "    return abs(a) + abs(b)")]) == ["O"]


def test_problem_rates():
    result = {"mutants": [{"status": s} for s in "BBBPPO"],
              "samples": [{"count": 10, "status": "B"}, {"count": 5, "status": "P"},
                          {"count": 1, "status": "P"}, {"count": 4, "status": "O"}]}
    r = ec.problem_rates(result)
    assert r["mutants_wrong"] == 5 and r["mutants_fp"] == 2 and r["predicted_fpr"] == 0.4
    assert r["samples_wrong"] == 16 and r["samples_fp"] == 6 and r["real_fpr"] == 6 / 16
    assert r["real_fdr"] == 6 / 10
    assert r["real_fpr_distinct"] == 2 / 3


def test_auc():
    assert ec.auc([0.9, 0.8, 0.1, 0.2], [True, True, False, False]) == 1.0
    assert ec.auc([0.1, 0.2, 0.9, 0.8], [True, True, False, False]) == 0.0
    assert ec.auc([0.5, 0.5], [True, False]) == 0.5
    assert ec.auc([0.5, 0.5], [True, True]) is None


def test_spearman_interval_on_a_perfect_relationship():
    x = [float(i) for i in range(20)]
    r = ec.spearman_with_interval(x, [v * 2 for v in x])
    assert r["rho"] == pytest.approx(1.0) and r["ci_low"] == pytest.approx(1.0) and r["n"] == 20
