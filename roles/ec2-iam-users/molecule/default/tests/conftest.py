from pytest import fixture
from shlex import quote
import sys

from common import ENV


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


@fixture(scope='module')
def ansibler(host):
    def call_ansible_module(module_name, check=False, become=True, **kwargs):
        return host.ansible(module_name, kwargs, check=check, become=True)

    return call_ansible_module
