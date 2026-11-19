# One command runs everything:  make all
#
#   make core      the 12-task audit, the hack gallery & the hand-check comparison (about 2 minutes, no download)
#   make evalplus  the realism check on HumanEval+ (downloads about 110 MB once, then 10 to 20 minutes)
#   make report    plots & key numbers
#   make test      the test suite
PYTHON ?= python

.PHONY: all core audit hacks review evalplus report test hooks

all: core evalplus report test

core: audit hacks review

audit:
	$(PYTHON) audit.py

hacks:
	$(PYTHON) hacks_eval.py
	$(PYTHON) demos/verifier_attacks/demo.py

review:
	$(PYTHON) review/compare.py

evalplus:
	$(PYTHON) evalplus_check.py

report:
	$(PYTHON) report.py

test:
	$(PYTHON) -m pytest -q

hooks:
	sh scripts/install_hooks.sh
