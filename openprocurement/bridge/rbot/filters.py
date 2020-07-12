# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import logging
import jmespath

from gevent import sleep
from gevent.greenlet import Greenlet
from gevent.queue import Empty
from zope.interface import implementer

from openprocurement.bridge.basic.interfaces import IFilter
from openprocurement.bridge.basic.utils import journal_context


LOGGER = logging.getLogger(__name__)
INFINITY = True


@implementer(IFilter)
class ContractDataFilter(Greenlet):

    def __init__(self, conf, input_queue, filtered_queue, db):
        LOGGER.info("Init Contract Proforma Filter.")
        Greenlet.__init__(self)
        self.config = conf
        self.cache_db = db
        self.input_queue = input_queue
        self.filtered_queue = filtered_queue

        self.resource = self.config['resource']
        self.resource_id = "{}_ID".format(self.resource[:-1]).upper()

        self.statusmap = self.config['filter_config'].get('statusmap', {})
        self.timeout = self.config['filter_config']['timeout']

    def get_pmt_statuses(self, pmt):
        return self.statusmap.get(
            pmt,
            self.statusmap.get('common', [])
        )

    def _run(self):
        while INFINITY:
            if not self.input_queue.empty():
                priority, resource = self.input_queue.get()
            else:
                try:
                    priority, resource = self.input_queue.get(timeout=self.timeout)
                except Empty:
                    sleep(self.timeout)
                    continue

            cached = self.cache_db.get(resource['id'])
            if cached and cached == resource['dateModified']:
                LOGGER.info(
                    "{} {} not modified from last check. Skipping".format(self.resource[:-1].title(), resource['id']),
                    extra=journal_context({"MESSAGE_ID": "SKIPPED"}, params={self.resource_id: resource['id']})
                )
                continue

            status = resource['status']
            procurement_type = resource['procurementMethodType']
            statuses_to_process = self.get_pmt_statuses(procurement_type)

            if status not in statuses_to_process:
                LOGGER.info(
                    "Skipping {} {} {} {}".format(
                        resource['procurementMethodType'], self.resource[:-1],
                        resource['status'], resource['id']
                    ),
                    extra=journal_context(
                        {"MESSAGE_ID": "SKIPPED"},
                        params={self.resource_id: resource['id']}
                    )
                )
                continue
            LOGGER.debug(
                "Put to filtered queue {} {}".format(self.resource[:-1], resource['id'])
            )
            self.filtered_queue.put((priority, resource))
