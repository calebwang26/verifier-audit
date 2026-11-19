PYTHON ?= python

.PHONY: all test hooks

all: test

test:
	$(PYTHON) -m pytest -q

hooks:
	sh scripts/install_hooks.sh
