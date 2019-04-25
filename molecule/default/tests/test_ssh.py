from base64 import b64decode
from collections import namedtuple
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile

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

    ssh_args = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-i', str(key),
        '-p', str(port),
        f'{user}@{host}',
    ]
    args = args or ['whoami']
    process = subprocess.run(ssh_args + args,
                             encoding='utf-8', capture_output=True)
    print(process)
    if 'Permission denied' in process.stderr:
        raise paramiko.ssh_exception.AuthenticationException
    return SSHResult(process.returncode, process.stdout, process.stderr)


@contextmanager
def temp_ssh_keys():
    with tempfile.TemporaryDirectory() as tempdir:
        key1 = Path(tempdir) / 'key1'
        pub1 = key1.with_suffix('.pub')
        subprocess.run(['ssh-keygen', '-N', '', '-f', key1], check=True)

        key2 = Path(tempdir) / 'key2'
        pub2 = key2.with_suffix('.pub')
        subprocess.run(['ssh-keygen', '-N', '', '-f', key2], check=True)

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

    user = 'linux_user_1'
    with temp_ssh_keys() as keys:
        key1, pub1, key2, pub2 = keys
        fetcher = f'echo "{pub1}"'

        with temp_content(ansibler, '/usr/bin/fetch-public-keys-from-iam', fetcher):
            print(f'user = {user} key1 = {key1}')
            ssh_run(user=user, key=key1)
            with pytest.raises(paramiko.ssh_exception.AuthenticationException):
                ssh_run(user=user, key=key2)
