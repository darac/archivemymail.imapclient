from __future__ import absolute_import
# implement basic tests
import unittest

def get_suite():
    "Return a unittest.TestSuite."

    from . import test_StatsMan

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_StatsMan)
    return suite