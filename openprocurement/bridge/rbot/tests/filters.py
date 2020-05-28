# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy
from mock import patch

from gevent.queue import PriorityQueue
from openprocurement.bridge.rbot.filters import StatuslistFilter


CONFIG = {
    'filter_config': {
        'statuslist': ['active.tendering', 'active.awarded'],
        'timeout': 0,
    },
    'resource': 'tenders'
}


class TestStutuslistFilter(unittest.TestCase):

    def setUp(self):
        self.conf = CONFIG
        self.db = {}
        self.input_queue = PriorityQueue()
        self.filtered_queue = PriorityQueue()
        self.filter = StatuslistFilter(self.conf, self.input_queue, self.filtered_queue, self.db)

    @patch('openprocurement.bridge.rbot.filters.INFINITY')
    def test_filter_ok(self, infinity):
        infinity.__nonzero__.side_effect = [True, False]
        doc = {
            'id': 'test_id',
            'dateModified': '1970-01-02',
            'procurementMethodType': 'dgf',
            'status': 'active.tendering',
            'documents': [
                {
                    'documentType': 'contractProforma'
                }
            ]
        }

        self.input_queue.put((None, deepcopy(doc)))
        self.filter._run()
        self.assertEqual(len(self.filtered_queue), 1)
        filtered_doc = self.filtered_queue.get(block=False)
        self.assertEqual(
            doc,
            filtered_doc[1]
        )

    @patch('openprocurement.bridge.rbot.filters.INFINITY')
    def test_filter_not_modified(self, infinity):
        # Not changed dateModified
        infinity.__nonzero__.side_effect = [True, False]
        doc = {
            'id': 'test_id',
            'dateModified': '1970-01-01',
            'procurementMethodType': 'dgf',
            'status': 'status1',
            'documents': [
                {
                    'documentType': 'contractProforma'
                }
            ],
        }

        self.input_queue.put((None, deepcopy(doc)))
        self.db['test_id'] = '1970-01-01'

        self.filter._run()
        self.assertEqual(len(self.filtered_queue), 0)
        self.db.pop('test_id')

    @patch('openprocurement.bridge.rbot.filters.INFINITY')
    def test_filter_by_status(self, infinity):
        # Wrong tender status
        infinity.__nonzero__.side_effect = [True, False]
        doc = {
            'id': 'test_id',
            'dateModified': '1970-01-01',
            'procurementMethodType': 'dgf',
            'status': 'status3',
            'documents': [
                {
                    'documentType': 'contractProforma'
                }
            ],
        }

        self.input_queue.put((None, deepcopy(doc)))
        self.filter._run()
        self.assertEqual(len(self.filtered_queue), 0)


def suite():
    suite = unittest.TestSuite()
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')
