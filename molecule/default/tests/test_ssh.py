from base64 import b64decode
from collections import namedtuple
from contextlib import contextmanager, ExitStack
import os
from pathlib import Path
from shlex import quote
import subprocess
import tempfile
from uuid import uuid4

import paramiko
import pytest
import testinfra.utils.ansible_runner


testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


SSHResult = namedtuple('Command', ['rc', 'stdout', 'stderr'])


def ssh_run(*args, user, key, host='localhost', port=32768):
    if not user:
        raise ValueError('user is required')
    if not key:
        raise ValueError('keyfile is required')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        username=user,
        key_filename=str(key),
        port=port,
    )
    try:
        cmd = ' '.join(quote(arg) for arg in (args or ['whoami']))
        stdin, stdout, stderr = client.exec_command(cmd)
        rc = stdin.channel.recv_exit_status()
        return SSHResult(rc, stdout.read(), stderr.read())
    finally:
        client.close()


@contextmanager
def temp_ssh_keys():
    with tempfile.TemporaryDirectory() as tempdir:
        key1 = Path(tempdir) / 'key1'
        pub1 = key1.with_suffix('.pub')
        subprocess.run(['ssh-keygen', '-N', '', '-f', key1])

        key2 = Path(tempdir) / 'key2'
        pub2 = key2.with_suffix('.pub')
        subprocess.run(['ssh-keygen', '-N', '', '-f', key2])

        with open(str(pub2)) as f2, open(str(pub1)) as f1:
            yield (key1, f1.read(), key2, f2.read())


@contextmanager
def temp_content(ansibler, path, content):
    result = ansibler('slurp', path=path)
    ansibler('copy', content=content, dest=path, mode='0755')
    try:
        yield
    finally:
        ansibler('copy', content=b64decode(
            result['content']), dest=path, mode='0755')


def test_happy_path(host, shell, ansibler):
    vars = host.ansible.get_variables()
    if 'ssh' not in vars['group_names']:
        pytest.skip('host is not in ssh group')
        return

    user = 'u' + str(uuid4())[:8]
    with ExitStack() as stack:
        cmd = ansibler('user', name=user, state='present')
        assert not cmd.get('failed')
        stack.callback(ansibler, 'user', name=user, state='absent')

        cmd = ansibler('user', name=user, state='present',
                       groups=['ssh_iam'])
        assert not cmd.get('failed')

        with temp_ssh_keys() as keys:
            key1, pub1, key2, pub2 = keys
            fetcher = f'echo "{pub1}"'

            with temp_content(ansibler, '/usr/bin/fetch-public-keys-from-iam', fetcher):
                ssh_run(user=user, key=key1)
                with pytest.raises(paramiko.ssh_exception.AuthenticationException):
                    ssh_run(user=user, key=key2)
