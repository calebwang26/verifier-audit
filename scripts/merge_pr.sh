#!/bin/sh
# Merge a pull request only if every CI check passed.
# usage: scripts/merge_pr.sh <pr-number>
#
# The merge commit is made locally & pushed, NOT with GitHub's merge button.
# A merge done on GitHub's side is stamped with the account's primary email
# address unless "Keep my email addresses private" is switched on, which
# would put a personal email into public history. A local merge uses the
# no-reply address from `git config user.email`. GitHub still marks the pull
# request as merged, because its commits arrive on main.
set -eu
pr="$1"
branch=$(gh pr view "$pr" --json headRefName -q .headRefName)

# Checks take a few seconds to register after a push; wait for them to appear.
tries=0
until [ "$(gh pr checks "$pr" 2>/dev/null | grep -c .)" -gt 1 ]; do
  tries=$((tries + 1))
  if [ "$tries" -gt 30 ]; then echo "no checks appeared for PR $pr"; exit 1; fi
  sleep 5
done

if ! gh pr checks "$pr" --watch --interval 10 --fail-fast; then
  echo "checks FAILED for PR $pr; not merging"
  gh pr checks "$pr" || true
  exit 1
fi
echo "all checks passed; merging PR $pr ($branch)"

# Merge in a throwaway worktree so the main working folder is left alone.
git fetch -q origin
work=$(mktemp -d)
git worktree add -q --detach "$work" origin/main
(
  cd "$work"
  git merge -q --no-ff "origin/$branch" -m "Merge pull request #$pr from calebwang26/$branch"
  git push -q origin HEAD:main            # a normal push; never forced
)
git worktree remove --force "$work"
git push -q origin --delete "$branch"
git fetch -q origin
echo "merged PR $pr; merge commit author: $(git log -1 --format='%ae' origin/main)"
