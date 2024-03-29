[![Build Status](https://travis-ci.org/codylane/ci-pyenv.svg?branch=master)](https://travis-ci.org/codylane/ci-pyenv)

# ci-pyenv
A bash wrapper for python development projects to initialize pyenv in a CI environment

# Homepage

* https://github.com/codylane/ci-pyenv

Usage
-----

## Prep

```
git clone git@github.com:codylane/ci-pyenv.git .ci
rm -rf .ci/.git
```

* All further commands assume that you are in your project root, relative to the `.ci` directory.

## Initialize a new virtualenv

* This creates a virtualenv project named `my-special-project`
* With python `2.7.15`

* If you have a `test-requirements.txt` file in the project root directory then `enable-pyenv` will install those requirements into your virtualenv.
* If you have a `setup.py` file in the project root directory then `enable-pyenv` will `pip install -e .` into your virtualenv.

* Before we can initialize a new pyenv virtualenv we have to first tell it what the name of our project is and what python to use.

```
cat > .ci-pyenv <<EOF
CI_PYENV_PROJECT_NAME="my-special-project"
CI_PYENV_PROJECT_PYTHON="2.7.15"
EOF

.ci/init-pyenv
```

* If you already have pyenv virtualenv intialized in your shell you should notice your PS1 environment variable has changed to `(my-special-project-2.7.15)`

* If you do not see `(my-special-project-2.7.15)` in your environment variable you would do this to activate it. This makes using this virtualenv permanent or at least until you close your shell or cd out of the project root directory.

```
. .ci/enable-pyenv
INFO: running in directory /tmp/test
CMD: .ci/enable-pyenv
BIN_DIR: /tmp/test/.ci
PRJ_ROOT_DIR: /tmp/test
PYENV_ROOT: /Users/codylane/.pyenv
VENV_NAME: my-special-project
VENV_NAME_VERSION: my-special-project-2.7.15
VENV_PYTHON: 2.7.15

(my-special-project-2.7.15)
```

## Running a single add-hoc command inside the virtualenv without activating it

* Runs the command `pip list` inside the virtualenv

#### `.ci/run-pyenv 'pip list'`

```
INFO: running in directory /tmp/test
CMD: .ci/enable-pyenv
BIN_DIR: /tmp/test/.ci
PRJ_ROOT_DIR: /tmp/test
PYENV_ROOT: /Users/codylane/.pyenv
VENV_NAME: my-special-project
VENV_NAME_VERSION: my-special-proejct-2.7.15
VENV_PYTHON: 2.7.15

Package    Version
---------- -------
pip        18.0
setuptools 40.1.0
wheel      0.31.1
```

## How to initialize multiple versions of python

* Execute [Initialize a new virtualenv](#initialize-a-new-virtualenv)
* First create a `.ci-pyenv` in the project root directory.

```
cat > .ci-pyenv <<EOF
CI_PYENV_PROJECT_NAME="my-special-project"
CI_PYENV_PROJECT_PYTHON="2.7.15"

install-these-pythons() {

install-pyenv-python "3.6.5"
install-pyenv-python "3.6.6" "PERSIST"

}
EOF
```

* Run `.ci/init-pyenv`

The end result is the following:

* virtualenv name `my-special-project`
* virtualenv python `2.7.15`
* Python `3.6.5` is installed but NOT added to the `.python-version`
* Python `3.6.6` is installed and added to the `.python-version`

#### `cat .python-version`

```
my-special-project-2.7.15
3.6.6
```

#### `pyenv versions | grep '^\*'`

```
* 3.6.6 (set by /tmp/test/.python-version)
* my-special-project-2.7.15 (set by /tmp/test/.python-version)
```

TODO
----

* Figure out to test this and write automatted tests. I'll probably use [bats](https://github.com/sstephenson/bats)

License
-------

* MIT

Author
------

* Cody Lane - 2018

Contributing
------------

* Contributions and ideas are encouraged.
