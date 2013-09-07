# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import unittest
import trytond.tests.test_tryton

from tests.test_views import TestViewDepend
from tests.test_country import TestCountry
from tests.test_party import TestParty


def suite():
    """
    Define suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestViewDepend),
        unittest.TestLoader().loadTestsFromTestCase(TestCountry),
        unittest.TestLoader().loadTestsFromTestCase(TestParty),
    ])
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
