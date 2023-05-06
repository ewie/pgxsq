system_python := python3
venv := .venv
venv_python := $(venv)/bin/python3

.PHONY: all
all: deps check test

.PHONY: build
build: venv
	$(venv_python) -m build

.PHONY:
check: venv
	$(venv_python) -m flake8

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
	$(venv_python) -m pip install --upgrade pip
	$(venv_python) -m pip install --editable .[dev]

.PHONY: install
install:
	pip install .

.PHONY: test
test: venv
	$(venv_python) -m pytest

.PHONY: venv
venv: $(venv)/.gitignore

$(venv)/.gitignore:
	test -d $(venv) || $(system_python) -m venv $(venv)
	echo '*' > $@
