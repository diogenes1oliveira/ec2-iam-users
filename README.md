# ec2-iam-users

[![Build Status](https://travis-ci.org/diogenes1oliveira/ec2-iam-users.svg?branch=master)](https://travis-ci.org/diogenes1oliveira/ec2-iam-users)

Ansible role to provide IAM based SSH access to EC2 instances, altogether with
autosyncing via Lambda.

This role was originally inspired by this Medium post
[SSH Authentication with AuthorizedKeysCommand](https://medium.com/@jryancanty/just-in-time-ssh-provisioning-7b20d9736a07).

## Instance Requirements

- The EC2 instances must be using YUM-derived Linux AMIs.
- A minimum set of policies that must be attached to the instances is given in
  [iam-ec2-policy.yml](files/iam-ec2-policy.yml)

## Controller Requirements

- To install the dependencies on the controller node, run
  `pip install -r requirements.txt`

## Dependencies

No extra role or external module is required.

## Role Variables

```yaml
# defaults/main.yml

iam_group: devs
# Name of the group to fetch the users from

linux_group: devs
# Name of the Linux group that the users will belong to

max_ssh_keys: 5
# Max number of SSH public keys to fetch from IAM

region: sa-east-1
# Default AWS region

protected_users: # those users will never be touched
  - ec2-user
  - ubuntu

users: [] # list of users to assure existence
```

```yaml
# vars/main.yml

ansible_become: true
# Become root to run the commands

host_key_path: /etc/ssh/ssh_host_rsa_key
# Where to store the keys that identify the host

protected_users_group: protected-users
# group the protected users will belong to
```

## Example Playbook

Apply the role passing the values you wish to override:

```yaml
- hosts: bastion
  roles:
    - role: ec2-iam-users
      iam_group: developers
```

## License

MIT

## Author Information

Diógenes Oliveira - March 2019
