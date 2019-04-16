from contextlib import ExitStack
import json
import os
from shlex import quote
import sys
from uuid import uuid4

from pytest import fixture
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


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
def aws(shell):
    def aws_caller(*args):
        cmd = shell('aws', '--endpoint-url',
                    ENV['ENDPOINT_URL'], *args, ** ENV)
        return cmd
    return aws_caller


ENV = {
    'ENDPOINT_URL': 'http://ec2-iam-users-localstack:4593',
    'AWS_ACCESS_KEY_ID': 'no_key',
    'AWS_SECRET_ACCESS_KEY': 'no_key',
    'AWS_DEFAULT_REGION': 'sa-east-1',
}

CODES = {
    1: 'BAD_VALUE',
    2: 'API_ERROR',
    4: 'NOT_FOUND',
    8: 'NO_KEYS',
}


def test_invalid_parameters(shell):
    cmd = shell('fetch-public-keys-from-iam', 'invalid user name', ** ENV)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'

    cmd = shell('fetch-public-keys-from-iam', '-g',
                'invalid group name', 'my-user', ** ENV)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'

    cmd = shell('fetch-public-keys-from-iam', '-m', 'lol', 'my-user', ** ENV)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'


class Group:
    def __init__(self, aws, defer):
        self.aws = aws
        self.defer = defer
        self.name = None
        self.users = []

    def create(self, name):
        self.name = name
        cmd = self.aws('iam', 'get-group', '--group-name', name)
        if cmd.rc != 0:
            assert self.aws('iam', 'create-group',
                            '--group-name', name).rc == 0
            # self.defer.push(lambda *args: self.aws('iam', 'delete-group',
            #                                        '--group-name', name))
            # delete_group is not yet implemented as of today

    def add_user(self, user):
        self.users.append(user)

        cmd = self.aws('iam', 'get-user', '--user-name', user)
        if cmd.rc != 0:
            assert self.aws('iam', 'create-user',
                            '--user-name', user).rc == 0
            self.defer.push(lambda *args: self.aws('iam', 'delete-user',
                                                   '--user-name', user))

        cmd = self.aws('iam', 'get-group', '--group-name',
                       self.name, '--query', f'Users[?Username==`{user}`]')
        if not json.loads(cmd.stdout):
            assert self.aws(
                'iam', 'add-user-to-group', '--group-name', self.name,
                '--user-name', user
            ).rc == 0
            self.defer.push(lambda *args: self.aws(
                'iam', 'remove-user-from-group', '--group-name', self.name,
                '--user-name', user)
            )


def test_not_found(aws, shell):
    group_name = 'group-' + str(uuid4())[:10]
    user1 = 'user-' + str(uuid4())[:10]

    with ExitStack() as stack:
        cmd = shell('fetch-public-keys-from-iam',
                    '-g', group_name, user1, ** ENV)
        assert CODES[cmd.rc] == 'NOT_FOUND'

        group = Group(aws, stack)
        group.create(group_name)
        group.add_user(user1)

        cmd = shell('fetch-public-keys-from-iam',
                    '-g', group_name, user1, ** ENV)
        assert CODES[cmd.rc] == 'NO_KEYS'
