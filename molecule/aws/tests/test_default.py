from contextlib import ExitStack
import os

import testinfra.utils.ansible_runner

from common import local_shell, ssh_shell

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_user_of_group(host, iam, temp_keypair):
    ip = host.ansible.get_variables()['ansible_host']

    with ExitStack() as stack, temp_keypair() as (key1, pub1), temp_keypair() as (key2, pub2):
        this_iam = iam(stack.callback)
        user1 = 'linux_user_1_molecule_test'
        group = 'iam_group_molecule_test'
        this_iam.add_user(user1)
        key1_id = this_iam.add_ssh_key(user1, pub1)

        # shouldn't succeed, user is not in group
        cmd = ssh_shell(user=user1, key=key1, host=ip)
        assert cmd.returncode != 0

        # adding the user to the group and trying again
        this_iam.add_group(group, user1)
        print(f'-i {key1} {user1}@{ip}')
        cmd = ssh_shell('whoami', user=user1, key=key1, host=ip, check=True)
        assert user1 in cmd.stdout

        # shouldn't succeed after disabling the SSH key
        this_iam.toggle_ssh_key(user1, key1_id, False)
        cmd = ssh_shell(user=user1, key=key1, host=ip)
        assert cmd.returncode != 0
