"""Tests for the mutation engine: every operator must produce valid, different code."""
import ast

import pytest

from mutate import OPERATORS, diff, generate_mutants, normalize
from run_suite import list_tasks, reference_source

SAMPLE = '''
"""Module docstring with a number 5 that must not change."""
LIMIT = 10


def clamp_sum(values, low, high):
    """Docstring: returns 1 if ... (this 1 must not change)."""
    total = 0
    for v in values:
        if v > low and v < high:
            total += v
        elif v == low:
            total = total - 1
    while total > 100:
        total -= 10
    evens = [v for v in values if v % 2 == 0]
    label = "big" if total >= 50 else "small"
    if not evens:
        return total
    return total + len(evens)
'''


def by_operator(mutants):
    grouped = {name: [] for name in OPERATORS}
    for m in mutants:
        grouped[m.operator].append(m)
    return grouped


@pytest.fixture(scope="module")
def sample_mutants():
    return generate_mutants(SAMPLE)


@pytest.mark.parametrize("operator", OPERATORS)
def test_each_operator_produces_valid_different_code(sample_mutants, operator):
    produced = by_operator(sample_mutants)[operator]
    assert produced, f"{operator} produced no mutants"
    original = normalize(SAMPLE)
    for m in produced:
        compile(m.source, "<mutant>", "exec")           # valid Python
        assert normalize(m.source) != original, m.description   # really different


def test_mutants_are_unique_and_ids_are_in_order(sample_mutants):
    sources = [m.source for m in sample_mutants]
    assert len(set(sources)) == len(sources)
    assert [m.id for m in sample_mutants] == [f"m{i:03d}" for i in range(1, len(sample_mutants) + 1)]


def test_generation_is_deterministic():
    assert generate_mutants(SAMPLE) == generate_mutants(SAMPLE)


def test_module_level_code_and_docstrings_are_untouched(sample_mutants):
    for m in sample_mutants:
        assert "LIMIT = 10" in m.source
        assert "number 5 that must not change" in m.source
        assert "this 1 must not change" in m.source


def has(mutants, operator, fragment):
    return any(m.operator == operator and fragment in m.source for m in mutants)


def test_cmp_swap_swaps_boundaries_and_equality(sample_mutants):
    assert has(sample_mutants, "cmp_swap", "v >= low and v < high")
    assert has(sample_mutants, "cmp_swap", "v > low and v <= high")
    assert has(sample_mutants, "cmp_swap", "elif v != low")
    assert has(sample_mutants, "cmp_swap", "while total >= 100")


def test_const_offby1_goes_both_ways(sample_mutants):
    assert has(sample_mutants, "const_offby1", "total = 1\n")
    assert has(sample_mutants, "const_offby1", "total = -1\n")
    assert has(sample_mutants, "const_offby1", "total > 101")
    assert has(sample_mutants, "const_offby1", "total > 99")


def test_bool_swap(sample_mutants):
    assert has(sample_mutants, "bool_swap", "v > low or v < high")


def test_arith_swap_covers_binary_and_augmented(sample_mutants):
    assert has(sample_mutants, "arith_swap", "total -= v")
    assert has(sample_mutants, "arith_swap", "total = total + 1")
    assert has(sample_mutants, "arith_swap", "total += 10")
    assert has(sample_mutants, "arith_swap", "return total - len(evens)")


def test_cond_negate_covers_if_while_ternary_and_comprehension(sample_mutants):
    assert has(sample_mutants, "cond_negate", "if not (v > low and v < high)")
    assert has(sample_mutants, "cond_negate", "while not total > 100")
    assert has(sample_mutants, "cond_negate", "'big' if not total >= 50 else 'small'")
    assert has(sample_mutants, "cond_negate", "if evens:")       # `not evens` -> `evens`
    assert has(sample_mutants, "cond_negate", "for v in values if not v % 2 == 0")


def test_cond_negate_skips_plain_equality_tests(sample_mutants):
    # `elif v == low` is already negated by cmp_swap (`v != low`); no twin wanted.
    assert not has(sample_mutants, "cond_negate", "not v == low")


def test_stmt_delete_removes_one_statement(sample_mutants):
    deleted = by_operator(sample_mutants)["stmt_delete"]
    original_count = sum(isinstance(n, ast.stmt) for n in ast.walk(ast.parse(SAMPLE)))
    for m in deleted:
        count = sum(isinstance(n, ast.stmt) for n in ast.walk(ast.parse(m.source)))
        assert count < original_count or "pass" in m.source
    assert any("total = 0" not in m.source for m in deleted)
    # A block's only statement is replaced by `pass`, so the code still parses.
    assert has(sample_mutants, "stmt_delete", "pass")


def test_stmt_delete_never_removes_the_function_or_a_valued_return(sample_mutants):
    # Deleting `return x` behaves exactly like return_const's `return None`, so
    # stmt_delete leaves returns alone. (A return can still vanish when the
    # whole `if` block around it is deleted; that's a different change.)
    for m in by_operator(sample_mutants)["stmt_delete"]:
        assert "def clamp_sum" in m.source
        assert "return total + len(evens)" in m.source
        assert not m.description.startswith("delete `return")


def test_return_const_variants(sample_mutants):
    for constant in ["None", "0", "1", "''", "[]"]:
        assert has(sample_mutants, "return_const", f"return {constant}\n"), constant


def test_return_const_uses_true_false_for_boolean_functions():
    source = "def is_small(x):\n    if x < 0:\n        return False\n    return x < 10\n"
    mutants = generate_mutants(source)
    assert has(mutants, "return_const", "return True\n    return x < 10")
    assert has(mutants, "return_const", "return x < 10") and has(mutants, "return_const", "    return False\n")
    assert not has(mutants, "return_const", "return 0\n")


def test_diff_shows_only_the_change(sample_mutants):
    m = next(m for m in sample_mutants if m.operator == "bool_swap")
    text = diff(SAMPLE, m)
    assert "-        if v > low and v < high:" in text
    assert "+        if v > low or v < high:" in text


def test_code_with_no_functions_has_no_mutants():
    assert generate_mutants("x = 1 + 2\nif x > 2:\n    x -= 1\n") == []


@pytest.mark.parametrize("task", list_tasks())
def test_every_task_mutant_is_valid_and_different(task):
    source = reference_source(task)
    original = normalize(source)
    mutants = generate_mutants(source)
    assert len(mutants) >= 20, f"{task} has only {len(mutants)} mutants"
    assert len({m.source for m in mutants}) == len(mutants)
    for m in mutants:
        compile(m.source, "<mutant>", "exec")
        assert normalize(m.source) != original


def test_every_operator_is_used_somewhere_in_the_tasks():
    used = {m.operator for task in list_tasks() for m in generate_mutants(reference_source(task))}
    assert used == set(OPERATORS)
