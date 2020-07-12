# -*- coding: utf-8 -*-
import logging
import requests
import json
from functools import partial
from io import BytesIO
from tooz import coordination
from jsonschema import validate, ValidationError
from openprocurement.bridge.basic.handlers import HandlerTemplate
from openprocurement.bridge.basic.utils import journal_context
from openprocurement_client.clients import APIResourceClient
from openprocurement.bridge.rbot.renderer import HttpRenderer
from openprocurement.bridge.rbot.defaults import CONFIG_MAPPING, config
from openprocurement.bridge.rbot.utils import (
    get_contract_data_documents,
    get_contract_schema_documents,
    get_contract_proforma_documents,
    get_contract_template_documents,
    prepare_proforma_data,
    merge_contract_data
)

from .tests.data import CONTRACT_DATA


logger = logging.getLogger(__name__)


class RendererBot(HandlerTemplate):

    def __init__(self, config, cache_db):
        logger.info("Init renderer bot handler.")
        self.handler_name = "handler_rBot"
        super(RendererBot, self).__init__(config, cache_db)

    def initialize_clients(self):
        self.tender_client = APIResourceClient(
            key=self.handler_config.get('resources_api_token'),
            resource=self.handler_config['resource'],
            host_url=self.handler_config['resources_api_server'],
            api_version=self.handler_config['resources_api_version'],
            ds_config=self.handler_config.get('DS', {}),
        )
        self.renderer = HttpRenderer(self.handler_config['webrenderer_url'])

    def upload_contract_proforma(self, resource, proforma_template, file_):
        logger.info(
            "Update contract proforma document {} of tender {}".format(
                proforma_template['id'],
                resource['id']
            )
        )
        additional_doc_data = {
            'templateId': proforma_template['templateId'],
            'relatedItem': proforma_template['id'],
            'title': 'contractProforma.pdf',
            'documentOf': 'document'
        }
        return self.tender_client.upload_document(
            BytesIO(file_),
            resource['id'],
            doc_type='contractProforma',
            additional_doc_data=additional_doc_data
        )

    def upload_contract_document(self, file_, tender_id, contract_id,
                                 related_item=None, doc_type='contractData',
                                 title='contractData.json'):
        additional_doc_data = {
            'title': title,
            'documentOf': 'document'
        }
        if related_item:
            additional_doc_data['relatedItem'] = related_item
        return self.tender_client.upload_document(
            BytesIO(file_),
            tender_id,
            doc_type=doc_type,
            additional_doc_data=additional_doc_data,
            depth_path='{}/{}'.format('contracts', contract_id)
        )

    def get_file(self, url):
        return self.tender_client.session.get(url).content

    def get_file_json(self, url):
        return json.loads(self.get_file(url))

    def get_document_content(self, resource, getter, as_json=False):
        docs = getter(resource)
        if not docs:
            return None
        downloader = self.get_file_json if as_json else self.get_file
        return downloader(docs[-1]['url'])

    def get_latest_doc(self, resource, getter, msg):
        docs = getter(resource)
        if not docs:
            logger.info(
                "{} tender {} in {} does not contain {}. Skipping...".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],
                    msg

                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={"TENDER_ID": resource['id']}
                )
            )
            return
        return docs[-1]

    def process_resource(self, resource):

        contract_proforma = self.get_latest_doc(resource,
                                                get_contract_proforma_documents,
                                                "contractProforma")
        if not contract_proforma:
            return
        
        data_doc = self.get_latest_doc(
            resource,
            partial(get_contract_data_documents, related_item=contract_proforma['id']),
            "contractData"
        )
        if not data_doc:
            return

        schema_doc = self.get_latest_doc(
            resource,
            partial(get_contract_schema_documents, related_item=contract_proforma['id']),
            "contractSchema"
        )
        if not schema_doc:
            return
        template_doc = self.get_latest_doc(
            resource,
            partial(get_contract_template_documents, related_item=contract_proforma['id']),
            "contractSchema"
        )
        if not template_doc:
            return

        try:
            buyer_data = self.get_file_json(data_doc['url'])
        except Exception as e:
            logger.info(
                "Failed to parse contract data document in {} tender {} in {}. Skipping...".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={"TENDER_ID": resource['id']}
                )
            )
            return

        # document still not rendered
        if contract_proforma['dateModified'] < template_doc['dateModified']:
            logger.info("Rendering proforma document {} pdf of tender {}({})".format(
                contract_proforma['id'],
                resource['id'],
                resource['procurementMethodType'],
            ))
            template = self.get_file(template_doc['url'])
            proforma_data = prepare_proforma_data(resource, buyer_data)
            # TODO: validate
            # schema = self.get_file_json(schema_doc['url'])
            # if self.validate_contract_data(contract_data, scheme):
            # TODO: this will not work for resources before active.awarded
            contract_proforma_pdf = self.renderer.render(template,
                                                         proforma_data,
                                                         name=template_doc['title'])
            if contract_proforma_pdf.status_code == 200:
                result = self.upload_contract_proforma(resource,
                                                       contract_proforma,
                                                       contract_proforma_pdf.content)
                if result.get('status', '') == 'error':
                    logger.error('Failed to uploaded contractProforma document to tender {} with errors: {}'.format(
                        resource['id'],
                        result.errors
                    ))
                else:
                    logger.info('Uploaded contractProforma document {} for proforma template {} to tender {}({})'.format(
                        result.data.id,
                        contract_proforma['id'],
                        resource['id'],
                        resource['procurementMethodType'])
                    )
            else:
                try:
                    msg = contract_proforma_pdf.json()['error']['message']
                except:
                    msg = contract_proforma_pdf.text
                logger.error('Failed to render contractProforma document to tender {} with errors: {}'.format(
                    resource['id'],
                    msg
                ))
                return
        else:
            logger.info(
                "{} tender {} in {} already contains contractProforma. Skipping...".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],

                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={"TENDER_ID": resource['id']}
                )
            )
            return

        if resource['status'] == 'active.awarded':
            for contract in [c for c in resource.get('contracts') if c['status'] == 'pending']:
                award = [a for a in resource.get('awards') if contract['awardID'] == a['id']][-1]
                bid = [b for b in resource.get('bids') if b['id'] == award['bid_id']][-1]
                supplier_data = self.get_document_content(bid, get_contract_data_documents)

                # TODO: supplier and buyer data example? how to differentiate?
                bid_and_supplier_data = self.get_document_content(
                    award, get_contract_data_documents
                )
                contract_data = merge_contract_data(buyer_data,
                                                    supplier_data or {},
                                                    bid_and_supplier_data or {})
                doc = self.upload_contract_document(contract_data,
                                                    resource['id'],
                                                    contract['id'],
                                                    related_item=contract_proforma['id'])
                if doc.get('status', '') == 'error':
                    logger.error('Failed to uploaded contractData document to tender {} contract {} with errors: {}'.format(
                        resource['id'],
                        contract['id'],
                        result.errors
                    ))
                else:
                    logger.info('Uploaded contractData document {} to contract {} of tender {}({})'.format(
                        result.data.id,
                        contract['id'],
                        resource['id'],
                        resource['procurementMethodType'])
                    )

                contract_pdf = self.renderer.render(template,
                                                    contract_data,
                                                    name=template_doc['title'])
                if contract_pdf.status_code == 200:
                    result = self.upload_contract_document(
                        contract_pdf,
                        resource['id'],
                        contract['id'],
                        doc_type='contract',
                        title='contract.pdf'
                        )
                    if result.get('status', '') == 'error':
                        logger.error('Failed to uploaded contract to tender {} with errors: {}'.format(
                            resource['id'],
                            result.errors
                        ))
                    else:
                        logger.info('Uploaded contract document {} for proforma template {} to tender {}({})'.format(
                            result.data.id,
                            contract_proforma['id'],
                            resource['id'],
                            resource['procurementMethodType'])
                        )
                else:
                    try:
                        msg = contract_proforma_pdf.json()['error']['message']
                    except:
                        msg = contract_proforma_pdf.text
                        logger.error('Failed to render contractProforma document to tender {} with errors: {}'.format(
                            resource['id'],
                            msg
                        ))
                        return
