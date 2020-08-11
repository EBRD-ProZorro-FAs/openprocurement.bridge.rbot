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
from openprocurement.bridge.rbot.merge import Merger
from openprocurement.bridge.rbot.utils import (
    get_contract_data_documents,
    get_contract_schema_documents,
    get_contract_proforma_documents,
    get_contract_template_documents,
    get_contract_documents
)


logger = logging.getLogger(__name__)


class RendererBot(HandlerTemplate):

    def __init__(self, config, cache_db):
        logger.info("Init renderer bot handler.")
        self.handler_name = "handler_rBot"
        super(RendererBot, self).__init__(config, cache_db)

    def initialize_clients(self):
        self.tender_client = APIResourceClient(
            key=self.handler_config.get('resources_api_token'),
            resource='tenders',
            host_url=self.handler_config['resources_api_server'],
            api_version=self.handler_config['resources_api_version'],
            ds_config=self.handler_config.get('DS', {}),
        )
        self.plans_client = APIResourceClient(
            key=self.handler_config.get('resources_api_token'),
            resource='plans',
            host_url=self.handler_config['resources_api_server'],
            api_version=self.handler_config['resources_api_version'],
        )
        self.renderer = HttpRenderer(self.handler_config['webrenderer_url'])

    def upload_contract_proforma(self, resource, proforma_template, file_):
        logger.info(
            "Update contract proforma document {} of tender {}".format(
                proforma_template['id'],
                resource['id']
            ),
            extra=journal_context(
                {"MESSAGE_ID": "DOCUMENT_UPDATE"},
                params={
                    "TENDER_ID": resource['id'],
                    "PROFORMA_ID": proforma_template['id']
                }
            )
        )
        additional_doc_data = {
            'format': 'application/pdf',
            'title': 'contractProforma.pdf',
            'documentOf': 'tender',
            'templateId': proforma_template['templateId']
        }
        return self.tender_client.update_document(
            BytesIO(file_),
            resource['id'],
            proforma_template['id'],
            doc_type='contractProforma',
            additional_doc_data=additional_doc_data
        )

    def upload_contract_document(self,
                                 file_,
                                 tender_id,
                                 contract_id,
                                 related_item=None,
                                 doc_type='contractData',
                                 title='contractData.json'):
        additional_doc_data = {
            'title': title,
            'documentOf': 'document',
            'relatedItem': related_item
        }
        return self.tender_client.upload_document(
            BytesIO(file_),
            tender_id,
            doc_type=doc_type,
            additional_doc_data=additional_doc_data,
            depth_path='{}/{}'.format('contracts', contract_id)
        )

    def update_contract_document(self,
                                 file_,
                                 tender_id,
                                 contract_id,
                                 document,
                                 doc_type='contractData',
                                 title='contractData.json'):
        additional_doc_data = {
            'title': document['title'],
            'documentOf': document['documentOf'],
            'relatedItem': document['relatedItem']
        }
        return self.tender_client.update_document(
            BytesIO(file_),
            tender_id,
            document['id'],
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
            return {}
        downloader = self.get_file_json if as_json else self.get_file
        return downloader(docs[-1]['url'])

    def get_latest_doc(self, resource, getter, msg, tender=None):
        docs = getter(resource)
        if not tender:
            tender = resource
        if not docs:
            logger.info(
                "{} tender {} in {} does not contain {}.".format(
                    tender['procurementMethodType'],
                    tender['id'],
                    tender['status'],
                    msg

                ),
                extra=journal_context(
                    {"MESSAGE_ID": "MISSING"},
                    params={"TENDER_ID": tender['id']}
                )
            )
            return
        return docs[-1]

    def validate_data(self, resource, data, schema):
        try:
            validate(data, schema)
            return True
        except ValidationError as e:
            logger.warn(
                "Validation of proforma for role {} data in resource {}({}) failed with error {}".format(
                    data['role'],
                    resource['id'],
                    resource['procurementMethodType'],
                    e
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "VALIDATION"},
                    params={"TENDER_ID": resource['id']}
                )
            )
            return False

    def get_plan(self, plan_id):
        return self.plans_client.get_resource_item(plan_id)

    def generate_and_upload_proforma(self, resource, template, template_doc, proforma_data, contract_proforma):
        title = template_doc['title']
        if not title.endswith('docx'):
            title = '{}.docx'.format(title)
        contract_proforma_pdf = self.renderer.render(template,
                                                     proforma_data,
                                                     name=title)
        if contract_proforma_pdf.status_code == 200:
            try:
                result = self.upload_contract_proforma(resource,
                                                       contract_proforma,
                                                       contract_proforma_pdf.content)
            except Exception as e:
                logger.error(
                    'Failed to uploaded contractProforma {} document to tender {} with errors: {}'.format(
                        resource['id'],
                        template_doc['relatedItem'],
                        e
                    ),
                    extra=journal_context(
                        {"MESSAGE_ID": "UPLOAD"},
                        params={
                            "TENDER_ID": resource['id'],
                            "PROFORMA_ID": template_doc['relatedItem']
                        }
                    )
                )
            else:
                logger.info(
                    'Uploaded contractProforma document {} for proforma template {} to tender {}({})'.format(
                        result.data.id,
                        template_doc['relatedItem'],
                        resource['id'],
                        resource['procurementMethodType']
                    ),
                    extra=journal_context(
                        {"MESSAGE_ID": "UPLOAD"},
                        params={
                            "TENDER_ID": resource['id'],
                            "PROFORMA_ID": template_doc['relatedItem']
                        }
                    )
                )
        else:
            try:
                msg = contract_proforma_pdf.json()['error']['message']
            except:
                msg = contract_proforma_pdf.text
            logger.error(
                'Failed to render contractProforma {} document to tender {} with errors: {}'.format(
                    template_doc['relatedItem'],
                    resource['id'],
                    msg
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "RENDER"},
                    params={
                        "TENDER_ID": resource['id'],
                        "PROFORMA_ID": template_doc['relatedItem']
                    }
                )
            )

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
                "Failed to parse buyer contract data document in {} tender {} in {}. Skipping...".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={
                        "TENDER_ID": resource['id'],
                        'DOCUMENT_ID': data_doc['url'],
                        "PROFORMA_ID": contract_proforma['id']
                    }
                )
            )
            return

        plans = resource.get('plans')
        if not plans:
            logger.error(
                "Error rendering contract proforma. No plan in tender {}({})".format(
                    resource['id'],
                    resource['procurementMethodType'],
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={
                        "TENDER_ID": resource['id'],
                        "PROFORMA_ID": contract_proforma['id']
                    }
                )
            )
            return
        plan = self.get_plan(plans[0].id)['data']

        try:
            schema = self.get_file_json(schema_doc['url'])
        except Exception as e:
            logger.error(
                "Failed to parse schema document in {} tender {} in {}. Skipping...".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={
                        "TENDER_ID": resource['id'],
                        'DOCUMENT_ID': data_doc['url'],
                        "PROFORMA_ID": contract_proforma['id']
                    }
                )
            )
            return
        merger = Merger(schema)
        template = self.get_file(template_doc['url'])

        # document still not rendered
        if contract_proforma['dateModified'] < template_doc['dateModified']\
           and resource['status'] in ('active.tendering', 'active.enquiries'):
            logger.info(
                "Rendering proforma document {} pdf of tender {}({})".format(
                    contract_proforma['id'],
                    resource['id'],
                    resource['procurementMethodType'],
                ),
                extra=journal_context(
                    {"MESSAGE_ID": "PROFORMA"},
                    params={
                        "TENDER_ID": resource['id'],
                        "PROFORMA_ID": contract_proforma['id']
                    }
                )
            )
            proforma_data = merger.merge(
                {'tender': resource},
                {'buyer': buyer_data.get('buyer'), 'role': 'process', 'plan': plan}
            )

            if not self.validate_data(resource, proforma_data, schema):
                logger.warn(
                    "Provided data for rendering is not valid for proforma {} in tender {}({})".format(
                        contract_proforma['id'],
                        resource['id'],
                        resource['procurementMethodType'],
                    ),
                    extra=journal_context(
                        {"MESSAGE_ID": "VALIDATION"},
                        params={
                            "TENDER_ID": resource['id'],
                            "PROFORMA_ID": contract_proforma['id']
                        }
                    )
                )
                return
            self.generate_and_upload_proforma(resource,
                                              template,
                                              template_doc,
                                              proforma_data,
                                              contract_proforma)
        else:
            logger.info(
                "{} tender {} in {} already contains contractProforma.".format(
                    resource['procurementMethodType'],
                    resource['id'],
                    resource['status'],

                ),
                extra=journal_context(
                    {"MESSAGE_ID": "SKIPPED"},
                    params={
                        "TENDER_ID": resource['id'],
                        "PROFORMA_ID": contract_proforma['id']
                    }
                )
            )

        if resource['status'] == 'active.awarded':
            for contract in [c for c in resource.get('contracts') if c['status'] == 'pending']:
                contract_doc = self.get_latest_doc(
                    contract,
                    get_contract_documents,
                    "contract",
                    tender=resource
                )
                buyer_corr_doc = self.get_latest_doc(
                    contract,
                    partial(get_contract_data_documents, related_item=contract_proforma['id']),
                    "contractData",
                    tender=resource
                )
                if contract_doc:
                    # check in contract is up to date
                    if buyer_corr_doc.get('dateModified', '') < contract_doc['dateModified']:
                        logger.info(
                            'Contract {} of tender {} already rendered'.format(contract['id'], resource['id']),
                            extra=journal_context(
                                {"MESSAGE_ID": "SKIPPED"},
                                params={
                                    "TENDER_ID": resource['id'],
                                    "PROFORMA_ID": contract_proforma['id'],
                                    "CONTRACT_ID": contract['id']
                                }
                            )
                        )
                        continue

                award = [a for a in resource.get('awards') if contract['awardID'] == a['id']][-1]
                bid = [b for b in resource.get('bids') if b['id'] == award['bid_id']][-1]

                # {"supplier": {}, "buyer": {}}
                bid_and_supplier_data = self.get_document_content(
                    contract, get_contract_data_documents, as_json=True
                )
                if bid_and_supplier_data:
                    bid_and_supplier_data['role'] = "buyerCorrigenda"
                    if not self.validate_data(resource, bid_and_supplier_data, schema):
                        logger.warn(
                            'BuyerCorrigenda data in tender {} does not satisfy schema'.format(resource['id']),
                            extra=journal_context(
                                {"MESSAGE_ID": "VALIDATION"},
                                params={
                                    "TENDER_ID": resource['id'],
                                    "CONTRACT_ID": contract['id'],
                                    "PROFORMA_ID": contract_proforma['id']
                                }
                            )
                        )
                
                supplier_data = self.get_document_content(bid, get_contract_data_documents, as_json=True)
                if supplier_data:
                    supplier_data['role'] = 'supplier'
                    if not self.validate_data(resource, supplier_data, schema):
                        logger.warn(
                            'Supplier data in tender {} does not satisfy schema'.format(resource['id']),
                            extra=journal_context(
                                {"MESSAGE_ID": "VALIDATION"},
                                params={
                                    "TENDER_ID": resource['id'],
                                    "CONTRACT_ID": contract['id'],
                                    "PROFORMA_ID": contract_proforma['id']
                                }
                            )
                        )
                        supplier_data = {}

                contract_data = {'tender': resource}
                to_merge = [
                    {'plan': plan},
                    {'contract': contract},
                    {'bid': bid},
                    buyer_data,
                    supplier_data,
                    bid_and_supplier_data,
                    bid_and_supplier_data,
                    {'role': 'process'}
                ]
                for data in to_merge:
                    contract_data = merger.merge(contract_data, data)
                if not self.validate_data(resource, contract_data, schema):
                    logger.error(
                        'Contract data in tender {} does not satisfy schema'.format(resource['id']),
                        extra=journal_context(
                            {"MESSAGE_ID": "VALIDATION"},
                            params={
                                "TENDER_ID": resource['id'],
                                "CONTRACT_ID": contract['id'],
                                "PROFORMA_ID": contract_proforma['id']
                            }
                        )
                    )
                    return
                try:
                    if buyer_corr_doc:
                        doc = self.update_contract_document(json.dumps(contract_data),
                                                            resource['id'],
                                                            contract['id'],
                                                            buyer_corr_doc)
                    else:
                        doc = self.upload_contract_document(json.dumps(contract_data),
                                                            resource['id'],
                                                            contract['id'],
                                                            related_item=contract_proforma['id'])
                except Exception as e:
                    logger.error(
                        'Failed to uploaded contractData document to tender {} contract {} with errors: {}'.format(
                            resource['id'],
                            contract['id'],
                            e
                        ),
                        extra=journal_context(
                            {"MESSAGE_ID": "UPLOAD"},
                            params={
                                "TENDER_ID": resource['id'],
                                "CONTRACT_ID": contract['id'],
                                "PROFORMA_ID": contract_proforma['id']
                            }
                        )
                    )
                else:
                    logger.info(
                        'Uploaded contractData document {} to contract {} of tender {}({})'.format(
                            doc.data.id,
                            contract['id'],
                            resource['id'],
                            resource['procurementMethodType']
                        ),
                        extra=journal_context(
                            {"MESSAGE_ID": "UPLOAD"},
                            params={
                                "TENDER_ID": resource['id'],
                                "CONTRACT_ID": contract['id'],
                                "PROFORMA_ID": contract_proforma['id']
                            }
                        )
                    )
                title = template_doc['title']
                if not title.endswith('docx'):
                    title = '{}.docx'.format(template_doc['title'])
                contract_pdf = self.renderer.render(template,
                                                    contract_data,
                                                    name=title)
                if contract_pdf.status_code == 200:
                    try:
                        result = self.upload_contract_document(
                            contract_pdf.content,
                            resource['id'],
                            contract['id'],
                            related_item=contract_proforma['id'],
                            doc_type='contract',
                            title='contract.pdf'
                        )
                    except Exception as e:
                        logger.error(
                            'Failed to uploaded contract to tender {} with errors: {}'.format(
                                resource['id'],
                                e
                            ),
                            extra=journal_context(
                                {"MESSAGE_ID": "UPLOAD"},
                                params={
                                    "TENDER_ID": resource['id'],
                                    "CONTRACT_ID": contract['id'],
                                    "PROFORMA_ID": contract_proforma['id']
                                }
                            )
                        )
                    else:
                        logger.info(
                            'Uploaded contract document {} for proforma template {} to tender {}({})'.format(
                                result.data.id,
                                contract_proforma['id'],
                                resource['id'],
                                resource['procurementMethodType']
                            ),
                            extra=journal_context(
                                {"MESSAGE_ID": "UPLOAD"},
                                params={
                                    "TENDER_ID": resource['id'],
                                    "CONTRACT_ID": contract['id'],
                                    "PROFORMA_ID": contract_proforma['id']
                                }
                            )
                        )
                else:
                    try:
                        msg = contract_pdf.json()['error']['message']
                    except:
                        msg = contract_pdf.text
                    logger.error(
                        'Failed to render contractProforma document to tender {} with errors: {}'.format(
                            resource['id'],
                            msg
                        ),
                        extra=journal_context(
                            {"MESSAGE_ID": "RENDER"},
                            params={
                                "TENDER_ID": resource['id'],
                                "CONTRACT_ID": contract['id'],
                                "PROFORMA_ID": contract_proforma['id']
                            }
                        )
                    )
                    return
