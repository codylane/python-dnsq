###############################################################################
#
# integration tests
#
###############################################################################
# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals
from tests import conftest

import dns.name
import dnsq
import tasks


SEARCH_DOMAIN = 'foo-domain.com'
NAMESERVERS = ['67.77.255.142']
LIFETIME = 5.0
SOA_SERIAL = '2018070500'
SOA_REFRESH = '28800'
SOA_RETRY = '3600'
SOA_EXPIRE = '604800'
SOA_TTL = '86400'
resolver = dnsq.create_resolver(search=SEARCH_DOMAIN, nameservers=NAMESERVERS, lifetime=LIFETIME)


# before running any of these tests, fire up the test environment if it  is not running
if conftest.is_box_running(box='default') is False:
    tasks.prep(conftest.CONTEXT, pty=True, box='default', skip_if_built=False)


def test_resolver():
    assert resolver.search == [dns.name.from_text(SEARCH_DOMAIN)]
    assert resolver.nameservers == NAMESERVERS


def test_ns_records():
    actual_ns_records = dnsq.ns_records(resolver, domain=SEARCH_DOMAIN)
    expected_ns_records = [
        'ns1.' + SEARCH_DOMAIN + '.',
        'ns2.' + SEARCH_DOMAIN + '.',
    ]
    assert actual_ns_records == expected_ns_records


def test_soa_records():
    actual_soa_records = dnsq.soa_records(resolver, domain=SEARCH_DOMAIN)
    expected_soa_records = [
        [
            'ns1.' + SEARCH_DOMAIN + '.',
            'root.' + SEARCH_DOMAIN + '.',
            SOA_SERIAL,
            SOA_REFRESH,
            SOA_RETRY,
            SOA_EXPIRE,
            SOA_TTL,
        ]
    ]
    assert actual_soa_records == expected_soa_records


def test_supports_zone_transfer_returns_True():
    actual = dnsq.supports_zone_transfer(domain=SEARCH_DOMAIN, nameserver=NAMESERVERS[0], lifetime=LIFETIME)
    assert actual is True


def test_supports_zone_transfer_returns_False():
    actual = dnsq.supports_zone_transfer(domain='a-non-existant-domain-for-unit-test.com', nameserver=NAMESERVERS[0], lifetime=LIFETIME)
    assert actual is False

    actual = dnsq.supports_zone_transfer(domain='zonetransfer.me', nameserver=NAMESERVERS[0], lifetime=LIFETIME)
    assert actual is False
