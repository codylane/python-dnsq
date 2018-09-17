dnsq
----

A small python wrapper for `dnspython` to query information from DNS


# Requirements

This library requires the following to be setup before you can use this library.

- You must be using `bind 9` >= `9.10.3` as this library was only tested against this version of bind.


# Examples

This section contains examples how you might use this library

## Query the zone transfer for a specific subnet `192.168.1` and sort by `hostname`

```
$ dnsq --query '192\.168\.1' --domain foo-domain.com --nameserver 67.77.255.142 --sort-by hostname
aa-foo-01 A 192.168.1.22
dc-app-01 A 192.168.1.20
dc-app-02 A 192.168.1.21
ns1 A 192.168.1.10
ns2 A 192.168.1.11
zz-bar-01 A 192.168.1.23
```

## Query the zone transfer for a specific subnet `192.168.1` and sort by `ip`

```
$ dnsq --query '192\.168\.1' --domain foo-domain.com --nameserver 67.77.255.142 --sort-by ip
192.168.1.10 A ns1
192.168.1.11 A ns2
192.168.1.20 A dc-app-01
192.168.1.21 A dc-app-02
192.168.1.22 A aa-foo-01
192.168.1.23 A zz-bar-01
```

## Check for zone transfer support


### Example of a zone that supports a zone transfer

```
$ dnsq --supports-axfr -d foo-domain.com -n 67.77.255.142

$ echo $?
0
```

### Example of a zone that does not support a zone transfer

```
$ dnsq --supports-axfr -d some-special-domain-that-exists.com -n 67.77.255.142

$ echo $?
1
```

### Example without `domain` and `nameserver` options

* NOTE: This uses your default resolver

```
$ dnsq --supports-axfr
```

## Get the SOA records for a domain

### Example of getting the SOA records for a `domain` via `nameserver`

```
$ dnsq --type soa --domain foo-domain.com --nameserver 67.77.255.142
ns1.foo-domain.com. root.foo-domain.com. 2018070500 28800 3600 604800 86400
```

### Example of getting the SOA record using the default `domain` and `nameserver`

```
$ dnsq --type soa
ns1.foo-domain.com. root.foo-domain.com. 2018070500 28800 3600 604800 86400
```

## Get the NS records for a domain

### Example of getting the SOA records for a `domain` via `nameserver`

```
$ dnsq --type ns --domain foo-domain.com --nameserver 67.77.255.142
ns1.foo-domain.com. ns2.foo-domain.com.
```

### Example of getting the NS record using the default `domain` and `nameserver`

```
$ dnsq -t ns
ns1.foo-domain.com. ns2.foo-domain.com.
```

## Perform a zone transfer

### Performing a zone tranfer for `domain` via `nameserver`

* This tests that a zone transfer can be performed
* and if succesful, performs the zone transfer and echos the results

```
$ dnsq --type zone-transfer --domain foo-domain.com --nameserver 67.77.255.142

@ 7200 IN SOA ns1 root 2018070500 28800 3600 604800 86400
@ 7200 IN NS ns1
@ 7200 IN NS ns2
aa-foo-01 7200 IN A 192.168.1.22
app-01 7200 IN CNAME dc-app-01
dc-app-01 7200 IN A 192.168.1.20
dc-app-02 7200 IN A 192.168.1.21
dns1 7200 IN CNAME ns1
dns2 7200 IN CNAME ns2
ns1 7200 IN A 192.168.1.10
ns2 7200 IN A 192.168.1.11
zz-bar-01 7200 IN A 192.168.1.23
```

## Testing

* Create a new virtualenv and set the project directory

```
cd python-dnsq
.ci/init-pyenv
```

* Run the tests to see if they work before doing anything else

```
invoke test
```

## Known Issues

* [dnspython](https://github.com/rthalley/dnspython) has not had a new release since 2016 and there are quiet a few open issues that have not been addressed.
* This library is pretty robust and attempts to address and handle/catch exceptions as they are documented via the dnspython API, however, there are times when it just plain pukes all over the place and you'll need to re-run your command again.

### `socket.error: [Errno 54] Connection reset by peer`

* Got there error one attempting to run a zone transfer query.
* The solution in this case was just wait a hot second and try again.

```
$ dnsq --query 'dc-app-01.*' -d foo-domain.com -n  67.77.255.142

Traceback (most recent call last):
  File "~/.pyenv/versions/python-dnsq-2.7.15/bin/dnsq", line 7, in <module>
    exec(compile(f.read(), __file__, 'exec'))
  File "~/prj/python-dnsq/bin/dnsq", line 13, in <module>
    cli.execute(sys.argv[1:])
  File "ne/prj/python-dnsq/dnsq/cli.py", line 109, in execute
    assert dnsq.supports_zone_transfer(domain=options.domain, nameserver=options.nameserver, timeout=options.timeout), err_msg
  File "~/prj/python-dnsq/dnsq/__init__.py", line 190, in supports_zone_transfer
    [x for x in zone_transfer(nameserver=nameserver, domain=domain, timeout=timeout, *args, **kwargs)]
  File "~prj/python-dnsq/dnsq/__init__.py", line 213, in zone_transfer
    zone = dns.zone.from_xfr(axfr)
  File "~/.pyenv/versions/2.7.15/envs/python-dnsq-2.7.15/lib/python2.7/site-packages/dns/zone.py", line 1066, in from_xfr
    for r in xfr:
  File "~/.pyenv/versions/2.7.15/envs/python-dnsq-2.7.15/lib/python2.7/site-packages/dns/query.py", line 476, in xfr
    ldata = _net_read(s, 2, mexpiration)
  File "~/.pyenv/versions/2.7.15/envs/python-dnsq-2.7.15/lib/python2.7/site-packages/dns/query.py", line 273, in _net_read
    n = sock.recv(count)
```

### `dns.exception.Timeout: The DNS operation timed out after x.yyy seconds'`

* This error doesn't appear to happen very often but only when you are trying to run tests. So far there is no easy way to fix this error.

```
$ dnsq -t ns -n 67.77.255.142 -d foo-domain.com --timeout 8.0

AssertionError: Traceback (most recent call last):
File "~/prj/python-dnsq/.tox/py27/bin/dnsq", line 7, in <module>
exec(compile(f.read(), __file__, 'exec'))
File "~/prj/python-dnsq/bin/dnsq", line 13, in <module>
cli.execute(sys.argv[1:])
File "~/prj/python-dnsq/dnsq/cli.py", line 146, in execute
recs = dnsq.ns_records(resolver, domain=options.domain)
File "~/prj/python-dnsq/dnsq/__init__.py", line 143, in ns_records
results = [x.to_text() for x in resolver.query(domain, 'NS', *args, **kwargs)]
File "~/prj/python-dnsq/.tox/py27/lib/python2.7/site-packages/dns/resolver.py", line 1041, in query
timeout = self._compute_timeout(start)
File "~/prj/python-dnsq/.tox/py27/lib/python2.7/site-packages/dns/resolver.py", line 858, in _compute_timeout
raise Timeout(timeout=duration)
dns.exception.Timeout: The DNS operation timed out after 8.00094914436 seconds
```

# Deploying


## Clone the repository

```
$ git clone git@github.com:codylane/python-dnsq.git dnsq
```

## Install the development related libraries for your system

### Ubuntu 16.04

```
sudo apt-get install -y \
  build-essential \
  curl \
  git \
  libapt-pkg-dev \
  libbz2-dev \
  libffi-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl-dev \
  llvm \
  make \
  tk-dev \
  wget \
  xz-utils \
  zlib1g-dev \
  dnsutils \
  ntp \
  ntpdate
```

### Ubuntu 18.04

```
sudo apt-get install -y \
  build-essential \
  curl \
  git \
  libapt-pkg-dev \
  libbz2-dev \
  libffi-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl1.0-dev \
  llvm \
  make \
  tk-dev \
  wget \
  xz-utils \
  zlib1g-dev \
  dnsutils \
  ntp \
  ntpdate
```

### Centos 7.x

```
sudo yum install -y \
  epel-release \
  centos-release-scl && \
  sudo yum clean expire-cache && \
  sudo yum install -y \
    autoconf \
    automake \
    bzip2 \
    bzip2-devel \
    cmake \
    ctags \
    db4-devel \
    expat-devel \
    git \
    gcc \
    gcc-c++ \
    gdbm-devel \
    kernel-devel \
    libffi-devel \
    libpcap-devel \
    libtool \
    make \
    ncurses-devel \
    openssl-devel \
    patch \
    patchutils \
    pkgconfig \
    python-devel \
    python-setuptools \
    readline-devel \
    sqlite \
    sqlite-devel \
    sqlite2-devel \
    tk-devel \
    zlib-devel \
    xz \
    xz-devel

```

## Initialize the `virtualenv`

```
.ci/init-pyenv
```

* Add this to your shell

```
export PYENV_ROOT="${HOME}/.pyenv"
export PATH="${PYENV_ROOT}/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:${PATH}"

[ -d "${PYENV_ROOT}" ] || git clone https://github.com/pyenv/pyenv.git ${PYENV_ROOT}
[ -d "${PYENV_ROOT}/plugins/pyenv-virtualenv" ] || git clone https://github.com/pyenv/pyenv-virtualenv.git "${PYENV_ROOT}/plugins/pyenv-virtualenv"

[ -d "${PYENV_ROOT}" ] && eval "$(pyenv init -)"
[ -d "${PYENV_ROOT}/plugins/pyenv-virtualenv" ] && eval "$(pyenv virtualenv-init -)"
```

* Logout of your shell and re-login in, then cd to this directory again.

```
$ cd python-dnsq/

(python-dnsq-2.7.15) $ dnsq -h

usage: dnsq [-h] [--version] [-t {ns,soa,axfr,zone-transfer}] [-d DOMAIN]
            [-n NAMESERVER] [-q QUERY] [--sort-by {hostname,ip}] [-v]
            [--timeout TIMEOUT] [--supports-axfr]

A python DNS tool for doing fun things with DNS

optional arguments:
  -h, --help            show this help message and exit
  --version             Display dnsq version
  -t {ns,soa,axfr,zone-transfer}, --type {ns,soa,axfr,zone-transfer}
                        A type of query to make
  -d DOMAIN, --domain DOMAIN
                        The domain to query. Default "foo-example.com."
  -n NAMESERVER, --nameserver NAMESERVER
                        The nameserver to query. Default "192.168.1.88"
  -q QUERY, --query QUERY
                        Query and filter the zone transfer for a particular
                        record
  --sort-by {hostname,ip}
                        Only used with QUERY option, allows sorting the
                        results. Default "hostname"
  -v, --verbose         Turn on verbose logging, -v=INFO, -vv=DEBUG
  --timeout TIMEOUT     The timeout to wait for a response from the
                        nameserver. Default 20.0
  --supports-axfr, --supports-zone-transfer
                        If domain supports a zone transfer exit 0, otherwise
                        exit 1
```

## Author

* Cody Lane - 2018
