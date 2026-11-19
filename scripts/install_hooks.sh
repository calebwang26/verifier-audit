#!/bin/sh
# Point this repo's git hooks at the versioned hooks/ folder.
set -e
git config core.hooksPath hooks
echo "git hooks installed (core.hooksPath=hooks)"
