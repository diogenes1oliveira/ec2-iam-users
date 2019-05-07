import json
import sys


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
    16: 'MISSING_REQUIREMENTS',
}


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
