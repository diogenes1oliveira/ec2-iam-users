from contextlib import contextmanager
import json
from pathlib import Path
from shlex import quote
import sys
import tempfile
from uuid import uuid4

from pytest import fixture
from testinfra.host import Host

from common import local_shell


@fixture(scope='module')
def shell(host):
    def cmd_caller(*args, **kwargs):
        envs = ' '.join('%s=%s' % (k, quote(v)) for k, v in kwargs.items())
        argpart = ' '.join(map(quote, args))
        cmdline = envs + ' ' + argpart
        cmd = host.run(cmdline)
        print(f'---- {cmdline} ----')
        print('---- stdout ----')
        print(cmd.stdout)
        print('---- stderr ----')
        print(cmd.stderr, file=sys.stderr)
        print('----------------')
        return cmd

    return cmd_caller


@fixture(scope='module')
def ansibler(host):
    def call_ansible_module(module_name, check=False, become=True, **kwargs):
        return host.ansible(module_name, kwargs, check=check, become=True)

    return call_ansible_module


def local_ansible(*args, **kwargs):
    cmd = Host.get_host('ansible://localhost').ansible(*args, kwargs, check=False)
    return cmd


class IAM:
    def __init__(self, cleanup_callback=None):
        self.cleanup_callback = cleanup_callback
        self.suffix = str(uuid4())

    def add_group(self, name, *users):
        cmd = local_ansible('iam_group', name=name, users=users, state='present')
        assert not cmd.get('failed')
        self.cleanup_callback and self.cleanup_callback(
            lambda: local_ansible('iam_group', name=name, state='absent')
        )
        return cmd

    def add_user(self, name):
        cmd = local_ansible('iam_user', name=name, state='present')
        assert not cmd.get('failed')
        self.cleanup_callback and self.cleanup_callback(
            lambda: local_ansible('iam_user', name=name, state='absent')
        )
        return cmd

    def add_ssh_key(self, user_name, key_body):
        cmd = local_shell(
            'aws', 'iam', 'upload-ssh-public-key',
            '--user-name', user_name,
            '--ssh-public-key-body', key_body,
        )
        assert cmd.returncode == 0
        key_id = json.loads(cmd.stdout)['SSHPublicKey']['SSHPublicKeyId']
        self.cleanup_callback and self.cleanup_callback(
            lambda: local_shell(
                'aws', 'iam', 'delete-ssh-public-key',
                '--user-name', user_name,
                '--ssh-public-key-id', key_id,
            )
        )
        return key_id

    def toggle_ssh_key(self, user_name, key_id, active):
        cmd = local_shell(
            'aws', 'iam', 'update-ssh-public-key',
            '--user-name', user_name,
            '--ssh-public-key-id', key_id,
            '--status', 'Active' if active else 'Inactive',
        )


@fixture(scope='module')
def iam():
    return IAM


@fixture(scope='module')
def temp_keypair():
    @contextmanager
    def inner():
        with tempfile.TemporaryDirectory() as tempdir:
            key = Path(tempdir) / f'key-{uuid4()}'
            pub = key.with_suffix('.pub')
            args = ['ssh-keygen', '-b', '2048', '-t', 'rsa', '-f', str(key), '-q', '-N', ""]
            local_shell(*args, input=str(key), check=True)
            with open(pub) as fp:
                pub_key = fp.read()

            yield key, pub_key

    return inner
