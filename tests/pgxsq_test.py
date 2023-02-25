import textwrap


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


def test_output_directory(cli, postgres, sqitch, workdir):
    sqitch.init('test')
    sqitch.add('foo', "CREATE VIEW foo AS SELECT 1;")

    cli.build(dest='ext')

    extfiles = workdir.find_extension_files('test', 'ext')

    assert sorted(extfiles) == [
        'test--HEAD.sql',
        'test.control',
    ]

    with (
        postgres.load_extension(extfiles, 'ext'),
        postgres.connect() as con,
        postgres.extension(con, 'test', 'HEAD'),
        con.execute("SELECT * FROM foo") as cur,
    ):
        assert cur.fetchall() == [(1,)]


def test_transaction(cli, postgres, sqitch, workdir):
    sqitch.init('test')
    sqitch.add('foo', textwrap.dedent("""
        BEGIN;
        CREATE FUNCTION foo()
            RETURNS int
            LANGUAGE sql
            AS 'SELECT 1';
        COMMENT ON FUNCTION foo() IS 'Foo';
        COMMIT;
        """))

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
        con.execute("""
            SELECT
                foo(),
                (
                    SELECT description
                    FROM pg_description
                    WHERE objoid = 'foo()'::regprocedure
                    AND classoid = 'pg_proc'::regclass
                )
            """) as cur,
    ):
        assert cur.fetchall() == [(1, 'Foo')]


def test_extschema(cli, postgres, sqitch, workdir):
    sqitch.init('test')
    sqitch.add('foo', textwrap.dedent("""
        CREATE FUNCTION foo()
            RETURNS text
            LANGUAGE sql
            AS $$ SELECT 'extschema' $$;

        CREATE FUNCTION bar()
            RETURNS text
            LANGUAGE sql
            AS $$ SELECT extschema.foo() $$;
        """))

    cli.build(extschema='extschema')

    extfiles = workdir.find_extension_files('test')

    assert sorted(extfiles) == [
        'test--HEAD.sql',
        'test.control',
    ]

    # Test extension via CREATE EXTENSION.

    with (
        postgres.load_extension(extfiles),
        postgres.connect() as con,
        postgres.extension(con, 'test', 'HEAD'),
        con.execute("SELECT foo(), bar()") as cur,
    ):
        assert cur.fetchall() == [('public', 'public')]

    # Test that sqitch-deploy can be used with the extschema placeholder.

    try:
        # Prepare the database so that extschema is an actual schema on the
        # search_path.
        with postgres.connect() as con:
            con.execute("""
                CREATE SCHEMA extschema;

                DO $$
                BEGIN
                    EXECUTE format(
                        'ALTER DATABASE %I SET search_path = extschema',
                        current_database(), 'extschema'
                    );
                END $$;
                """)

        sqitch.deploy(postgres.uri())

        with (
            postgres.connect() as con,
            con.execute("SELECT foo(), bar()") as cur,
        ):
            assert cur.fetchall() == [('extschema', 'extschema')]
    finally:
        # Reset the database.
        with postgres.connect() as con:
            con.execute("""
                DO $$
                BEGIN
                    EXECUTE format(
                        'ALTER DATABASE %I RESET search_path',
                        current_database()
                    );
                END $$;

                DROP SCHEMA extschema CASCADE;
                DROP SCHEMA sqitch CASCADE;
                """)
