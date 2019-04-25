import os
from shlex import quote
import subprocess
import sys


def local_shell(*args, **kwargs):
    check = kwargs.pop('check', False)
    input = kwargs.pop('input', None)
    cmdline = ' '.join(map(quote, args or ['whoami']))

    env = os.environ.copy()
    env.update(kwargs)

    kwargs = {
        'check': check,
        'shell': True,
        'env': env,
        'capture_output': True,
        'input': input,
        'text': True,
        'encoding': 'utf-8',
        'cwd': os.getcwd(),
    }
    if not input:
        kwargs['stdin'] = subprocess.DEVNULL

    cmd = subprocess.run(cmdline, **kwargs)
    print(f'\n\n---- {cmdline} ----> ({cmd.returncode})')
    print('---- stdout ----')
    print(cmd.stdout)
    print('---- stderr ----')
    print(cmd.stderr, file=sys.stderr)
    print('----------------')
    return cmd


def ssh_shell(*args, **kwargs):
    check = kwargs.pop('check', False)
    user = kwargs.pop('user', 'ec2-user')
    key = kwargs.pop('key', None)
    host = kwargs.pop('host', None)
    port = kwargs.pop('port', 22)
    assert key
    assert host

    ssh_args = [
        'ssh',
        '-i', str(key),
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-i', str(key),
        '-p', str(port),
        f'{user}@{host}',
    ]
    envs = ['%s=%s' % (k, quote(v)) for k, v in kwargs.items()]
    args = list(args) or ['whoami']

    return local_shell(*(ssh_args + envs + args), check=check)
