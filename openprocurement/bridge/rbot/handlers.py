# -*- coding: utf-8 -*-
import logging

from openprocurement.bridge.basic.handlers import HandlerTemplate
from openprocurement.bridge.basic.utils import journal_context
from tooz import coordination


config = {
    "worker_type": "contracting",
    "client_inc_step_timeout": 0.1,
    "client_dec_step_timeout": 0.02,
    "drop_threshold_client_cookies": 2,
    "worker_sleep": 5,
    "retry_default_timeout": 3,
    "retries_count": 10,
    "queue_timeout": 3,
    "bulk_save_limit": 100,
    "bulk_save_interval": 3,
    "resources_api_token": "",
    "resources_api_version": "",
    "input_resources_api_server": "",
    "input_public_resources_api_server": "",
    "input_resource": "tenders",
    "output_resources_api_server": "",
    "output_public_resources_api_server": "",
    "output_resource": "agreements",
    "handler_cfaua": {
        "resources_api_token": "",
        "output_resources_api_token": "agreement_token",
        "resources_api_version": "",
        "input_resources_api_token": "tender_token",
        "input_resources_api_server": "",
        "input_public_resources_api_server": "",
        "input_resource": "tenders",
        "output_resources_api_server": "",
        "output_public_resources_api_server": "",
        "output_resource": "agreements"
    }
}

CONFIG_MAPPING = {
    "input_resources_api_token": "resources_api_token",
    "output_resources_api_token": "resources_api_token",
    "resources_api_version": "resources_api_version",
    "input_resources_api_server": "resources_api_server",
    "input_public_resources_api_server": "public_resources_api_server",
    "input_resource": "resource",
    "output_resources_api_server": "resources_api_server",
    "output_public_resources_api_server": "public_resources_api_server"
}


logger = logging.getLogger(__name__)


class RBot(HandlerTemplate):

    def __init__(self, config, cache_db):
        logger.info("Init renderer bot.")
        self.handler_name = "handler_rbot"
        super(RBot, self).__init__(config, cache_db)
        coordinator_config = config.get("coordinator_config", {})
        self.coordinator = coordination.get_coordinator(coordinator_config.get("connection_url", "redis://"),
                                                        coordinator_config.get("coordinator_name", "bridge"))
        self.coordinator.start(start_heart=True)

    def initialize_clients(self):
        self.tender_client = self.create_api_client()

    def process_resource(self, resource):
        pass
