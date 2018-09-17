# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals
from dnsq import cli
from tests import conftest

import dnsq
import logging
import mock
import pytest
import subprocess
import tasks

EXPECTED_VERSION = '2018.9.13'
DEFAULT_NAMESERVER = '67.77.255.142'
DEFAULT_DOMAIN = 'foo-domain.com'
DEFAULT_TIMEOUT = 8.0


# before running any of these tests, fire up the test environment if it  is not running
if conftest.is_box_running(box='default') is False:
    tasks.prep(conftest.CONTEXT, pty=True, box='default', skip_if_built=False)

# create the ssh-config
conftest.refresh_vagrant_ssh_config(box='default')


def assert_cli(cmd, expected=None, rc=0, stdout=True, stderr=True, *args, **kwargs):
    """A helper to capture stdout and stderr when testing command line options that raise SystemExit

    Args:
        cmd `str` - The command as a string to run
        expected `str` - The expected output from stdout or stderr. If `None` this test is skipped.
        rc `int` - The expected exit code. Default `0`
        stdout `bool` - When `True` captures and returns stdout. Default `True`
        stderr `bool` - When `True` captures and returns stderr. Default `True`
        args `tuple` - positional args to pass to subprocess.Popen
        kwargs `dict` - key value pairs to pass to subprocess.Popen

    """
    kwargs['shell'] = True

    if stdout:
        kwargs['stdout'] = subprocess.PIPE
    if stderr:
        kwargs['stderr'] = subprocess.PIPE

    proc = subprocess.Popen(cmd, *args, **kwargs)
    out, err = proc.communicate()
    out = out.decode('utf-8').strip()
    err = err.decode('utf-8').strip()

    assert proc.returncode == rc, out or err

    if expected:
        actual = out or err
        assert actual == expected

    return out, err


def test_create_parser():
    parser = cli.create_parser()

    assert parser.description == 'A python DNS tool for doing fun things with DNS'
    assert parser.prog == 'dnsq'


def test_version_argument():
    assert_cli('dnsq --version', stdout=True, stderr=True, rc=0, expected=EXPECTED_VERSION)


def test_ns_type_nameserver_domain_long_arguments():
    assert_cli('dnsq --type ns --nameserver {nameserver} --domain {domain} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected='ns1.foo-domain.com. ns2.foo-domain.com.',
               rc=0,
               stdout=True,
               stderr=True
               )

    resolver = dnsq.create_resolver(DEFAULT_DOMAIN, DEFAULT_NAMESERVER)
    assert dnsq.ns_records(resolver=resolver, domain=DEFAULT_DOMAIN)


def test_query_with_default_sort_by():
    expected = '\n'.join([
        'aa-foo-01 A 192.168.1.22',
        'dc-app-01 A 192.168.1.20',
        'dc-app-02 A 192.168.1.21',
        'ns1 A 192.168.1.10',
        'ns2 A 192.168.1.11',
        'zz-bar-01 A 192.168.1.23',
    ])
    assert_cli('dnsq --query "192\.168\.1" --domain {domain} --nameserver {nameserver} --timeout {timeout}'.format(domain=DEFAULT_DOMAIN, nameserver=DEFAULT_NAMESERVER, timeout=DEFAULT_TIMEOUT),
               rc=0,
               expected=expected,
               stdout=True,
               stderr=True
               )


def test_query_with_default_sort_by_should_exit_0():
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(['--query', r'192\.168\.1', '--domain', 'foo-domain.com', '--nameserver', '67.77.255.142', '--timeout', str(DEFAULT_TIMEOUT), '-vv'])

    assert str(exp.value) == '0'


def test_query_with_ip_sort_by():
    expected = '\n'.join([
        '192.168.1.10 A ns1',
        '192.168.1.11 A ns2',
        '192.168.1.20 A dc-app-01',
        '192.168.1.21 A dc-app-02',
        '192.168.1.22 A aa-foo-01',
        '192.168.1.23 A zz-bar-01',
    ])
    assert_cli('dnsq --query "192\.168\.1" --domain {domain} --nameserver {nameserver} --timeout {timeout} --sort-by ip'.format(domain=DEFAULT_DOMAIN, nameserver=DEFAULT_NAMESERVER, timeout=DEFAULT_TIMEOUT),
               rc=0,
               expected=expected,
               stdout=True,
               stderr=True
               )


def test_query_with_ip_sort_by_should_exit_0():
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(['--query', r'192\.168\.1', '--domain', 'foo-domain.com', '--nameserver', '67.77.255.142', '--timeout', str(DEFAULT_TIMEOUT), '--sort-by', 'ip'])

    assert str(exp.value) == '0'


def test_soa_type_nameserver_domain_short_arguemnts():
    assert_cli('dnsq -t soa -n {nameserver} -d {domain}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected='ns1.foo-domain.com. root.foo-domain.com. 2018070500 28800 3600 604800 86400',
               rc=0,
               stdout=True,
               stderr=True
               )


def test_soa_type_nameserver_domain_long_arguemnts():
    assert_cli('dnsq --type soa --nameserver {nameserver} --domain {domain} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected='ns1.foo-domain.com. root.foo-domain.com. 2018070500 28800 3600 604800 86400',
               rc=0,
               stdout=True,
               stderr=True
               )


def test_supports_zone_transfer_with_short_options_will_exit_cleanly():
    assert_cli('dnsq --supports-axfr -d {domain} -n {nameserver} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected='',
               rc=0,
               stdout=True,
               stderr=True
               )


def test_supports_zone_transfer_with_long_options_will_exit_cleanly():
    assert_cli('dnsq --supports-axfr --domain {domain} --nameserver {nameserver} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected='',
               rc=0,
               stdout=True,
               stderr=True
               )


def test_axfr_with_short_arguments():
    expected = (
        '@ 7200 IN SOA ns1 root 2018070500 28800 3600 604800 86400\n'
        '@ 7200 IN NS ns1\n'
        '@ 7200 IN NS ns2\n'
        'aa-foo-01 7200 IN A 192.168.1.22\n'
        'app-01 7200 IN CNAME dc-app-01\n'
        'dc-app-01 7200 IN A 192.168.1.20\n'
        'dc-app-02 7200 IN A 192.168.1.21\n'
        'dns1 7200 IN CNAME ns1\n'
        'dns2 7200 IN CNAME ns2\n'
        'ns1 7200 IN A 192.168.1.10\n'
        'ns2 7200 IN A 192.168.1.11\n'
        'zz-bar-01 7200 IN A 192.168.1.23'
    )

    assert_cli('dnsq -t axfr -d {domain} -n {nameserver} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected=expected,
               rc=0,
               stdout=True,
               stderr=True
               )


def test_axfr_with_long_arguments():
    expected = (
        '@ 7200 IN SOA ns1 root 2018070500 28800 3600 604800 86400\n'
        '@ 7200 IN NS ns1\n'
        '@ 7200 IN NS ns2\n'
        'aa-foo-01 7200 IN A 192.168.1.22\n'
        'app-01 7200 IN CNAME dc-app-01\n'
        'dc-app-01 7200 IN A 192.168.1.20\n'
        'dc-app-02 7200 IN A 192.168.1.21\n'
        'dns1 7200 IN CNAME ns1\n'
        'dns2 7200 IN CNAME ns2\n'
        'ns1 7200 IN A 192.168.1.10\n'
        'ns2 7200 IN A 192.168.1.11\n'
        'zz-bar-01 7200 IN A 192.168.1.23'
    )

    assert_cli('dnsq --type axfr --domain {domain} --nameserver {nameserver} --timeout {timeout}'.format(nameserver=DEFAULT_NAMESERVER, domain=DEFAULT_DOMAIN, timeout=DEFAULT_TIMEOUT),
               expected=expected,
               rc=0,
               stdout=True,
               stderr=True
               )


@mock.patch('dnsq.create_resolver', side_effect=Exception('called create_resolver'))
def test_when_options_domain_and_namerserver_are_present_should_create_resolver(create_resolver_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called create_resolver' in str(exp.value)
    create_resolver_mock.assert_called_once_with()


@mock.patch('dnsq.LOGGER.setLevel', side_effect=Exception('called dns.LOGGER.setLevel'))
def test_when_single_verbose_option_is_present(setlevel_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['-v', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dns.LOGGER.setLevel' in str(exp.value)
    setlevel_mock.assert_called_once_with(logging.INFO)


@mock.patch('dnsq.LOGGER.setLevel', side_effect=Exception('called dns.LOGGER.setLevel'))
def test_when_double_verbose_option_is_present(setlevel_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['-v', '-v', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dns.LOGGER.setLevel' in str(exp.value)
    setlevel_mock.assert_called_once_with(logging.DEBUG)


@mock.patch('dnsq.supports_zone_transfer', side_effect=Exception('called dnsq.supports_zone_transfer'))
def test_when_supports_axfr_option_is_present(supports_zone_transfer_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['--supports-axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dnsq.supports_zone_transfer' in str(exp.value)
    supports_zone_transfer_mock.assert_called_once_with(domain='example.com', nameserver='1.0.0.1', lifetime=20.0)


@mock.patch('dnsq.supports_zone_transfer', return_value=True)
def test_when_supports_axfr_option_is_present_and_the_result_is_True_it_should_exit_0(supports_zone_transfer_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--supports-axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    # make sure we exit 1 since we force supports_zone_transfer to return False
    assert str(exp.value) == '0'
    supports_zone_transfer_mock.assert_called_once_with(domain='example.com', nameserver='1.0.0.1', lifetime=20.0)


@mock.patch('dnsq.supports_zone_transfer', return_value=False)
def test_when_supports_axfr_option_is_present_and_the_result_is_False_it_should_exit_1(supports_zone_transfer_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--supports-axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    # make sure we exit 1 since we force supports_zone_transfer to return False
    assert str(exp.value) == '1'
    supports_zone_transfer_mock.assert_called_once_with(domain='example.com', nameserver='1.0.0.1', lifetime=20.0)


@mock.patch('dnsq.ns_records', side_effect=Exception('called dnsq.ns_records'))
def test_when_type_ns_records_option_is_present(ns_records_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['--type', 'ns', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dnsq.ns_records' in str(exp.value)


@mock.patch('dnsq.ns_records')
def test_when_type_ns_records_option_is_present_it_should_exit_0(ns_records_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--type', 'ns', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert str(exp.value) == '0'


@mock.patch('dnsq.soa_records', side_effect=Exception('called dnsq.soa_records'))
def test_when_type_soa_records_option_is_present(soa_records_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['--type', 'soa', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dnsq.soa_records' in str(exp.value)


@mock.patch('dnsq.soa_records')
def test_when_type_soa_records_option_is_present_it_should_exit_0(soa_records_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--type', 'soa', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert str(exp.value) == '0'


@mock.patch('dnsq.zone_transfer', side_effect=Exception('called dnsq.zone_transfer'))
@mock.patch('dnsq.supports_zone_transfer')
def test_when_type_axfr_is_present(supports_zone_transfer_mock, zone_transfer_mock):
    with pytest.raises(Exception) as exp:
        dnsq.cli.execute(argv=['--type', 'axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert 'called dnsq.zone_transfer' in str(exp.value)


@mock.patch('dnsq.supports_zone_transfer', return_value=False)
def test_when_type_axfr_is_present_and_supports_zone_tranfer_returns_False_it_should_exit_1(supports_zone_transfer_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--type', 'axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert str(exp.value) == '1'


@mock.patch('dnsq.zone_transfer', return_value=['foo1', 'foo2'])
@mock.patch('dnsq.supports_zone_transfer', return_value=True)
def test_when_type_axfr_is_present_and_supports_zone_tranfer_returns_True_it_should_exit_0(supports_zone_transfer_mock, zone_transfer_mock):
    with pytest.raises(SystemExit) as exp:
        dnsq.cli.execute(argv=['--type', 'axfr', '--domain', 'example.com', '--nameserver', '1.0.0.1'])

    assert str(exp.value) == '0'
