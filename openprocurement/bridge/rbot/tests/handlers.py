import unittest
from copy import deepcopy
from datetime import datetime

from mock import MagicMock, call, patch
from munch import munchify
from openprocurement.bridge.basic.tests.base import AdaptiveCache
from openprocurement.bridge.rbot.handlers import RendererBot
from openprocurement.bridge.rbot.tests.data import TENDER
from openprocurement_client.exceptions import ResourceGone, ResourceNotFound


class TestRendererHandler(unittest.TestCase):
    config = {
        'worker_config': {
            'handler_rBot': {
                'resources_api_token': 'resources_api_token',
                'resources_api_version': 'resources_api_version',
                'resources_api_server': 'resources_api_server',
                'resource': 'resource',
                'output_resource': 'output_resource',
                'DS': {
                    'host_url': 'host_url',
                    'auth_ds': 'auth_ds',
                },
                'webrenderer_url': 'http://localhost:8080'
            },
        },
        'public_resources_api_server': 'http://localhost:6543',
        'resources_api_token': 'resources_api_token',
        'resources_api_version': 'resources_api_version',
        'resources_api_server': 'resources_api_server',
        'resource': 'resource',
        'output_resource': 'output_resource',
    }

    @patch('openprocurement.bridge.basic.handlers.APIClient')
    def test_init(self, mocked_client):
        handler = RendererBot(self.config, 'cache_db')

        self.assertEquals(handler.cache_db, 'cache_db')
        self.assertEquals(handler.handler_config, self.config['worker_config']['handler_rBot'])
        self.assertEquals(handler.main_config, self.config)
        self.assertEquals(handler.config_keys,
                          ('input_resources_api_token', 'output_resources_api_token', 'resources_api_version',
                           'input_resources_api_server',
                           'input_public_resources_api_server', 'input_resource', 'output_resources_api_server',
                           'output_public_resources_api_server', 'output_resource')
                          )
        self.assertTrue(hasattr(handler, 'tender_client'))
        self.assertTrue(hasattr(handler, 'config'))


    @patch('openprocurement.bridge.rbot.handlers.logger')
    @patch('openprocurement.bridge.basic.handlers.APIClient')
    def test_process_resource(self, logger, tender_client):
        cache_db = AdaptiveCache({'0' * 32: datetime.now().isoformat()})
        handler = RendererBot(self.config, cache_db)

        resource = deepcopy(TENDER)
        resource['id'] = '0' * 32
        resource = munchify(resource)

        # test not found profile in catalogue
        # not_found_exception = ResourceNotFound()
        # handler.catalogues_client.profiles.get_profile.side_effect = (not_found_exception,)

    #     handler.process_resource(resource.data)
    #     self.assertEquals(len(handler.tender_client.patch_resource_item.mock_calls), 1)
    #     self.assertEquals(handler.tender_client.patch_resource_item.mock_calls[0],
    #                       call(resource.data.id, {'data': {'status': 'draft.unsuccessful'}}))
    #     handler.tender_client.patch_resource_item.reset_mock()

    #     # test not found category in catalogue
    #     handler.catalogues_client.profiles.get_profile.side_effect = (munchify(deepcopy(TEST_PROFILE)),)
    #     handler.catalogues_client.categories.get_category_suppliers.side_effect = (not_found_exception,)

    #     handler.process_resource(resource.data)
    #     self.assertEquals(len(handler.tender_client.patch_resource_item.mock_calls), 1)
    #     self.assertEquals(handler.tender_client.patch_resource_item.mock_calls[0],
    #                       call(resource.data.id, {'data': {'status': 'draft.unsuccessful'}}))
    #     handler.tender_client.patch_resource_item.reset_mock()

    #     # test with empty list supplier in catalogue category
    #     handler.catalogues_client.profiles.get_profile.side_effect = (munchify(deepcopy(TEST_PROFILE)),)
    #     handler.catalogues_client.categories.get_category_suppliers.side_effect = (munchify({'data': []}),)

    #     handler.process_resource(resource.data)
    #     self.assertEquals(len(handler.tender_client.patch_resource_item.mock_calls), 1)
    #     self.assertEquals(handler.tender_client.patch_resource_item.mock_calls[0],
    #                       call(resource.data.id, {'data': {'status': 'draft.unsuccessful'}}))
    #     handler.tender_client.patch_resource_item.reset_mock()

    #     # test successfull switch to `active.tendering`
    #     suppliers = {'data': deepcopy(TEST_CATEGORY)['data']['suppliers']}

    #     handler.catalogues_client.profiles.get_profile.side_effect = (munchify(deepcopy(TEST_PROFILE)),)
    #     handler.catalogues_client.categories.get_category_suppliers.side_effect = (munchify(suppliers),)

    #     self.assertNotIn('classification', resource.data['items'][0])
    #     self.assertNotIn('unit', resource.data['items'][0])
    #     handler.process_resource(resource.data)

    #     items = deepcopy(TENDER['data']['items'])
    #     items[0]['classification'] = TEST_PROFILE['data']['classification']
    #     if 'additionalClassifications' in TEST_PROFILE['data']:
    #         items[0]['additionalClassifications'] = TEST_PROFILE['data']['additionalClassifications']
    #     items[0]['unit'] = TEST_PROFILE['data']['unit']
    #     value = deepcopy(TEST_PROFILE['data']['value'])
    #     amount = sum([item["quantity"] for item in items]) * TEST_PROFILE['data']['value']['amount']
    #     value['amount'] = amount
    #     shortlisted_firms = [s for s in TEST_CATEGORY['data']['suppliers'] if s['status'] == 'active']
    #     criteria = deepcopy(TEST_PROFILE['data']['criteria'])
    #     for criterion in criteria:
    #         criterion.pop('code', None)
    #         for rq_group in criterion['requirementGroups']:
    #             for rq in rq_group['requirements']:
    #                 if rq['dataType'] == 'string':
    #                     continue
    #                 for key in requirement_keys:
    #                     if key in rq:
    #                         rq[key] = str(rq[key])
    #     patch_data = {
    #         'data': {
    #             'criteria': criteria,
    #             'status': 'active.tendering',
    #             'items': items,
    #             'shortlistedFirms': shortlisted_firms,
    #             'value': value
    #         }
    #     }
    #     self.assertEquals(handler.tender_client.patch_resource_item.mock_calls[0], call(resource.data.id, patch_data))

    #     # test tender not found
    #     handler.catalogues_client.profiles.get_profile.side_effect = (munchify(deepcopy(TEST_PROFILE)),)
    #     handler.catalogues_client.categories.get_category_suppliers.side_effect = (munchify(suppliers),)
    #     handler.tender_client.patch_resource_item.side_effect = (not_found_exception,)

    #     handler.process_resource(resource.data)
    #     self.assertEquals(len(logger.critical.mock_calls), 1)
    #     self.assertEquals(logger.critical.mock_calls[0], call("Tender {} not found".format(resource.data.id)))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRendererHandler))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')
