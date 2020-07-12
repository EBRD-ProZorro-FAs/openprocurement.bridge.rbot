# -*- coding: utf-8 -*-
import unittest

from openprocurement.bridge.rbot.tests import handlers, filters, render


def suite():
    tests = unittest.TestSuite()
    tests.addTest(handlers.suite())
    tests.addTest(filters.suite())
    tests.addTest(render.suite())
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
