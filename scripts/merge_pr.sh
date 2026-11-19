#!/bin/sh
# Merge a pull request only if every CI check passed.
# usage: scripts/merge_pr.sh <pr-number>
set -u
pr="$1"

# Checks take a few seconds to register after a push; wait for them to appear.
tries=0
until gh pr checks "$pr" >/dev/null 2>&1 || [ "$(gh pr checks "$pr" 2>&1 | grep -c .)" -gt 1 ]; do
  tries=$((tries + 1))
  if [ "$tries" -gt 30 ]; then echo "no checks appeared for PR $pr"; exit 1; fi
  sleep 5
done

if gh pr checks "$pr" --watch --interval 10 --fail-fast; then
  echo "all checks passed; merging PR $pr"
  gh pr merge "$pr" --merge --delete-branch
else
  echo "checks FAILED for PR $pr; not merging"
  gh pr checks "$pr"
  exit 1
fi
