import io
import textwrap

import pytest

from pgxsq import strip_transactions


def test_strip_transactions():
    sql = "--before\nBEGIN;\n--inside\nCOMMIT;\n--after\n"
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == "--before\n--inside\n--after\n"


@pytest.mark.parametrize('mapcase', [str.capitalize, str.lower, str.upper])
def test_case_insensitive(mapcase):
    sql = f"{mapcase('BEGIN')};\n{mapcase('COMMIT')};\n"
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == ""


def test_keep_indented_statements():
    sql = " BEGIN;\n COMMIT;\n"
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == sql


def test_multiple_transactions():
    sql = "BEGIN;\nCOMMIT;\nBEGIN;\nCOMMIT;\n"
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == ""


def test_without_transaction():
    sql = "--\n"
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == sql


def test_keep_plpgsql_begin():
    sql = textwrap.dedent("""
        DO $$
        BEGIN
        END $$;
        """)
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == sql


@pytest.mark.xfail(reason="edge case", strict=True)
def test_edge_case_multline_string_literal():
    sql = textwrap.dedent("""
        SELECT '
        BEGIN;
        COMMIT;
        ';
        """)
    fp = io.StringIO(sql)

    assert ''.join(strip_transactions(fp)) == sql
