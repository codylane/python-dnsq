#!/usr/bin/env python
# coding: utf-8


from __future__ import absolute_import
from __future__ import unicode_literals

from io import open
from setuptools import find_packages
from setuptools import setup

import codecs
import os
import re

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
RELEASE_FILENAME = os.path.join(PROJECT_DIR, 'dnsq/release.py')


class Release(object):
    """Avoid the import just read the file

    """
    __version__ = None
    __author__ = None
    __author_email__ = None
    __url__ = None

    def __init__(self):
        with open(RELEASE_FILENAME, encoding='utf-8', mode='r') as fd:
            self.content = fd.read()

            for line in self.content.splitlines():
                if line.startswith('__') is False:
                    continue
                key, val = re.split(r'\s*=\s*', line)
                val = val.replace('"', '').replace("'", '')
                setattr(self, key, val)


release = Release()

assert release.__version__ is not None, 'Please set __version__ in {}'.format(RELEASE_FILENAME)
assert release.__author__ is not None, 'Please set __author__ in {}'.format(RELEASE_FILENAME)
assert release.__author_email__ is not None, 'Please set __author_email__ in {}'.format(RELEASE_FILENAME)
assert release.__url__ is not None, 'Please set __url__ in {}'.format(RELEASE_FILENAME)


def read(fname):
    file_path = os.path.join(PROJECT_DIR, fname)
    return codecs.open(file_path, encoding='utf-8').read()


def read_requirements(fname):
    fname = os.path.join(PROJECT_DIR, fname)
    with open(fname, mode='r', encoding='utf-8') as fd:
        result = fd.read().splitlines()
        return result


EXCLUDE_FROM_PACKAGES = []

REQUIRED_LIBRARIES = read_requirements('requirements.txt')

setup(
    name='dnsq',
    version=release.__version__,
    author=release.__author__,
    author_email=release.__author_email__,
    maintainer=release.__author__,
    maintainer_email=release.__author_email__,
    license='Apache Software License 2.0',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    url=release.__url__,
    description='A python utility for querying information in DNS',
    long_description=read('README.md'),
    install_requires=REQUIRED_LIBRARIES,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: System Administrators',
        'Intended Audience :: DevOps',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: DNS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7.14',
        'Programming Language :: Python :: 2.7.15',
        'Programming Language :: Python :: 3.6.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
    ],
    zip_safe=False,
    include_package_data=True,
    scripts=[
        'bin/dnsq',
    ],
)
