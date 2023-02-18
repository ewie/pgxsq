# pgxsq

Write [Postgres extensions] as [Sqitch] projects.


## Usage

    pip install pgxsq
    pgxsq --help


## Development setup

Setup virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip

Install:

    pip install --editable .[dev]

Lint and test:

    flake8
    pytest


[Postgres extensions]: https://www.postgresql.org/docs/current/extend-extensions.html
[Sqitch]: https://sqitch.org
