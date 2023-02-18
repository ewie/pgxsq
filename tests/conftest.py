import contextlib
import glob
import io
import os
import subprocess
import tarfile

import docker
import psycopg
import pytest

import pgxsq


@pytest.fixture
def cli():
    return Pgxsq()


@pytest.fixture(scope='session')
def postgres():
    pg = Postgres()
    pg.start()

    try:
        yield pg
    finally:
        pg.stop()


@pytest.fixture
def sqitch():
    return Sqitch()


@pytest.fixture
def workdir(tmp_path):
    """Change working directory to a temporary directory during test.
    """
    oldcwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        yield Workdir(tmp_path)
    finally:
        os.chdir(oldcwd)


class Pgxsq:
    """Client to the pgxsq command line.
    """

    def build(self):
        pgxsq.main([])


class Postgres:
    """Postgres container running during tests.
    """

    _PASSWORD = 'test'
    _USER = 'test'
    _PORT = '5432/tcp'

    def start(self):
        self._container = docker.from_env().containers.run(
            detach=True,
            environment={
                'POSTGRES_PASSWORD': self._PASSWORD,
                'POSTGRES_USER': self._USER,
            },
            image='postgres',
            ports={self._PORT: ('127.0.0.1', 0)},  # Pick random host port.
            remove=True,
        )

        self._container.reload()  # Reload to get ports.

        addr = self._container.ports[self._PORT][0]
        self._host = addr['HostIp']
        self._port = int(addr['HostPort'])

        self._sharedir = self._get_sharedir()

    def stop(self):
        self._container.stop(timeout=0)

    @contextlib.contextmanager
    def load_extension(self, filenames):
        """Return a context manager that loads extension files into this
        container and removes them upon completion of the block.
        """
        dest = f'{self._sharedir}/extension'
        tarball = io.BytesIO()

        with tarfile.open(fileobj=tarball, mode='w') as f:
            for fname in filenames:
                f.add(fname)

                # Check for existing files in the container and don't
                # just overwrite files with put_archive.
                rc, _ = self._container.exec_run(
                    cmd=['test', '-f', fname],
                    workdir=dest,
                )

                if rc == 0:
                    raise ValueError(f"extension file exists: {fname!r}")

                assert rc == 1

        ok = self._container.put_archive(dest, tarball.getvalue())

        if not ok:
            raise RuntimeError("put_archive failed")

        try:
            yield
        finally:
            rc, _ = self._container.exec_run(
                cmd=['rm', '--force'] + filenames,
                workdir=dest,
            )

            if rc != 0:
                raise RuntimeError(
                    "failed to remove extension files: {filename!r}"
                )

    @contextlib.contextmanager
    def extension(self, connection, name, version):
        """Return a context manager that creates an extension and drops it upon
        completion of the block.
        """
        connection.execute(
            psycopg.sql.SQL("CREATE EXTENSION {} VERSION {}")
            .format(psycopg.sql.Identifier(name), version)
        )

        try:
            yield
        finally:
            connection.execute(
                psycopg.sql.SQL("DROP EXTENSION IF EXISTS {}")
                .format(psycopg.sql.Identifier(name))
            )

    def connect(self):
        """Connect to the default database."""
        return psycopg.connect(
            host=self._host,
            port=self._port,
            user=self._USER,
            password=self._PASSWORD,
        )

    def _get_sharedir(self):
        rc, out = self._container.exec_run(['pg_config', '--sharedir'])
        if rc != 0:
            raise RuntimeError(f"pg_config exited with {rc}: {out!r}")
        return out.decode('ascii').strip()


class Sqitch:
    """Interface for the Sqitch command line.
    """

    def init(self, name):
        self._run(['init', name, '--engine', 'pg'])

    def add(self, name, deploy_script):
        self._run(['add', name, '--note', f'Add {name}'])

        with open(f'deploy/{name}.sql', 'w') as f:
            f.write(deploy_script)

    def tag(self, name):
        self._run(['tag', name, '--note', f'Tag {name}'])

    def _run(self, args):
        subprocess.run(
            args=['sqitch'] + args,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class Workdir:
    """Working directory for a single test.
    """

    def __init__(self, base):
        self._base = base

    def find_extension_files(self, extname):
        extname = glob.escape(extname)
        return [
            fname
            for pat in (f'{extname}.control', f'{extname}--*.sql')
            for fname in glob.iglob(pat, root_dir=self._base)
        ]
