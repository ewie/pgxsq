SHELL := bash
python := python3.10
venv := .venv

.PHONY: all
all: deps check test

.PHONY: build
build: venv
	source $(venv)/bin/activate \
	  && $(python) -m build

.PHONY:
check: venv
	source $(venv)/bin/activate \
	  && flake8

.PHONY: clean
clean: clean-buildfiles clean-pycache clean-testfiles

.PHONY: clean-buildfiles
clean-buildfiles:
	rm -fr dist
	rm -fr src/pgxsq.egg-info

.PHONY: clean-pycache
clean-pycache:
	find -name __pycache__ -exec rm -fr {} +

.PHONY: clean-testfiles
clean-testfiles:
	rm -fr .pytest_cache

.PHONY: deps
deps: venv
	source $(venv)/bin/activate \
	  && pip install --upgrade pip \
	  && pip install --editable .[dev]

.PHONY: install
install:
	pip install .

.PHONY: test
test: venv
	source $(venv)/bin/activate \
	  && pytest

.PHONY: venv
venv: $(venv)/.gitignore

$(venv)/.gitignore:
	test -d $(venv) || $(python) -m venv $(venv)
	echo '*' > $@
