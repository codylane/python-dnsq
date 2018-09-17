# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals


import dns.exception
import dns.query
import dns.resolver
import dns.zone
import io
import logging
import socket
import struct
import sys
import types

# configure logging
LOGGING_FORMAT = '%(asctime)s::%(levelname)s::%(funcName)s::%(message)s'
LOGGING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S %Z'
logging.basicConfig(level=logging.WARNING, format=LOGGING_FORMAT, datefmt=LOGGING_DATE_FORMAT)
LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
DEFAULT_LIFETIME = DEFAULT_TIMEOUT * 2

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
STRING_TYPE = None

if PY2:
    STRING_TYPE = basestring
    IntType = types.IntType
    open = io.open
else:
    STRING_TYPE = str
    xrange = range
    IntType = type(int)
    # Python 3.4+
    from importlib import reload  # noqa: F401


def sort_ips(ips):
    """Given a list of @ips, sort them

    Credit: https://stackoverflow.com/questions/6545023/how-to-sort-ip-addresses-stored-in-dictionary-in-python/6545090#6545090

    Args:
        ips `list` `tuple` - A list or tuple of ips

    """
    return sorted(ips, key=lambda ip: struct.unpack('!L', socket.inet_aton(ip))[0])


def get_resolver_domain_type(domain):
    """A wrapper to validate and return the correct domain type for a resolver

    Args:
        domain - One of the following types `basestring, str, list, tuple, dns.name.Name`

    Raises:
        AssertionError - When domain type is invalid

    Returns:
        `dns.name.Name`

    """
    supported_types = (
        STRING_TYPE,
        list,
        tuple,
        dns.name.Name,
    )

    err_msg = 'Expected domain to be one of {supported_types}, got {invalid_type}'.format(supported_types=supported_types,
                                                                                          invalid_type=type(domain).__name__
                                                                                          )
    assert isinstance(domain, supported_types), err_msg

    if isinstance(domain, STRING_TYPE):
        LOGGER.debug('The domain: {} is a string'.format(domain))
        return dns.name.from_text(domain)

    if isinstance(domain, (list, tuple)):
        LOGGER.debug('The domain: {} is a list or tuple'.format(domain))
        return dns.name.Name(domain)

    # if we get here then domain must be dns.name.Name
    LOGGER.debug('The domain: {} is {}'.format(domain, type(domain)))
    return domain


def create_resolver(search=None, nameservers=None, lifetime=DEFAULT_LIFETIME, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
    """A wrapper to simplify creation of a resolver so that we can do DNS queries

    Args:
        search `str, list, tuple, dns.name.Name` - The search domain to be used for our DNS query.
        nameservers `list, tuple` - A list of nameservers to query.
                                    Each nameserver is a string which contains the IP address of a nameserver.
        lifetime `float` - The total number of seconds to spend doing the transfer. If ``None``, then there is no limit on the time the transfer may take.
        timeout `float` - The number of seconds to wait for each response message.

    Returns:
        `dns.resolver.Resolver`

    """
    LOGGER.info(dict(search=search, nameservers=nameservers, lifetime=lifetime, timeout=timeout, args=args, kwargs=kwargs))

    resolver = dns.resolver.Resolver(*args, **kwargs)
    resolver.lifetime = lifetime
    resolver.timeout = timeout

    if search:
        resolver.search = [get_resolver_domain_type(domain=search)]
        resolver.domain = resolver.search[0]
        LOGGER.debug('Setting search to: {}'.format(resolver.search))
        LOGGER.debug('Setting domain to: {}'.format(resolver.domain))

    if nameservers:
        if isinstance(nameservers, STRING_TYPE):
            nameservers = [nameservers]
        resolver.nameservers = nameservers
        LOGGER.debug('Setting nameservers to: {}'.format(resolver.nameservers))

    return resolver


def ns_records(resolver, domain, *args, **kwargs):
    """Returns a list of NS records for a domain

    Args:
        resolver `dns.resolver.Resolver` - A resolver instance.
        domain `str` - The domain containing the NS record(s).

    Returns:
        `list` - A list of NS records that are sorted
                 [
                    'nsztm1.digi.ninja.',
                    'nsztm2.digi.ninja.',
                 ]

    """
    LOGGER.info(dict(resolver=resolver, domain=domain, args=args, kwargs=kwargs))
    results = [x.to_text() for x in resolver.query(domain, 'NS', *args, **kwargs)]
    return sorted(results)


def soa_records(resolver, domain, *args, **kwargs):
    """Returns a list of SOA records for a domain

    Args:
        resolver `dns.resolver.Resolver` - A resolver instance.
        domain `str` - The domain containing the SOA record(s).

    Returns:
        `list` - A list of lists that are sorted
                [
                    [
                        'nsztm1.digi.ninja.',
                        'robin.digi.ninja.',
                        '2017042001',
                        '172800',
                        '900',
                        '1209600',
                        '3600'
                    ]
                ]


    """
    LOGGER.info(dict(resolver=resolver, domain=domain, args=args, kwargs=kwargs))
    results = [x.to_text().split(' ') for x in resolver.query(domain, 'SOA', *args, **kwargs)]
    return sorted(results)


def supports_zone_transfer(domain, nameserver, lifetime=DEFAULT_LIFETIME, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
    """Tests if a nameserver, supports a zone transfer for a specific domain

    Args:
        domain `str` - The domain to check. Ex: `zonetransfer.me`.
        nameserver `str` - The name server to query. Ex: `nsztm1.digi.ninja`.
        timeout `float` - The number of seconds to wait for each response message.
        lifetime `float` - The total number of seconds to spend doing the transfer. If ``None``, then there is no limit on the time the transfer may take.

    Returns:
        bool - Returns `True` when the nameserver supports a zone transfer for domain, otherwise `False`

    """
    try:
        LOGGER.info(dict(domain=domain, nameserver=nameserver, lifetime=lifetime, timeout=timeout, args=args, kwargs=kwargs))
        [x for x in zone_transfer(nameserver=nameserver, domain=domain, timeout=timeout, *args, **kwargs)]
        return True
    except dns.exception.FormError:
        pass
    except dns.exception.Timeout:
        pass
    return False


def zone_transfer(domain, nameserver, timeout=DEFAULT_TIMEOUT, lifetime=DEFAULT_LIFETIME, *args, **kwargs):
    """Perform a zone-transfer via nameserver

    Args:
        domain `str` - The domain to check. Ex: `zonetransfer.me`.
        nameserver `str` - The name server to query. Ex: `nsztm1.digi.ninja`.
        timeout `float` - The number of seconds to wait for each response message.
        lifetime `float` - The total number of seconds to spend doing the transfer. If ``None``, then there is no limit on the time the transfer may take.

    Returns:
        `generator` - of sorted zone transfer encoded strings

    """
    axfr = dns.query.xfr(where=nameserver, zone=domain, timeout=timeout, lifetime=lifetime, *args, **kwargs)
    zone = dns.zone.from_xfr(axfr)

    # py36 .keys returns dict_keys so we work around it
    hostnames = sorted(zone.nodes.keys())

    for hostname in hostnames:
        for line in zone[hostname].to_text(hostname).splitlines():
            yield line.split(' ')
