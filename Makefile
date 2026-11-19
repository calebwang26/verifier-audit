PYTHON ?= python

.PHONY: all core audit test hooks

# Everything that needs no download.
core: audit

all: core test

audit:
	$(PYTHON) audit.py

test:
	$(PYTHON) -m pytest -q

hooks:
	sh scripts/install_hooks.sh
