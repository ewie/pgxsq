SHELL := bash
python := python3.10
venv := .venv

.PHONY: all
all: deps check test

.PHONY:
check: venv
	source $(venv)/bin/activate \
	  && flake8

.PHONY: clean
clean:
	rm -fr $(venv)
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

venv: $(venv)/.gitignore

$(venv)/.gitignore:
	test -d $(venv) || $(python) -m venv $(venv)
	echo '*' > $@
