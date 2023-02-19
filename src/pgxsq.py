import collections
import re
import subprocess
import typing as t


def main(args=None):
    import argparse
    import importlib.metadata

    version = importlib.metadata.version(__name__)

    parser = argparse.ArgumentParser(
        description="""
            Generate Postgres extension from Sqitch project in current working
            directory.
            """,
    )
    parser.add_argument('--version', action='version', version=version)

    parser.parse_args(args)

    write_extension(read_project())


def read_project():
    proc = subprocess.run(
        args=[
            'sqitch', '--quiet',
            'plan', '--no-header', '--format', 'format:%o %n %{ }t',
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    project = None

    for line in proc.stdout.splitlines():
        pname, cname, *tags = re.split(r'\s+', line)
        tags = [t.removeprefix('@') for t in tags if t]

        if project:
            assert pname == project.name
        else:
            project = Project(pname, plan=[])

        project.plan.append(Change(cname, tags))

    return project


def write_extension(project):
    extname = project.name
    guard = rf'\echo Use "CREATE EXTENSION {extname}" to load this file. \quit'

    # Create empty control file.
    with open(f'{extname}.control', 'w'):
        pass

    for cs in project.changesets:
        with open(f'{extname}--{cs.version}.sql', 'w') as ext:
            ext.write(guard)
            ext.write('\n')
            for cname, _ in cs.changes:
                with open(f'deploy/{cname}.sql') as change:
                    ext.write(change.read())


class Project(t.NamedTuple):
    """Sqitch project."""

    name: str
    plan: list['Change']

    @property
    def changesets(self):
        # The final changesets.
        changesets = []

        # Changes for a single changeset.
        changes = []

        # The two most recent tags that determine a changeset version.
        # Changesets apply to the version given by the left tag and
        # target the version given by the right tag.
        tags = collections.deque(['HEAD'], maxlen=2)

        # Map (potentially) reworked changes to the tag when the change
        # was reworked.
        rework = {}

        # Collect changes in reverse to trace back reworked changes.
        for change in reversed(self.plan):
            if change.tags:
                tags.appendleft(change.tags[0])

                if changes:
                    cs = Changeset(
                        *tags,
                        [
                            (cname, rework.get(cname))
                            for cname in reversed(changes)
                        ],
                    )

                    # Track tags of (possibly) reworked changes.
                    for cname, _ in cs.changes:
                        rework[cname] = cs.fromver

                    changesets.append(cs)
                    changes = []

            changes.append(change.name)

        # Remaining changes before the first tag or untagged HEAD in
        # case there are no tags at all.
        if changes:
            tags.appendleft(None)
            cs = Changeset(
                *tags,
                [
                    (cname, rework.get(cname))
                    for cname in reversed(changes)
                ],
            )
            changesets.append(cs)

        return reversed(changesets)


class Change(t.NamedTuple):
    """Change from a Sqitch plan."""

    name: str
    tags: list[str]


class Changeset(t.NamedTuple):
    """Set of changes for a single extension script.

    The changeset updates an extension from one version to another specified
    by attributes `fromver` and `version`.  Attribute `fromver` is `None` in
    case of an install script.  Update scripts that contain the untagged HEAD
    of a Sqitch plan have attribute `version` set to `HEAD`.

    Attribute `changes` lists optionally tagged changes.  The optional tag
    name is needed to identity the correct deploy script of each change in
    case of reworks.  Changes that are not reworked have tag `None`.
    """

    fromver: str | None
    version: str
    changes: list[tuple[str, str | None]]
