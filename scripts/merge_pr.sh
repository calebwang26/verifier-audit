#!/bin/sh
# Merge a pull request only if every CI check passed.
# usage: scripts/merge_pr.sh <pr-number>
#
# After merging it checks the email on the merge commit. A merge done on
# GitHub's side is stamped with the account's primary email unless "Keep my
# email addresses private" is on (GitHub -> Settings -> Emails). That setting
# was off for this project's first eight merges, which put a personal email
# into history & forced a rewrite (BUILDLOG.md, steps 9 & 10). If it ever
# gets switched off again, this script says so at once instead of at the end.
set -eu
pr="$1"

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
echo "all checks passed; merging PR $pr"
gh pr merge "$pr" --merge --delete-branch

git fetch -q origin
email=$(git log -1 --format='%ae' origin/main)
case "$email" in
  *@users.noreply.github.com) echo "merged PR $pr; merge commit email is the no-reply address" ;;
  *) echo "PROBLEM: the merge commit on main carries '$email', not the no-reply address."
     echo "Turn on 'Keep my email addresses private' in GitHub settings & fix this commit before publishing."
     exit 2 ;;
esac
