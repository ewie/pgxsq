from pgxsq import Change, Changeset, Project


def test_untagged_head():
    project = Project('test', plan=[
        Change('a', []),
        Change('b', []),
    ])

    assert list(project.changesets) == [
        Changeset(None, 'HEAD', [('a', None), ('b', None)]),
    ]


def test_tagged_head():
    project = Project('test', plan=[
        Change('a', []),
        Change('b', ['0.1']),
    ])

    assert list(project.changesets) == [
        Changeset(None, '0.1', [('a', None), ('b', None)]),
    ]


def test_reworked_change():
    project = Project('test', plan=[
        Change('a', ['0.1']),
        Change('b', []),
        Change('a', []),
    ])

    assert list(project.changesets) == [
        Changeset(None,  '0.1',  [('a', '0.1')]),
        Changeset('0.1', 'HEAD', [('b', None), ('a', None)]),
    ]


def test_reworked_change_with_tags_in_between():
    project = Project('test', plan=[
        Change('a', ['0.1']),
        Change('b', ['0.2']),
        Change('c', ['0.3']),
        Change('a', []),
    ])

    assert list(project.changesets) == [
        Changeset(None,  '0.1',  [('a', '0.3')]),
        Changeset('0.1', '0.2',  [('b', None)]),
        Changeset('0.2', '0.3',  [('c', None)]),
        Changeset('0.3', 'HEAD', [('a', None)]),
    ]


def test_reworked_change_with_more_tags_in_between():
    project = Project('test', plan=[
        Change('a', ['0.1']),
        Change('b', ['0.2']),
        Change('c', ['0.3']),
        Change('a', []),
        Change('b', ['0.4']),
        Change('c', []),
        Change('a', ['0.5']),
    ])

    assert list(project.changesets) == [
        Changeset(None,  '0.1', [('a', '0.3')]),
        Changeset('0.1', '0.2', [('b', '0.3')]),
        Changeset('0.2', '0.3', [('c', '0.4')]),
        Changeset('0.3', '0.4', [('a', '0.4'), ('b', None)]),
        Changeset('0.4', '0.5', [('c', None),  ('a', None)]),
    ]
