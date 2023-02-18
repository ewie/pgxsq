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
            for cname in cs.changes:
                with open(f'deploy/{cname}.sql') as change:
                    ext.write(change.read())


class Project(t.NamedTuple):
    """Sqitch project."""

    name: str
    plan: list['Change']

    @property
    def changesets(self):
        changes = []

        for change in self.plan:
            changes.append(change)

            if change.tags:
                yield Changeset(
                    change.tags[0],
                    [c.name for c in changes],
                )
                changes = []

        # Final changeset for an untagged HEAD.  Refer to that version
        # as HEAD as well.  That name is safe as Sqitch does not allow
        # it as tag name.
        if changes:
            yield Changeset('HEAD', [c.name for c in changes])


class Change(t.NamedTuple):
    """Change from a Sqitch plan."""

    name: str
    tags: list[str]


class Changeset(t.NamedTuple):
    """Set of changes for a single extension script."""

    version: str
    changes: list[str]
