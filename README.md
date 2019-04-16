# ec2-iam-users

[![Build Status](https://travis-ci.org/diogenes1oliveira/ec2-iam-users.svg?branch=master)](https://travis-ci.org/diogenes1oliveira/ec2-iam-users)

Ansible role to provide IAM based SSH access to EC2 instances, altogether with
autosyncing via Lambda

## Requirements

The EC2 instances must be using YUM-derived Linux AMIs. A minimum set of
policies that must be attached to the instances is given in
[iam-ec2-policy.yml](files/iam-ec2-policy.yml)

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
```

## Dependencies

A list of other roles hosted on Galaxy should go here, plus any details in
regards to parameters that may need to be set for other roles, or variables that
are used from other roles.

## Example Playbook

Including an example of how to use your role (for instance, with variables
passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: ec2-iam-users, x: 42 }

## License

MIT

## Author Information

Diógenes Oliveira - March 2019
