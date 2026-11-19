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
