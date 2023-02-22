def test_tagged_head(cli, postgres, sqitch, workdir):
    sqitch.init('test')
    sqitch.add('foo', "CREATE VIEW foo AS SELECT 1;")
    sqitch.tag('0.1')

    cli.build()

    extfiles = workdir.find_extension_files('test')

    assert sorted(extfiles) == [
        'test--0.1.sql',
        'test.control',
    ]

    with (
        postgres.load_extension(extfiles),
        postgres.connect() as con,
        postgres.extension(con, 'test', '0.1'),
        con.execute("SELECT * FROM foo") as cur,
    ):
        assert cur.fetchall() == [(1,)]


def test_untagged_head(cli, postgres, sqitch, workdir):
    sqitch.init('test')
    sqitch.add('foo', "CREATE VIEW foo AS SELECT 1;")

    cli.build()

    extfiles = workdir.find_extension_files('test')

    assert sorted(extfiles) == [
        'test--HEAD.sql',
        'test.control',
    ]

    with (
        postgres.load_extension(extfiles),
        postgres.connect() as con,
        postgres.extension(con, 'test', 'HEAD'),
        con.execute("SELECT * FROM foo") as cur,
    ):
        assert cur.fetchall() == [(1,)]


def test_rework_in_next_changeset(cli, postgres, sqitch, workdir):
    sqitch.init('test')

    sqitch.add('foo', "CREATE VIEW foo AS SELECT 1;")
    sqitch.tag('0.1')

    sqitch.rework('foo', "CREATE OR REPLACE VIEW foo AS SELECT 2;")

    cli.build()

    extfiles = workdir.find_extension_files('test')

    assert sorted(extfiles) == [
        'test--0.1--HEAD.sql',
        'test--0.1.sql',
        'test.control',
    ]

    with (
        postgres.load_extension(extfiles),
        postgres.connect() as con,
        postgres.extension(con, 'test', '0.1'),
    ):
        with con.execute("SELECT * FROM foo") as cur:
            assert cur.fetchall() == [(1,)]

        con.execute("ALTER EXTENSION test UPDATE TO 'HEAD'")

        with con.execute("SELECT * FROM foo") as cur:
            assert cur.fetchall() == [(2,)]


def test_rework_in_later_changeset(cli, postgres, sqitch, workdir):
    sqitch.init('test')

    sqitch.add('foo', "CREATE VIEW foo AS SELECT 1;")
    sqitch.tag('0.1')

    # Intermediate changeset before reworking foo.
    sqitch.add('bar', "CREATE VIEW bar AS SELECT 2;")
    sqitch.tag('0.2')

    # Rework foo in final changeset.
    sqitch.rework('foo', "CREATE OR REPLACE VIEW foo AS SELECT 3;")

    cli.build()

    extfiles = workdir.find_extension_files('test')

    assert sorted(extfiles) == [
        'test--0.1--0.2.sql',
        'test--0.1.sql',
        'test--0.2--HEAD.sql',
        'test.control',
    ]

    with (
        postgres.load_extension(extfiles),
        postgres.connect() as con,
        postgres.extension(con, 'test', '0.1'),
    ):
        with con.execute("SELECT * FROM foo") as cur:
            assert cur.fetchall() == [(1,)]

        con.execute("ALTER EXTENSION test UPDATE TO '0.2'")

        with con.execute("SELECT * FROM foo, bar") as cur:
            assert cur.fetchall() == [(1, 2)]

        con.execute("ALTER EXTENSION test UPDATE TO 'HEAD'")

        with con.execute("SELECT * FROM foo, bar") as cur:
            assert cur.fetchall() == [(3, 2)]


def test_empty_plan(capsys, cli, sqitch, workdir):
    sqitch.init('test')

    rc = cli.build()
    _, err = capsys.readouterr()
    extfiles = workdir.find_extension_files('test')

    assert rc == 1
    assert err == "error: empty plan\n"
    assert sorted(extfiles) == []


def test_missing_project(capsys, cli, workdir):
    rc = cli.build()
    _, err = capsys.readouterr()
    extfiles = workdir.find_extension_files('test')

    assert rc == 1
    assert err == "error: no project\n"
    assert sorted(extfiles) == []
