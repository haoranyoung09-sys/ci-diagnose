PYTHON ?= python3

.PHONY: diagnose self-check test eval smoke

diagnose:
	$(PYTHON) scripts/diagnose.py --fixtures-dir fixtures/gha

self-check:
	$(PYTHON) scripts/diagnose.py --self-check

test:
	$(PYTHON) -m unittest discover -s tests

eval:
	$(PYTHON) scripts/eval_fixtures.py

smoke: self-check test diagnose eval
