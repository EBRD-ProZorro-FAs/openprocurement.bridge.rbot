import unittest
import os
import requests.exceptions
from openprocurement.bridge.rbot.renderer import HttpRenderer
from openprocurement.bridge.rbot.tests.data import TENDER,\
    TEMPLATE_PATH, BUYER, CONTRACT_DATA, SUPPLIER


RENDERER_URL = os.environ.get('TEST_RENDERER_URL', 'http://edge-prod-hw.office.quintagroup.com:8080/')


class TestHttpRenderer(unittest.TestCase):

    def setUp(self):
        self.renderer = HttpRenderer(RENDERER_URL)

    def test_render_ok(self):
        data = CONTRACT_DATA
        with open(TEMPLATE_PATH, 'rb') as template:
            try:
                resp = self.renderer.render(template, data)
                resp.raise_for_status()
            except requests.exceptions.RequestException:
                self.fail("Failed to render! Data: {}".format(data))
            


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestHttpRenderer))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')
