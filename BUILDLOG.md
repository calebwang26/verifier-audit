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
