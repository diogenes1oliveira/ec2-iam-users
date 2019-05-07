# ec2-iam-users

[![Build Status](https://travis-ci.org/diogenes1oliveira/ec2-iam-users.svg?branch=master)](https://travis-ci.org/diogenes1oliveira/ec2-iam-users)

Ansible role to provide IAM based SSH access to EC2 instances

This role was originally inspired by this Medium post
[SSH Authentication with AuthorizedKeysCommand](https://medium.com/@jryancanty/just-in-time-ssh-provisioning-7b20d9736a07).

## Instance Requirements

- The EC2 instances must be using YUM-derived Linux AMIs.
- A minimum set of policies that must be attached to the instances is given in
  [iam-ec2-policy.yml](files/iam-ec2-policy.yml)

## Controller Requirements

- To install the dependencies on the controller node, use [pipenv](https://github.com/pypa/pipenv)
  with `pipenv install`

## Dependencies

No extra role or external module is required.

## Role Variables

```yaml
# defaults/main.yml

iam_group: devs
# Name of the group to fetch the users from

max_ssh_keys: 5
# Max number of SSH public keys to fetch from IAM

region: sa-east-1
# Default AWS region

ssh_username: dev
# User the IAM user will be able to login as

ssh_user_groups:
  - sudo
  - docker
# Additional groups the user will belong to

default_username: ec2-user
# Extra user to always be allowed SSH
```

```yaml
# vars/main.yml

ansible_become: true
# Become root to run the commands

host_key_path: /etc/ssh/ssh_host_rsa_key
# Where to store the keys that identify the host
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
