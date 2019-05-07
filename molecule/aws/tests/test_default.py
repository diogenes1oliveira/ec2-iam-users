from contextlib import ExitStack
import os

import testinfra.utils.ansible_runner

from common import ssh_shell

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_user_of_group(host, iam, temp_keypair):
    ip = host.ansible.get_variables()['ansible_host']

    with ExitStack() as stack, temp_keypair() as (key1, pub1), temp_keypair() as (key2, pub2):
        this_iam = iam(stack.callback)
        iam_user = 'linux_user_1_molecule_test'
        linux_user = 'linux_user_1'
        group = 'molecule_test_devs'
        this_iam.add_user(iam_user)
        key1_id = this_iam.add_ssh_key(iam_user, pub1)

        # shouldn't succeed, user is not in group
        cmd = ssh_shell(user=linux_user, key=key1, host=ip)
        assert cmd.returncode != 0

        # adding the user to the group and trying again
        this_iam.add_group(group, iam_user)
        print(f'-i {key1} {linux_user}@{ip}')
        cmd = ssh_shell('whoami', user=linux_user, key=key1, host=ip, check=True)
        assert linux_user in cmd.stdout

        # shouldn't succeed after disabling the SSH key
        this_iam.toggle_ssh_key(iam_user, key1_id, False)
        cmd = ssh_shell(user=linux_user, key=key1, host=ip)
        assert cmd.returncode != 0
