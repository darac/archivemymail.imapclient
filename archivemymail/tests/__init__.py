# implement basic tests
import unittest


def get_suite():
    "Return a unittest.TestSuite."
    import StatsMan

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(StatsMan.tests)
    return suite
