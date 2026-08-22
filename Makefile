PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
MYPY ?= $(PYTHON) -m mypy
PIP_COMPILE ?= $(PYTHON) -m piptools compile
COVERAGE_FAIL_UNDER ?= 70

.PHONY: install test lint typecheck coverage lock-check audit

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTEST) -q --tb=short
	@echo "Canonical suite: pytest reported above (fail the job if any test failed)."

lint:
	$(RUFF) format --check ssg tests
	$(RUFF) check ssg tests
	$(MAKE) lock-check

typecheck:
	$(PYTHON) -m pip install -q mypy types-PyYAML
	$(MYPY) ssg/logging_config.py ssg/validation.py ssg/error_tracking.py ssg/runtime_metrics.py ssg/config.py
	$(PYTHON) -m compileall -q ssg

coverage:
	mkdir -p coverage
	$(PYTEST) -q --cov=ssg --cov-report=term --cov-report=html:coverage --cov-report=xml:coverage/coverage.xml --cov-fail-under=$(COVERAGE_FAIL_UNDER) | tee coverage/summary.txt
	@$(PYTHON) -c "import xml.etree.ElementTree as E; r=E.parse('coverage/coverage.xml').getroot(); print('LINE_COVERAGE_PCT', round(float(r.attrib['line-rate'])*100, 2))"

lock-check:
	$(PYTHON) ci/lock_check.py

audit:
	$(PYTHON) -m pip_audit -r requirements.txt
	npm audit --prefix . --audit-level=high
