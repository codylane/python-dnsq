#!/usr/bin/env python
# coding: utf-8
"""The interface for the command line portion of this utility."""

from __future__ import absolute_import
from __future__ import unicode_literals
# from __future__ import print_function
# from io import open

import argparse
import dnsq
import dnsq.release
import logging
import re
import sys

PROG = 'dnsq'
DESCRIPTION = 'A python DNS tool for doing fun things with DNS'


def create_parser():
    """Create a new `argparse.ArgumentParser`

    Returns:
        `argparse.ArgumentParser`

    """
    parser = argparse.ArgumentParser(prog=PROG, description=DESCRIPTION)
    resolver = dnsq.create_resolver()
    default_domain = resolver.search[0]
    default_nameserver = resolver.nameservers[0]
    default_timeout = dnsq.DEFAULT_LIFETIME
    default_sort_by = 'hostname'

    parser.add_argument('--version',
                        action='version',
                        version=dnsq.release.__version__,
                        help='Display dnsq version'
                        )

    parser.add_argument('-t', '--type',
                        choices=['ns', 'soa', 'axfr', 'zone-transfer'],
                        required=False,
                        help='A type of query to make'
                        )

    parser.add_argument('-d', '--domain',
                        default=default_domain,
                        required=False,
                        help='The domain to query. Default "{}"'.format(default_domain)
                        )

    parser.add_argument('-n', '--nameserver',
                        default=default_nameserver,
                        help='The nameserver to query. Default "{}"'.format(default_nameserver)
                        )

    parser.add_argument('-q', '--query',
                        help='Query and filter the zone transfer for a particular record'
                        )

    parser.add_argument('--sort-by',
                        choices=['hostname', 'ip'],
                        required=False,
                        help='Only used with QUERY option, allows sorting the results. Default "{}"'.format(default_sort_by)
                        )

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Turn on verbose logging, -v=INFO, -vv=DEBUG',
                        )

    parser.add_argument('--timeout',
                        action='store',
                        required=False,
                        type=float,
                        default=default_timeout,
                        help='The timeout to wait for a response from the nameserver. Default {}'.format(default_timeout)
                        )

    parser.add_argument('--supports-axfr', '--supports-zone-transfer',
                        action='store_true',
                        default=False,
                        required=False,
                        help='If domain supports a zone transfer exit 0, otherwise exit 1',
                        )

    return parser


def execute(argv=None):
    """Execute the command line with argv

    Args:
        Argv `list` or `None` - When `None` reads sys.argv[1:]

    """
    parser = create_parser()
    options = parser.parse_args(argv)
    resolver = None

    if options.verbose == 1:
        dnsq.LOGGER.setLevel(logging.INFO)
    elif options.verbose >= 2:
        dnsq.LOGGER.setLevel(logging.DEBUG)

    if options.domain and options.nameserver:
        resolver = dnsq.create_resolver(search=options.domain, nameservers=options.nameserver, lifetime=options.timeout)
        options.resolver = resolver

    if options.query:
        regex = re.compile(r'{!s}'.format(options.query))
        dnsq.LOGGER.info('Searching zone transfer for the following query: "{}"'.format(regex.pattern))
        err_msg = 'The query option requires the zone transfer capability for domain={} nameserver={}'.format(options.domain, options.nameserver)
        assert dnsq.supports_zone_transfer(domain=options.domain, nameserver=options.nameserver, lifetime=options.timeout), err_msg

        results = []
        for line in dnsq.zone_transfer(domain=options.domain, nameserver=options.nameserver, lifetime=options.timeout):
            for item in line:
                if regex.search(item):
                    hostname, rec_type, alias = (line[0], line[-2], line[-1])
                    if options.sort_by == 'ip':
                        result = ' '.join([alias, rec_type, hostname])
                    elif options.sort_by == 'hostname' or options.sort_by is None:
                        result = ' '.join([hostname, rec_type, alias])
                    results.append(result)

        # sort the results
        if options.sort_by is None or options.sort_by == 'hostname':
            sorted_results = '\n'.join(sorted(results))
            print(sorted_results)
        elif options.sort_by == 'ip':
            sorted_results = '\n'.join(dnsq.sort_ips(results))
            print(sorted_results)

        sys.exit(0)

    if options.supports_axfr:
        result = dnsq.supports_zone_transfer(domain=options.domain, nameserver=options.nameserver, lifetime=options.timeout)
        if result:
            sys.exit(0)
        sys.exit(1)

    if options.type == 'ns':
        recs = dnsq.ns_records(resolver, domain=options.domain)
        rec_str = ' '.join(recs)
        print(rec_str)
        sys.exit(0)
    elif options.type == 'soa':
        recs = dnsq.soa_records(resolver, domain=options.domain)
        print('\n'.join([' '.join(rec) for rec in recs]))
        sys.exit(0)
    elif options.type == 'axfr' or options.type == 'zone-transfer':
        err_msg = (
            'ERR: The domain: "{domain}" via nameserver: "{nameserver}"'
            'does not support AXFR (zone-transfers)\n'
        ).format(
            domain=options.domain,
            nameserver=options.nameserver
        )

        if dnsq.supports_zone_transfer(domain=options.domain, nameserver=options.nameserver, lifetime=options.timeout) is False:
            sys.stderr.write(err_msg)
            sys.exit(1)
        for line in dnsq.zone_transfer(domain=options.domain, nameserver=options.nameserver, lifetime=options.timeout):
            result = ' '.join(line)
            print(result)
        sys.exit(0)
