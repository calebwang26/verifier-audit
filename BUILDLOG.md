# Build log

What was built in each step, the decisions made & why, & the problems hit along the way. Newest entries at the bottom.

## Step 0: setup & safety files

**Built:** `.gitignore`, `.gitleaks.toml`, a pre-commit hook that runs the gitleaks secret scanner on staged changes, a GitHub Actions workflow (pytest + gitleaks on every pull request), the MIT `LICENSE`, `PLAN.md` & pinned `requirements.txt`.

**Decisions:**

- **The plan fixes the headline analysis before any results exist.** `PLAN.md` states exactly how the EvalPlus correlation is computed (which problems are included, which rate is on each axis). That way the result can't be quietly reshaped afterwards to look better.
- **The hook lives in `hooks/` & is switched on with `git config core.hooksPath hooks`** (`make hooks`). A script in `.git/hooks/` isn't tracked by git, so it would vanish on a fresh clone.
- **Two requirements files.** `requirements.txt` is everything. `requirements-ci.txt` leaves out `evalplus`, which pulls in about 90 packages & is only needed to download the HumanEval+ dataset.

**Problems hit:**

- `conda create` failed because Anaconda's default channels now need their Terms of Service accepted. Accepting legal terms is Caleb's call, not mine, so the environment was created from the community `conda-forge` channel instead (`conda create -n verifier-audit --override-channels -c conda-forge python=3.11`). Nothing in the global conda settings was changed.
- Checked the scanner on a throwaway repo: a real-shaped GitHub token was blocked, & the same token with the `FAKE` marker passed. The allowlist behaves as intended.

## Step 1: the suite runner & the first task

**Built:** `run_suite.py`, the shared files in `tasks/_shared/` (the harness that runs inside the sandbox, the empty suite, the oracle suite & `checks.py`) & the first task, `merge_intervals`, with its reference solution, brute-force oracle & weak, medium & strong suites.

**How a run works:** the candidate is written to a fresh temporary folder as `solution.py`, next to the suite files. A separate Python process imports the suite, calls every `test_*` function & prints one result line. The parent waits at most 4 seconds, then kills it.

**Decisions:**

- **A tiny home-made test harness instead of pytest inside the sandbox.** Starting pytest costs about 0.3 seconds per run & the audit does thousands of runs. The suites are still plain `assert` tests, so they read like normal pytest files.
- **Each stronger suite imports the weaker one** (`from suite_weak import *`). So weak ⊂ medium ⊂ strong is true by construction, which later gives a free consistency check: a mutant caught by a weaker suite must be caught by the stronger one.
- **A pass needs two signals to agree:** the harness's result line & exit code 0. A candidate that calls `sys.exit(0)` before the tests run, or prints a fake result line, doesn't pass. Both tricks are covered by tests.
- **`PYTHONHASHSEED=0` in the child process,** so the order of sets & dicts of strings is the same on every run. Without it, results could change from run to run.
- **The oracle suite & the equivalence check compare results strictly** (`checks.outcome`): a result only counts if it's plain built-in data. The ordinary suites use plain `==` like a normal developer would. This difference matters later, in the hack gallery.

**Checked:** the reference passes all five suites, a wrong solution fails with an assertion, & an infinite loop is cut off at the timeout.

## Step 1b: a CI mistake, & the fix

**What went wrong:** pull request 1 was merged while its gitleaks check was red. The rule is that a PR merges only when tests & gitleaks both pass. I had chained "wait for CI" & "merge" in one command in a way that threw away the CI result, so the merge went ahead regardless. That was my error.

**Was anything leaked?** No. The check failed before it scanned anything: on a private repo the gitleaks action isn't allowed to list a pull request's commits unless the workflow asks for `pull-requests: read` (error: "Resource not accessible by integration"). A full local scan of the whole history (`gitleaks detect --log-opts="--all"`) found nothing, & the pre-commit hook had scanned every commit as it was made.

**Fixes:**

- `.github/workflows/ci.yml` now grants the gitleaks job `contents: read` & `pull-requests: read`.
- New `scripts/merge_pr.sh <number>`: waits for the checks & merges only if every one passed. Every later PR is merged through it, so a red check can't be skipped again.

## Step 2: the other eleven tasks

**Built:** `is_valid_parentheses`, `top_k_frequent`, `parse_duration`, `roman_to_int`, `lru_cache`, `binary_search`, `rle_encode`, `max_subarray_sum`, `longest_common_prefix`, `spiral_order` & `count_primes`. Twelve tasks in total, each with a reference solution, an oracle, an input generator, hand-picked edge inputs & three suites.

**How the three suite strengths were defined** (the same rule for every task, decided before any mutant was run):

- **weak:** one or two happy-path examples, the kind you'd find in a docstring.
- **medium:** weak plus the handful of cases a typical repo's test file has (a "not found" case, a second example, one well-known gotcha).
- **strong:** medium plus edge cases (empty input, single element, boundaries, duplicates) plus 200 random inputs compared with the oracle.

**Decisions:**

- **Every oracle uses a different method from the reference.** For example the reference `merge_intervals` sorts & sweeps once, while its oracle keeps merging any two overlapping intervals until nothing changes. If both were written the same way they'd share the same blind spots, & agreeing with each other would prove nothing.
- **Random inputs are deliberately small** (lists of 0 to 10 items, numbers from a narrow range). Small inputs hit the awkward cases (empty, one item, duplicates, ties) far more often than big ones do.
- **`lru_cache` is a class, not a function,** so its "input" is a capacity plus a list of operations & its "output" is the list of what each operation returned. Each task's `spec.apply()` hides that difference, so the rest of the audit treats every task the same way.

**Checked:** all twelve references pass all five suites. Passing the oracle suite means each reference agrees with its independently written oracle on 500 random inputs.

## Step 3: the mutation engine

**Built:** `mutate.py` & `tests/test_mutate.py`. The engine parses a solution into a syntax tree (Python's `ast` module), finds every place one of seven operators applies, & writes out one mutant per place. The twelve tasks yield 444 mutants, between 23 & 83 per task.

**Decisions:**

- **Work on the syntax tree, not on text.** Swapping `<` for `<=` with find-&-replace would also hit comments, strings & `<<`. On the tree, a comparison is a comparison.
- **Only code inside functions is mutated.** Module-level tables (like the Roman numeral values) & docstrings are left alone.
- **No twin mutants.** Three rules stop two operators producing the same wrong program twice, which would count one bug double:
  - `stmt_delete` skips `return x`, because deleting it behaves exactly like `return_const`'s `return None`.
  - `cond_negate` skips a plain `a == b` test, because `cmp_swap` already turns it into `a != b`.
  - Any mutant whose code is identical to an earlier one is dropped.
- **`return_const` tries five constants:** `None`, `""`, `[]` & either `True`/`False` (if the function looks like it returns booleans) or `0`/`1`. `0` & `False` behave the same under `==`, so trying both would again count one bug twice.
- **Mutants are described by the line they change** (`` `if start <= last[1]:` -> `if start < last[1]:` ``), which makes the hand review readable.

**Problem hit:** one of my own tests was wrong. It claimed `stmt_delete` never removes a `return`, but deleting a whole `if` block legitimately removes the `return` inside it. The engine was right & the test was fixed to say what's actually promised.

## Step 4: equivalent mutants, the audit & the known-answer checks

**Built:** `equivalence.py` (flags likely-equivalent mutants), `audit.py` (runs every mutant against every suite & computes the rates) & three test files. The full audit takes about a minute.

**First real numbers** (share of real bugs each suite passes, averaged over the 12 tasks):

| suite | empty | weak | medium | strong | oracle |
|---|---|---|---|---|---|
| false-positive rate | 100% | 33% | 16% | 0% | 0.3% |

444 mutants, of which 19 (4%) were flagged likely equivalent & left out, leaving 425 real bugs.

**Decisions:**

- **Equivalence is checked on 3,000 random inputs plus each task's hand-picked edge inputs,** with a different random seed from the ones the suites use. A mutant is only called "likely equivalent" if it matches the reference on all of them. "Likely" is deliberate: no amount of testing proves two programs are the same.
- **Each input gets a 1-second alarm in the equivalence check.** A mutant stuck in a loop is recorded as "did not finish" on that input, which counts as different behaviour. Without the alarm every looping mutant would cost the full outer timeout.
- **The overall rate is the average of the 12 per-task rates,** not one big pooled fraction, so `spiral_order` (83 mutants) doesn't outweigh `top_k_frequent` (23). The pooled figure is saved too.
- **Two built-in consistency rules** (`audit.consistency_problems`): a mutant failed by a weaker suite must be failed by the stronger one, & a mutant flagged equivalent must pass every suite. Both hold with zero violations.

**Known-answer result:** the empty suite passes 425 of 425 real bugs (100%). The oracle suite passes 1 of 425 (0.2%). Both are where they must be.

**The one mutant that got past the oracle suite, & why it's worth knowing about:** in `lru_cache`, deleting the line that marks a key as recently used on `get` (the classic LRU bug). I checked whether this was an audit fault. It isn't: with my random operation generator the bug only shows on about 0.8% of inputs (24 of 3,000), because it needs a specific sequence (read an old key, then overflow the cache, then read again). The oracle suite's 500 inputs happened to miss it, which has roughly a 2% chance. The equivalence check's 3,000 inputs caught it, & so did the strong suite, which has a test written for exactly this case. I left the generator & seed alone rather than tune them until the number read 0: the honest lesson is that **random testing is weak against bugs that need a particular sequence of steps, & one targeted test beats 500 random ones there.**

**Problem hit:** another wrong expectation in one of my own tests (I'd miscounted how many consistency violations a made-up example should produce). Fixed the test.
