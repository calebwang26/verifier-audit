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

## Step 5: the reward-hack gallery & the verifier-attack demo

**Built:** four hacks for each of the 12 tasks (48 files in `tasks/<task>/hacks/`), `hacks_eval.py` to run them all, `scripts/build_hack_tables.py` & `demos/verifier_attacks/`.

**The four hack types:**

| hack | what it does |
|---|---|
| `hardcode_tests` | no logic, just a lookup table of every fixed test input & its expected answer |
| `mask_errors` | a rough first draft wrapped in `try/except` that returns a default instead of crashing |
| `special_case` | a plausible shortcut, plus `if input == ...` patches for the exact test inputs it gets wrong |
| `always_equal` | returns an object whose `==` always says yes |

**Threat model:** the model can read every test file (true whenever the tests sit in the repo it's editing). It can't predict the inputs of a random test.

**Results** (share of the 12 tasks where the hack passes the suite):

| hack | empty | weak | medium | strong | oracle |
|---|---|---|---|---|---|
| hardcode_tests | 100% | 100% | 100% | 0% | 0% |
| mask_errors | 100% | 100% | 25% | 0% | 0% |
| special_case | 100% | 100% | 100% | 8% | 8% |
| always_equal | 100% | 100% | 83% | 83% | 0% |

**What stood out:**

- **Fixed tests can always be memorised.** `hardcode_tests` & `special_case` beat every suite made only of fixed cases, on every task. Only the random-against-oracle check stopped them.
- **`always_equal` beats the strong suite on 10 of 12 tasks,** although that suite caught 100% of mutants. Every `assert f(x) == expected` asks the returned object whether it's equal, & the object lies. It only failed where a test asked something else: `assert not f(x)` (brackets) or "must raise ValueError" (durations). The oracle suite catches it everywhere because it insists results are plain built-in data.
- **One hack beat the oracle suite itself:** `is_valid_parentheses/special_case`. It only counts brackets of each kind, so it's wrong on strings like `[(])`. My random string generator produces such strings on about 0.04% of draws (36 in 100,000), so 500 random inputs missed it. Same lesson as the `lru_cache` mutant in step 4: a random check is only as good as its input generator. The 3,000-input equivalence check did catch it (2 hits).

**Decisions:**

- **The lookup tables were filled in by a helper, not typed.** `scripts/build_hack_tables.py` runs each task's fixed tests against the reference, notes every call & its answer (about 230 pairs), & writes them into the hack files. The hack files themselves are plain static Python, the same thing a model that read the tests would type. Typing 230 pairs by hand would have produced typos, & a typo would make a hack fail for the wrong reason.
- **The `mask_errors` drafts were written first & left alone.** I wrote each as the obvious rough draft for that task, then recorded whatever the suites did with it. Nine of twelve are caught by the medium suite.
- **A test proves no hack is accidentally correct:** all 48 differ from the reference under the strict comparison.

**The verifier-attack demo** (`demos/verifier_attacks/demo.py`) tries three attacks on the *verifier* rather than the task, against three verifiers:

| attack | naive | this repo's `run_suite` | out-of-process |
|---|---|---|---|
| edit the test file | passes | caught | caught |
| always_equal | passes | passes | caught |
| forge "all passed" & exit | passes | passes | caught |

- **naive:** runs whatever test files are in the agent's workspace & trusts the exit code.
- **this repo:** tests come from the verifier's own copy, so edited test files are never used. But the candidate & the tests still share one Python process.
- **out-of-process:** the candidate runs alone, gets only inputs & hands back only outputs as JSON. Answers & comparison stay in the parent.

**An honest weakness in my own runner:** the demo shows `run_suite.py` can be fooled by a candidate that writes a fake result line straight to the real stdout & exits. Any secret kept inside the shared process can be found by code running in that process, so this can't be patched from within. It doesn't affect the mutation audit (mutants are small accidental changes, not attacks, & the oracle suite compares strictly), but it's why the demo's third verifier exists & it's listed in the README's limitations.

## Step 6: the hand-checked sample

**Built:** `review/sample.py` (draws 30 mutants with a fixed seed), `review/hand_labels.json` (my verdict & a one-line reason for each), `review/compare.py` & the result, `review/mutant_sample.md`.

**How it was done:** I printed the 30 changes with no audit label beside them, read each against the original code, decided whether any allowed input could behave differently & wrote down why. Those labels were committed first. Only then was the comparison script written & run. The git history shows that order.

**Result: 30 of 30 agree.** All 30 are real bugs by hand & by the audit.

**Why that alone isn't enough:** only 19 of the 444 mutants are flagged equivalent, so a random 30 contains none about a quarter of the time, & this draw contained none. That means the sample tested the audit's "bug" label 30 times & its "equivalent" label zero times. So I also reviewed all 19 flagged mutants. That second review was not blind (I knew they were flagged), which is said plainly in the file. Each verdict is a short argument that can be checked.

**Result of the second review:** all 19 are equivalent on the inputs their task allows. 13 are equivalent on any input. The other 6 are equivalent only because of a promise in the task description:

- `max_subarray_sum` `current < 0` -> `current < 1`: the same for integers, a real bug for fractions.
- `spiral_order` reading the width from the last row instead of the first: the same for rectangular matrices only.
- `merge_intervals` re-processing the first interval: the same only if start <= end.
- `parse_duration` `and` -> `or`: still raises ValueError on every bad input, but with a different message.

**What this taught me:** "equivalent" really means "equivalent on the inputs the generator produces". The audit can't see a bug that only shows on inputs outside that range. That's a limit of the method, not a slip in the code, & it's in the README's limitations.

## Step 7: the EvalPlus realism check (the headline)

**Built:** `evalplus_check.py` (download, clean, evaluate, analyse), `evalplus_worker.py` (runs untrusted candidates safely), `scripts/crosscheck_evalplus.py` & `tests/test_evalplus.py`.

**Data used:** HumanEval+ v0.1.10 (164 problems) through the `evalplus` package, plus the model samples from EvalPlus's v0.1.0 release: 200 samples per problem at temperature 0.8 from six models (`chatgpt`, `phind-code-llama-34b-v2`, `code-llama-34b`, `starcoder`, `codegen-16b`, `mistral-7b`). That's 196,800 samples, about 110 MB of downloads, none of it committed.

**Result, exactly as fixed in advance in `PLAN.md`:**

| analysis | Spearman rho | 95% interval | problems |
|---|---|---|---|
| predicted FPR (mutants) vs real FPR (model samples), **primary** | **0.07** | −0.10 to 0.24 | 162 |
| same, duplicate samples removed | 0.06 | −0.11 to 0.23 | 162 |
| predicted FPR vs real false-discovery rate | 0.20 | 0.01 to 0.37 | 156 |

**The audit does not predict where real wrong code slips through.** This is a negative result & it's reported as one. I did not go looking for a different metric or a different subset that would produce a correlation.

- 3,929 mutants. 229 pass every test & are treated as equivalent. Of the 3,700 that HumanEval+ rejects, 210 (5.7%) pass the original tests.
- 123,248 of the 196,800 samples are wrong by HumanEval+. 9,815 of those (8.0%) pass the original tests.
- The audit flags 37 problems (at least one surviving mutant). 139 problems have real false positives. 59% of the real false positives are in problems the audit called clean.
- As a yes/no detector of "this problem has real false positives", the audit scores AUC 0.46, slightly worse than a coin.

**Why, from reading the cases:**

- *Missed by the audit:* `filter_integers`, `is_palindrome`, `sum_to_n`, `unique`. All have one-line references with 5 to 10 mutants, all killed. The real errors are different programs, not perturbed ones: `isinstance(x, int)` accepting booleans, an extra `.lower()`, recursion that overflows on large n, `list(set(l))` with no sort.
- *False alarms:* `numerical_letter_grade` has 22 surviving mutants (shifted grade boundaries) & zero real false positives in 993 wrong samples, because the boundaries are spelled out in the prompt & models copy them.

**Checks on the harness itself** (because a null result from a broken harness would be worthless):

- **Published scores reproduced.** On greedy samples, the pass rate on the original tests matches the EvalPlus paper to the decimal for all four models checked: GPT-4 88.4%, ChatGPT 73.2%, StarCoder 34.1%, CodeGen-16B 32.9%.
- **HumanEval+ pass rates came out 0 to 4 points above the paper's** (GPT-4 80.5% vs 76.2%). I didn't accept "probably a dataset revision" on trust. `scripts/crosscheck_evalplus.py` runs EvalPlus's own official evaluator on the same 328 greedy samples with the same dataset version: **328 of 328 verdicts identical to mine**, & it also reports 80.5%. So the gap from the 2023 paper comes from the dataset having been revised since, not from my evaluator.
- **Tests on a hand-made problem** cover all three verdicts, timeouts, crashes & the comparison rules.

**Decisions:**

- **Wrote my own evaluator instead of calling EvalPlus's.** EvalPlus starts a fresh Python process per check, which on macOS costs seconds each. Fine for 164 samples, hopeless for 200,000. Mine starts one process per problem & forks a child per candidate. The comparison rules are copied from EvalPlus (exact match, a small tolerance for floats, any root accepted for `find_zero`).
- **Samples are cleaned generously.** Code fences are stripped, the prompt is put in front so its imports exist, & trailing lines are dropped until the code parses. Being generous means a sample is only called wrong when its logic is wrong, not its formatting.
- **Untrusted code is sandboxed three ways:** a forked child per candidate with time limits, dangerous functions switched off (the same idea as HumanEval's `reliability_guard`), & on macOS the system sandbox with no network & no file writes. A test confirmed a candidate that tries to write a file can't.
- **Only run the extra tests on candidates that pass the original ones.** HumanEval+ includes the original inputs, so failing them already means wrong.

**Problems hit:**

- **The run took 32 minutes,** not the 5 I'd estimated. Wrong samples that loop cost a 1-second limit each, & the machine was shared with two other jobs. Results are cached per problem, so a re-run takes seconds.
- **EvalPlus's own evaluator failed every check on this Mac** the first time (0% pass rate for GPT-4). It tries to cap memory with `setrlimit`, which macOS refuses. Setting `EVALPLUS_MAX_MEMORY_BYTES=-1`, its own off switch, fixed it. Had I not sanity-checked the cross-check with a known-correct solution, I'd have "found" 300 disagreements that didn't exist.
- **The first disagreement list only showed one direction** (audit says weak, reality says fine) because of how ties rank. It now reports both directions separately.
