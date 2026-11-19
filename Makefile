PYTHON ?= python

.PHONY: all core audit hacks test hooks

# Everything that needs no download.
core: audit hacks

all: core test

audit:
	$(PYTHON) audit.py

hacks:
	$(PYTHON) hacks_eval.py
	$(PYTHON) demos/verifier_attacks/demo.py

test:
	$(PYTHON) -m pytest -q

hooks:
	sh scripts/install_hooks.sh
