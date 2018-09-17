# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals


from dnsq import release


def test_release_version():
    assert release.__version__ == '2018.9.13'


def test_release_author():
    assert release.__author__ == 'Cody Lane'


def test__author_email__():
    assert release.__author_email__ == 'cody.lane@gmail.com'


def test__url__():
    assert release.__url__ == 'https://github.com/codylane/python-dnsq'
