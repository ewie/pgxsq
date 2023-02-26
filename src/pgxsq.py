import collections
import functools
import os
import os.path
import re
import subprocess
import typing as t


def main(args=None):
    import argparse
    import importlib.metadata
    import sys

    def die(msg):
        print(f"error: {msg}", file=sys.stderr)
        raise SystemExit(1)

    version = importlib.metadata.version(__name__)

    parser = argparse.ArgumentParser(
        description="""
            Generate Postgres extension in directory DEST from the Sqitch
            project in current working directory.  Directory DEST is created
            automatically.
            """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--dest',
        default='.',
        help="generate extension files in this directory",
    )
    parser.add_argument(
        '--extschema',
        help="replace this substring with @extschema@",
    )
    parser.add_argument('--version', action='version', version=version)

    opts = parser.parse_args(args)

    try:
        project = read_project()
    except EmptyPlan:
        die("empty plan")
    except ProjectNotFound:
        die("no project")

    write_extension(project, opts.dest, opts.extschema)


def read_project():
    proc = subprocess.run(
        args=[
            'sqitch', '--quiet',
            'plan', '--no-header', '--format', 'format:%o %n %{ }t',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    # We cannot get the project name from the sqitch-plan output in case of an
    # empty plan.  sqitch-plan also includes the project name in its optional
    # headers but those are always omitted on empty plans.  The only other
    # possibilty is to parse the project pragam from the plan file.  But the
    # plan file path must be resolved from the project config first.  It's not
    # worth the effort just to generate an empty extension.
    if proc.returncode == 1:
        raise EmptyPlan

    if proc.returncode == 2:
        raise ProjectNotFound

    project = None

    for line in proc.stdout.splitlines():
        pname, cname, *tags = re.split(r'\s+', line.strip())

        if project:
            assert pname == project.name
        else:
            project = Project(pname, plan=[])

        project.plan.append(Change(cname, tags))

    assert project

    return project


def write_extension(project, dest, extschema):
    extname = project.name
    guard = rf'\echo Use "CREATE EXTENSION {extname}" to load this file. \quit'

    filename = functools.partial(os.path.join, dest)

    os.makedirs(dest, exist_ok=True)

    # Create empty control file.
    with open(filename(f'{extname}.control'), 'w'):
        pass

    for cs in project.changesets:
        with open(filename(cs.filename(extname)), 'w') as ext:
            ext.write(guard)
            ext.write('\n')
            for cname, tag in cs.changes:
                with project.open_deploy_script(cname, tag) as fp:
                    for ln in strip_transactions(fp):
                        if extschema:
                            ln = ln.replace(extschema, '@extschema@')
                        ext.write(ln)


def strip_transactions(lines):
    """Strip transaction control commands from lines of a Sqitch change script.

    Sqitch recommends explicit transactions for atomic changes.  Extension
    scripts, however, do not permit transaction control commands because
    extensions are installed in an implicit transaction.  Therefore, scripts
    must be stripped of transaction control commands.

    The filter removes lines that only contain the commands BEGIN or COMMIT
    followed by a semicolon.  A single trailing line feed is the only allowed
    whitespace.  The filter is case-insensitive.

    The filter is that strict to minimize edge cases where it would detect
    false positives in certain contexts, e.g. multiline string literals.

    Consider the following definition of function `foo` that returns a string
    that is formatted such that BEGIN and COMMIT appear on separate lines as if
    they are transaction control commands.

        BEGIN;

        CREATE FUNCTION foo()
            RETURNS text
            LANGUAGE plpgsql
            AS $$
        BEGIN
            RETURN '
        BEGIN;
        COMMIT;
        ';
        END $$;

        COMMIT;
    """
    return filter(
        lambda ln: ln.upper() not in ('BEGIN;\n', 'COMMIT;\n'),
        lines,
    )


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
        tags = collections.deque([''], maxlen=2)

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
                            (cname, rework.get(cname, ''))
                            for cname in reversed(changes)
                        ],
                    )

                    # Track tags of (possibly) reworked changes.
                    for cname, _ in cs.changes:
                        rework[cname] = cs.fromtag

                    changesets.append(cs)
                    changes = []

            changes.append(change.name)

        # Remaining changes before the first tag or untagged HEAD in
        # case there are no tags at all.
        if changes:
            tags.appendleft('')
            cs = Changeset(
                *tags,
                [
                    (cname, rework.get(cname, ''))
                    for cname in reversed(changes)
                ],
            )
            changesets.append(cs)

        return reversed(changesets)

    def open_deploy_script(self, change, tag):
        if tag and not tag.startswith('@'):
            raise ValueError(f"tag {tag!r} must start with '@'")

        return open(f'deploy/{change}{tag}.sql')


class Change(t.NamedTuple):
    """Change from a Sqitch plan."""

    name: str
    tags: list[str]


class Changeset(t.NamedTuple):
    """Set of changes for a single extension script.

    Changesets update an extension from one version to another.  The update
    path is defined by attributes `fromtag` and `tag`.  An empty `fromtag`
    marks an installation script.  An empty `tag` marks a changeset containing
    the untagged HEAD of a Sqitch plan.

    Attribute `changes` lists tagged and untagged changes.  The tag name is
    needed to identify the correct deploy script of each change in case of
    reworks.  Changes that are not reworked are untagged (empty string).
    """

    fromtag: str
    tag: str
    changes: list[tuple[str, str]]

    def filename(self, extname):
        fromver = self.fromtag.removeprefix('@')
        version = self.tag.removeprefix('@') or 'HEAD'

        if fromver:
            return f'{extname}--{fromver}--{version}.sql'
        else:
            return f'{extname}--{version}.sql'


class EmptyPlan(Exception):
    """Raised when reading an empty Sqitch plan."""


class ProjectNotFound(Exception):
    """Raised when no Sqitch project is found."""
