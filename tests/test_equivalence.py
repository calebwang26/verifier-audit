"""Tests for the equivalent-mutant check."""
import time

from equivalence import check_equivalence
from run_suite import reference_source

TASK = "merge_intervals"
REFERENCE = reference_source(TASK)


def test_reference_is_equivalent_to_itself():
    assert check_equivalence(TASK, REFERENCE).equivalent


def test_known_equivalent_mutant_is_flagged():
    # Re-assigning an equal value changes nothing.
    mutant = REFERENCE.replace("if end > last[1]:", "if end >= last[1]:")
    assert mutant != REFERENCE
    assert check_equivalence(TASK, mutant).equivalent


def test_known_bug_is_not_flagged_and_has_a_witness():
    # Touching intervals no longer merge.
    mutant = REFERENCE.replace("if start <= last[1]:", "if start < last[1]:")
    assert mutant != REFERENCE
    result = check_equivalence(TASK, mutant)
    assert not result.equivalent
    assert "input" in result.witness and "mutant" in result.witness


def test_bug_only_visible_on_an_edge_input_is_caught():
    # Wrong only for the empty list, which random inputs hit rarely; the
    # hand-picked edge inputs make sure it's tried.
    mutant = REFERENCE.replace("        return []", "        return None")
    assert mutant != REFERENCE
    assert not check_equivalence(TASK, mutant, n_inputs=0).equivalent


def test_infinite_loop_counts_as_a_difference_and_is_cut_off_quickly():
    mutant = REFERENCE.replace("    if not intervals:\n        return []",
                               "    while not intervals:\n        pass")
    assert mutant != REFERENCE
    started = time.time()
    result = check_equivalence(TASK, mutant)
    assert not result.equivalent
    assert "did not finish" in result.witness
    assert time.time() - started < 10


def test_trick_object_is_not_treated_as_equal():
    trick = ("class Anything:\n    def __eq__(self, other):\n        return True\n\n"
             "def merge_intervals(intervals):\n    return Anything()\n")
    result = check_equivalence(TASK, trick)
    assert not result.equivalent
    assert "non-plain" in result.witness


def test_mutant_that_will_not_import_is_not_equivalent():
    assert not check_equivalence(TASK, "def merge_intervals(:\n").equivalent
