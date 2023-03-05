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
clean:
	rm -fr dist
	find -name '*.pyc' -delete

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
