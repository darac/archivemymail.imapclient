from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.txt', 'CHANGES.txt')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name="archivemymail",
    version=1,
    author="Paul Saunders",
    tests_require=['pytest'],
    install_requires=['imapclient>=1.0'],
    cmdclass={'test': PyTest},
    author_email='darac@darac.org.uk',
    description='Archive Mail to MBoxes, with filtering through Spam Learning',
    long_description=long_description,
    packages=['archivemymail'],
    include_packages_data=True,
    platforms='any',
    test_suite='archivemymail.test.test_archivemymail',
    extras_require={'testing':['pytest']},
)
