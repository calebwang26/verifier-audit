# Plan

**Question:** how often do test suites pass wrong code, & how easily can a model game them?

Written before any code, so the method & the headline analysis are fixed before the results are known.

## What gets built

1. **12 small coding tasks** (`tasks/<name>/`), each with:
   - `solution.py`: the correct reference solution (the source for mutants)
   - `spec.py`: a slow, independently written brute-force **oracle**, a random input generator & hand-picked edge inputs
   - `suite_weak.py`, `suite_medium.py`, `suite_strong.py`: three test suites of rising strength (every weak test is also in medium, every medium test is also in strong)
   - `hacks/`: four hand-written reward hacks
2. **Two reference suites shared by every task** (`tasks/_shared/`): `suite_empty.py` (no assertions) & `suite_oracle.py` (oracle vs candidate on 500 random inputs). These have known answers, so they test the audit itself.
3. **`mutate.py`:** AST mutation engine with seven operators. Generates every single-point mutant of a solution.
4. **`run_suite.py`:** runs one suite against one candidate in a fresh folder, in a subprocess, with a timeout.
5. **`equivalence.py`:** flags likely-equivalent mutants (same output as the reference on thousands of random inputs & all edge inputs) so they can be excluded.
6. **`audit.py`:** for every task, mutant & suite, records pass or fail, then computes the mutation score & the false-positive rate.
7. **`hacks_eval.py`:** runs every hack against every suite. `demos/test_tamper/` shows a "solution" that edits the test file.
8. **`review/`:** 30 randomly drawn mutants, judged by hand before looking at the audit's label for them.
9. **`evalplus_check.py`:** the realism check on real model-written code (below).
10. **`report.py`:** plots & tables.

One command runs everything: `make all`.

## Definitions

- **Mutant:** the reference solution with one small change.
- **Equivalent mutant:** a mutant that behaves the same as the reference on every input. Not a bug, so it's excluded.
- **Real bug:** a non-equivalent mutant.
- **Mutation score** of a suite = real bugs the suite fails ÷ all real bugs.
- **Verifier false-positive rate (FPR)** of a suite = real bugs the suite passes ÷ all real bugs = 1 − mutation score.

## Checks that the audit itself is right

1. **Known answers:** the empty suite must pass ~100% of real bugs & the oracle suite ~0%. Written as pytest tests.
2. **Monotonic kills:** because weak ⊂ medium ⊂ strong, a mutant failed by a weaker suite must also be failed by the stronger one. Any violation means the runner is flaky.
3. **Hand-checked sample:** 30 seeded random mutants labelled by hand, compared with the audit's labels.
4. **Hack cross-check:** mutation FPR vs the share of hacks each suite lets through.
5. **EvalPlus realism check** (headline).

## EvalPlus analysis, fixed in advance

Data: HumanEval problems, HumanEval's original test inputs (`base_input`), HumanEval+'s extra inputs (`plus_input`) & the model-written solutions EvalPlus released (v0.1.0 release, temperature 0.8, 200 samples per problem per model). Ground truth for "wrong" = fails at least one base or plus input, compared against the canonical solution's output.

Per problem:

- **Predicted FPR (from mutants)** = mutants that pass the base tests but fail the plus tests ÷ mutants that fail the plus tests.
- **Real FPR (from model samples)** = samples that pass the base tests but fail the plus tests ÷ samples that fail the plus tests.

**Primary result:** Spearman rank correlation between predicted FPR & real FPR across problems, using all samples (duplicates kept, since they reflect what models actually produce). Included problems: at least 5 mutants that fail the plus tests & at least 20 wrong samples. Reported with a bootstrap 95% interval over problems.

**Secondary results** (reported whatever they show):

- the same correlation with duplicate samples removed
- predicted FPR vs the real **false-discovery rate** (wrong samples ÷ samples that pass the base tests)
- how well "predicted FPR > 0" separates problems that have at least one real false positive from those that have none (AUC)
- the five problems where prediction & reality disagree most, each read & explained by hand

If the correlation is weak or absent, the README says so.

## Order of work (one branch & pull request per slice)

1. `setup`: safety files, CI, this plan
2. `runner`: `run_suite.py`, shared suites, first task
3. `tasks`: remaining 11 tasks
4. `mutate`: mutation engine & its tests
5. `audit`: equivalence check, metrics, known-answer tests
6. `hacks`: hack gallery & tamper demo
7. `review`: hand-checked sample
8. `evalplus`: realism check
9. `report`: plots, cross-check, README
10. `docs`: EXPLAIN.md, final BUILDLOG.md

## Afterwards: what changed from this plan

Kept as written so the plan can be compared with what happened.

- **The analysis of the EvalPlus check was run exactly as fixed above.** No inclusion rule, metric or model list was changed after seeing results.
- **Order of work:** `report` came after `evalplus` rather than before, because one of the plots needs its results. An extra `ci-fix` pull request was needed early on (see `BUILDLOG.md`, step 1b).
- **Additions not in the plan:** a fourth hack type (`always_equal`), the verifier-attack demo's out-of-process checker, a review of all 19 flagged-equivalent mutants, & a cross-check of the EvalPlus evaluator against EvalPlus's own.
