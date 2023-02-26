import pytest

from pgxsq import Change, Changeset, InvalidName, Project


def test_untagged_head():
    project = Project('test', plan=[
        Change('a', []),
        Change('b', []),
    ])

    assert list(project.changesets) == [
        Changeset('', '', [('a', ''), ('b', '')]),
    ]


def test_tagged_head():
    project = Project('test', plan=[
        Change('a', []),
        Change('b', ['@0.1']),
    ])

    assert list(project.changesets) == [
        Changeset('', '@0.1', [('a', ''), ('b', '')]),
    ]


def test_reworked_change():
    project = Project('test', plan=[
        Change('a', ['@0.1']),
        Change('b', []),
        Change('a', []),
    ])

    assert list(project.changesets) == [
        Changeset('',     '@0.1', [('a', '@0.1')]),
        Changeset('@0.1', '',     [('b', ''), ('a', '')]),
    ]


def test_reworked_change_with_tags_in_between():
    project = Project('test', plan=[
        Change('a', ['@0.1']),
        Change('b', ['@0.2']),
        Change('c', ['@0.3']),
        Change('a', []),
    ])

    assert list(project.changesets) == [
        Changeset('',     '@0.1', [('a', '@0.3')]),
        Changeset('@0.1', '@0.2', [('b', '')]),
        Changeset('@0.2', '@0.3', [('c', '')]),
        Changeset('@0.3', '',     [('a', '')]),
    ]


def test_reworked_change_with_more_tags_in_between():
    project = Project('test', plan=[
        Change('a', ['@0.1']),
        Change('b', ['@0.2']),
        Change('c', ['@0.3']),
        Change('a', []),
        Change('b', ['@0.4']),
        Change('c', []),
        Change('a', ['@0.5']),
    ])

    assert list(project.changesets) == [
        Changeset('',     '@0.1', [('a', '@0.3')]),
        Changeset('@0.1', '@0.2', [('b', '@0.3')]),
        Changeset('@0.2', '@0.3', [('c', '@0.4')]),
        Changeset('@0.3', '@0.4', [('a', '@0.4'), ('b', '')]),
        Changeset('@0.4', '@0.5', [('c', ''),     ('a', '')]),
    ]


def test_empty_plan():
    project = Project('test', plan=[])

    assert list(project.changesets) == []


@pytest.mark.parametrize(
    'extname', ['', '-test', 'test-', 'te--st', 'te/st', r'te\st'],
)
def test_filename_invalid_extname(extname):
    project = Project('test', plan=[Change('a', [])])
    cs = next(project.changesets)

    with pytest.raises(InvalidName):
        cs.filename(extname)


@pytest.mark.parametrize(
    'version', [
        '0--rc',
        # The following names are not valid Sqitch tags.
        '-0', '0-', '0/rc', r'0\rc',
    ],
)
def test_filename_invalid_version(version):
    project = Project('test', plan=[
        Change('a', [version]),
        Change('b', []),
    ])
    cs = project.changesets

    # Test invalid target version with first changeset.
    with pytest.raises(InvalidName):
        next(cs).filename(project.name)

    # Test invalid base version with second changeset.
    with pytest.raises(InvalidName):
        next(cs).filename(project.name)
