# RUNME as 'python -m archivemymail.tests.__main__'
import unittest

import archivemymail.tests


def main():
    "Run all of the tests when run as a module with -m."
    suite = archivemymail.tests.get_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
