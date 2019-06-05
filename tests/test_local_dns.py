# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals
from tests import conftest

import dnsq
import tasks

testinfra_hosts = (
    'ssh://default?ssh_config=ssh-config',
)


# before running any of these tests, fire up the test environment if it  is not running
if conftest.is_box_running(box='default') is False:
    tasks.prep(conftest.CONTEXT, pty=True, box='default', skip_if_built=False)

# create the ssh-config
conftest.refresh_vagrant_ssh_config(box='default')

resolver = dnsq.create_resolver(search='foo-domain.com', nameservers=['67.77.255.142'])


def test_bind9_is_installed(host):
    bind9 = host.package('bind9')

    assert bind9.is_installed
    assert bind9.version == '1:9.10.3.dfsg.P4-12.3+deb9u5'


def test_bind9_config_files_contain_no_syntax_errors(host):
    with host.sudo():
        named_checkconf = host.run('/usr/sbin/named-checkconf')
        named_cz_db = host.run('/usr/sbin/named-checkzone 1.168.192.in-addr.arpa /etc/bind/db.192.168.1')
        named_cz_fwd = host.run('named-checkzone foo-domain.com /etc/bind/db.foo-domain.com')

    assert named_checkconf.rc == 0
    assert named_cz_db.rc == 0, '{}'.format(named_cz_db.stdout.strip() or named_cz_db.stderr.strip())
    assert named_cz_fwd.rc == 0, '{}'.format(named_cz_fwd.stdout.strip() or named_cz_fwd.stderr.strip())


def test_bind9_service_is_running(host):
    bind9 = host.service('bind9')

    assert bind9.is_enabled
    assert bind9.is_running


def test_rndc_is_working(host):
    with host.sudo():
        rndc = host.run('rndc status')

    assert rndc.rc == 0
    assert 'server is up and running' in rndc.stdout


def test_ntp_is_installed(host):
    ntp = host.package('ntp')

    assert ntp.is_installed


def test_ntp_config_exists(host):
    ntp_conf = host.file('/etc/ntp.conf')

    assert ntp_conf.exists
    assert ntp_conf.is_file


def test_ntp_service_is_running(host):
    ntp_service = host.service('ntp')

    assert ntp_service.is_enabled
    assert ntp_service.is_running


def test_nameserver_hostname_to_ip_lookup(host):
    orig_lifetime = resolver.lifetime
    try:
        resolver.lifetime = 3.0
        assert resolver.query('dc-app-01.foo-domain.com', 'A')[0].address == '192.168.1.20'
    finally:
        # reset the lifetime param back to the original
        resolver.lifetime = orig_lifetime


def test_nameserver_ip_to_hostname_lookup(host):
    nslookup = host.run('host -4 -W1 192.168.1.20 127.0.0.1')

    assert nslookup.rc == 0
    assert 'dc-app-01' in nslookup.stdout
