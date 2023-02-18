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
