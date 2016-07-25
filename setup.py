from __future__ import print_function

import io
import os

try:
    from setuptools.core import setup
except ImportError:
    from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


long_description = read('README.md', 'CHANGES.txt')


setup(
    name="archivemymail",
    version='1.0',
    author="Paul Saunders",
    install_requires=['imapclient>=1.0',
                      'pyyaml>=3.11',
                      'appdirs>=1.4.0'],
    author_email='darac@darac.org.uk',
    description='Archive Mail to MBoxes, with filtering through Spam Learning',
    long_description=long_description,
    packages=['archivemymail', 'archivemymail.tests'],
    platforms='any',
    test_suite='archivemymail.tests.get_suite',
    scripts=['archivemymail.py'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
