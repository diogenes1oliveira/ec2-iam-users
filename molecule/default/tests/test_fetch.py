from contextlib import ExitStack
import os
from uuid import uuid4

import testinfra.utils.ansible_runner

from common import (CODES, ENV, Group)

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_invalid_parameters(shell):
    cmd = shell('fetch-public-keys-from-iam', 'invalid user name', ** ENV)
    print(cmd)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'

    cmd = shell('fetch-public-keys-from-iam', '-g',
                'invalid group name', 'my-user', ** ENV)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'

    cmd = shell('fetch-public-keys-from-iam', '-m', 'lol', 'my-user', ** ENV)
    assert 'Unable to locate credentials' not in cmd.stdout
    assert CODES[cmd.rc] == 'BAD_VALUE'


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
