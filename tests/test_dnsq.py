# coding: utf-8

from __future__ import absolute_import
from __future__ import unicode_literals

import dns
import dnsq
import mock
import pytest

EXPECTED_SUPPORTED_TYPES = (
    dnsq.STRING_TYPE,
    list,
    tuple,
    dns.name.Name,
)


MOCKED_DNS_NS_MESSAGE = '''id 12345
opcode QUERY
rcode NOERROR
flags QR RD RA
;QUESTION
foo-domain. IN NS
;ANSWER
foo-domain. 21594 IN NS ns3.foo-domain.
foo-domain. 21594 IN NS ns1.foo-domain.
foo-domain. 21594 IN NS ns2.foo-domain.
;AUTHORITY
;ADDITIONAL
'''

MOCKED_DNS_SOA_MESSAGE = '''id 20123
opcode QUERY
rcode NOERROR
flags QR RD RA
;QUESTION
foo-domain. IN SOA
;ANSWER
foo-domain. 7199 IN SOA ns3.foo-domain. root.foo-domain. 2017103001 172800 900 1209600 3600
;AUTHORITY
;ADDITIONAL
'''

MOCKED_AXFR_MESSAGE = '''id 25634
opcode QUERY
rcode NOERROR
flags QR AA RA
;QUESTION
@ IN AXFR
;ANSWER
@ 7200 IN SOA ns1 root 2018070500 28800 3600 604800 38400
@ 7200 IN NS ns2
@ 7200 IN NS ns1
dc-app-02 7200 IN A 192.168.1.21
dc-app-01 7200 IN A 192.168.1.20
dc-dns-01 7200 IN A 192.168.1.10
dns-01 7200 IN CNAME dc-dns-01
@ 7200 IN SOA ns1 root 2018070500 28800 3600 604800 38400
;AUTHORITY
;ADDITIONAL
'''


def mock_Answer(rdtype, message, domain='foo-domain.', rdclass=dns.rdataclass.IN, raise_on_no_answer=False):
    """A wrapper to create a `dns.resolver.Answer` object  for unit tests

    """
    message = dns.message.from_text(message)
    domain = dns.name.from_text(domain)
    mocked_results = dns.resolver.Answer(domain, rdtype=rdtype, rdclass=rdclass, response=message, raise_on_no_answer=raise_on_no_answer)

    return mocked_results


def mock_NS_Answer(domain, message=MOCKED_DNS_NS_MESSAGE, raise_on_no_answer=False):
    """A wrapper to wrapp a `dns.resolver.Answer` object for NS unit tests

    """
    return mock_Answer(domain=domain, message=message, rdtype=dns.rdatatype.NS, rdclass=dns.rdataclass.IN, raise_on_no_answer=raise_on_no_answer)


def mock_SOA_Answer(domain, message=MOCKED_DNS_SOA_MESSAGE, raise_on_no_answer=False):
    """A wrapper to wrap a `dns.resolver.Answer` object for SOA unit tests

    """
    return mock_Answer(domain=domain, message=message, rdtype=dns.rdatatype.SOA, rdclass=dns.rdataclass.IN, raise_on_no_answer=raise_on_no_answer)


def mock_AXFR_Answer(message=MOCKED_AXFR_MESSAGE):
    """A wrapper to wrap a `dns.resolver.Answer` object for AXFR unit tests

    """
    mocked_result = [dns.message.from_text(message)]

    with mock.patch('dnsq.dns.query.xfr', autospec=True, return_value=mocked_result) as xfr_mock:
        yield xfr_mock


@pytest.mark.parametrize(
    'test_ips, expected',
    [
        pytest.param(
            ['192.168.1.200', '192.168.1.10', '192.168.4.50', '192.168.4.3', '192.168.200.220', '172.16.1.30', '10.0.0.2'],
            ['10.0.0.2', '172.16.1.30', '192.168.1.10', '192.168.1.200', '192.168.4.3', '192.168.4.50', '192.168.200.220'],
        ),
    ]
)
def test_sort_ips(test_ips, expected):
    sorted_ips = dnsq.sort_ips(test_ips)
    assert sorted_ips == expected


@pytest.mark.parametrize(
    'invalid_type',
    [
        pytest.param(dict()),
        pytest.param(42),
    ]
)
def test_get_resolver_domain_type_will_raise_AssertionError_when_passed_invalid_domain_type(invalid_type):
    expected_err_msg = 'Expected domain to be one of {the_supported_types}, got {this_invalid_type}'.format(the_supported_types=EXPECTED_SUPPORTED_TYPES,
                                                                                                            this_invalid_type=type(invalid_type).__name__,
                                                                                                            )

    with pytest.raises(AssertionError) as exp:
        dnsq.get_resolver_domain_type(domain=invalid_type)

    assert expected_err_msg in str(exp.value)


@pytest.mark.parametrize(
    'valid_type, expected',
    [
        pytest.param('example.com', 'example.com.'),
        pytest.param(u'example.com', 'example.com.'),
        pytest.param(r'example.com', 'example.com.'),
        pytest.param(['example', 'foo', 'com'], 'example.foo.com'),
        pytest.param(('example', 'foo2', 'com'), 'example.foo2.com'),
        pytest.param(dns.name.Name(['example', 'com']), 'example.com'),
    ]
)
def test_get_resolver_domain_type_will_return_Name_instance(valid_type, expected):
    actual_type = dnsq.get_resolver_domain_type(domain=valid_type)

    assert isinstance(actual_type, dns.name.Name)
    assert actual_type.to_text() == expected


def test_create_resolver_with_default_arguments():
    resolver = dnsq.create_resolver()

    assert isinstance(resolver, dns.resolver.Resolver)
    assert isinstance(resolver.nameservers, list)
    assert resolver.nameservers != []
    assert isinstance(resolver.domain, dns.name.Name)


def test_create_resolver_with_custom_search_should_invoke_get_resolver_domain_type():
    resolver = None
    domain = 'example.com'

    def mocked_result(*args, **kwargs):
        return dns.name.from_text(domain)

    # we mock get_resolver_domain_type to return a custom mock each time get_resolver_domain_type is called
    with mock.patch('dnsq.get_resolver_domain_type', autospec=True, side_effect=mocked_result) as get_resolver_domain_type_mock:
        resolver = dnsq.create_resolver(search=domain)

    assert isinstance(resolver, dns.resolver.Resolver)
    get_resolver_domain_type_mock.assert_called_once_with(domain=domain)
    assert isinstance(resolver.domain, dns.name.Name)
    assert resolver.search == [dns.name.from_text(domain)]
    assert resolver.lifetime == 20.0
    assert resolver.timeout == 10.0


def test_create_resolver_with_custom_nameservers_argument():
    resolver = None
    resolver = dnsq.create_resolver(nameservers=['1.2.3.4', '2.3.4.5'])

    assert isinstance(resolver, dns.resolver.Resolver)
    assert isinstance(resolver.domain, dns.name.Name)
    assert resolver.domain.to_text() != ''
    assert resolver.nameservers == ['1.2.3.4', '2.3.4.5']
    assert resolver.lifetime == 20.0
    assert resolver.timeout == 10.0


def test_ns_records_with_default_arguments_will_invoke_resolver_dot_query_and_return_a_non_empty_list_of_nameservers():
    domain = 'foo-domain.'
    mocked_results = mock_NS_Answer(domain=domain, message=MOCKED_DNS_NS_MESSAGE)

    resolver = mock.MagicMock(spec=dns.resolver.Resolver)
    resolver.query.return_value = mocked_results
    actual_ns_records = dnsq.ns_records(resolver=resolver, domain=domain)
    expected_ns_records = [x.to_text() for x in mocked_results]
    expected_ns_records.sort()

    assert actual_ns_records == expected_ns_records
    resolver.query.assert_called_once_with(domain, 'NS')


def test_ns_records_with_custom_arguments_will_invoke_resolver_dot_query_and_return_a_non_empty_list_of_nameservers():
    message = MOCKED_DNS_NS_MESSAGE
    domain = 'foo-domain.'
    mocked_results = mock_NS_Answer(domain=domain, message=message)

    resolver = mock.MagicMock(spec=dns.resolver.Resolver)
    resolver.query.return_value = mocked_results
    actual_ns_records = dnsq.ns_records(resolver, domain, 'arg1', 'arg2', key='val1', key2='val2')
    expected_ns_records = [x.to_text() for x in mocked_results]
    expected_ns_records.sort()

    assert actual_ns_records == expected_ns_records
    resolver.query.assert_called_once_with(domain, 'NS', 'arg1', 'arg2', key='val1', key2='val2')


def test_soa_records_with_default_arguments_will_invoke_resolver_dot_query_and_return_a_non_empty_list_of_SOAs():
    message = MOCKED_DNS_SOA_MESSAGE
    domain = 'foo-domain.'
    mocked_results = mock_SOA_Answer(domain=domain, message=message)

    resolver = mock.MagicMock(spec=dns.resolver.Resolver)
    resolver.query.return_value = mocked_results
    actual_ns_records = dnsq.soa_records(resolver=resolver, domain=domain)
    expected_ns_records = [x.to_text().split(' ') for x in mocked_results]

    assert actual_ns_records == expected_ns_records
    resolver.query.assert_called_once_with(domain, 'SOA')


def test_soa_records_with_custom_arguments_will_invoke_resolver_dot_query_and_return_a_non_empty_list_of_SOAs():
    message = MOCKED_DNS_SOA_MESSAGE
    domain = 'foo-domain.'
    mocked_results = mock_SOA_Answer(domain=domain, message=message)

    resolver = mock.MagicMock(spec=dns.resolver.Resolver)
    resolver.query.return_value = mocked_results
    actual_ns_records = dnsq.soa_records(resolver, domain, 'arg1', 'arg2', key='val1')
    expected_ns_records = [x.to_text().split(' ') for x in mocked_results]

    assert actual_ns_records == expected_ns_records
    resolver.query.assert_called_once_with(domain, 'SOA', 'arg1', 'arg2', key='val1')


def test_supports_zone_transfer_with_default_arguments_will_return_True():
    domain = 'foo-domain-example'
    nameserver = '1.2.999.4'

    expected_results = (
        [
            ['@', '7200', 'IN', 'SOA', 'ns1', 'root', '2018070500', '28800', '3600', '604800', '38400'],
            ['@', '7200', 'IN', 'NS', 'ns2'],
            ['@', '7200', 'IN', 'NS', 'ns1'],
            ['dc-app-01', '7200', 'IN', 'A', '192.168.1.20'],
            ['dc-app-02', '7200', 'IN', 'A', '192.168.1.21'],
            ['dc-dns-01', '7200', 'IN', 'A',  '192.168.1.10'],
            ['dns-01', '7200', 'IN', 'CNAME', 'dc-dns-01'],
        ],
    )

    for i, xfr_mock in enumerate(mock_AXFR_Answer()):
        expected = expected_results[i]
        actual = [x for x in dnsq.zone_transfer(nameserver=nameserver, domain=domain)]

        assert actual == expected
        xfr_mock.assert_called_once_with(where=nameserver, zone=domain, timeout=10.0, lifetime=20.0)


def test_supports_zone_transfer_with_default_arguments_will_raise_dns_exception_FormError_and_return_False():
    domain = 'foo-domain.'
    nameserver = '1.2.999.4'

    # every time zone_transfer is called, we raise a FormError
    with mock.patch('dnsq.zone_transfer', side_effect=dns.exception.FormError):
        actual = dnsq.supports_zone_transfer(domain=domain, nameserver=nameserver)

    assert actual is False


def test_supports_zone_transfer_with_default_arguments_will_raise_dns_exception_Timeout_and_return_False():
    domain = 'foo-domain.'
    nameserver = '1.2.999.4'

    # every time zone_transfer is called, we raise a FormError
    with mock.patch('dnsq.zone_transfer', side_effect=dns.exception.Timeout):
        actual = dnsq.supports_zone_transfer(domain=domain, nameserver=nameserver)

    assert actual is False


def test_zone_transfer_with_default_arguments_will_raise_dns_exception_FormError():
    domain = 'foo-domain.'
    nameserver = '1.2.999.4'

    # every time zone_transfer is called, we raise a FormError
    with mock.patch('dnsq.zone_transfer', side_effect=dns.exception.FormError):
        with pytest.raises(dns.exception.FormError) as exp:
            dnsq.zone_transfer(domain=domain, nameserver=nameserver)

        assert 'DNS message is malformed' in str(exp.value)


def test_zone_transfer_with_default_arguments_will_raise_dns_exception_Timeout():
    domain = 'foo-domain.'
    nameserver = '1.2.999.4'

    # every time zone_transfer is called, we raise a FormError
    with mock.patch('dnsq.zone_transfer', side_effect=dns.exception.Timeout):
        with pytest.raises(dns.exception.Timeout) as exp:
            dnsq.zone_transfer(domain=domain, nameserver=nameserver)

        assert 'The DNS operation timed out' in str(exp.value)
