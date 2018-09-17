# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
from functools import wraps
from io import open

import invoke
import os
import subprocess
import tasks


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(TEST_DIR, os.pardir))
CONTEXT = invoke.context.Context()


def is_box_running(box='default'):
    for vagrant_box in tasks.get_vagrant_suts():
        if vagrant_box['sut'] == box and vagrant_box['status'] == 'running':
            return True
    return False


def refresh_vagrant_ssh_config(box='default'):
    filename = os.path.join(PROJECT_DIR, 'ssh-config')
    ssh_config_cmd = [
        'vagrant',
        'ssh-config',
        box,
    ]

    with open(filename, mode='w', encoding='utf-8') as stdout:
        rc = subprocess.call(ssh_config_cmd, stdout=stdout)

    return rc


def vagrant_ssh_config(box='default'):
    """A parametrized decorator for refreshing the ssh-config for a vagrant box

    """
    def wrapper(func):
        @wraps(func)
        def on_call(*args, **kwargs):
            rc = refresh_vagrant_ssh_config(box=box, *args, **kwargs)
            assert rc == 0, 'Unable to refresh ssh config for box={}'.format(box)
        return on_call
    return wrapper
