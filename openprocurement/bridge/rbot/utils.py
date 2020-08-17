def _get_documents(resource, doc_type, related_item=None):
    if related_item:
        return [
            doc for doc in resource.get('documents', [])
            if doc.get('documentType') == doc_type and
            doc.get('relatedItem') == related_item
        ]
    return [
        doc for doc in resource.get('documents', [])
        if doc.get('documentType') == doc_type
    ]


def get_contract_data_documents(resource, related_item=None):
    return _get_documents(resource, 'contractData', related_item=related_item)


def get_contract_schema_documents(resource, related_item=None):
    return _get_documents(resource,
                          "contractSchema",
                          related_item=related_item)


def get_contract_template_documents(resouce, related_item=None):
    return _get_documents(resouce,
                          "contractTemplate",
                          related_item=related_item)


def get_contract_proforma_documents(resource, related_item=None):
    return _get_documents(resource, 'contractProforma', related_item=None)


def get_contract_documents(resource, related_item=None):
    return _get_documents(resource, 'contract', related_item=None)


def prepare_title(doc):
    title = doc['title']
    if not title.endswith('docx'):
        title = '{}.docx'.format(title)
    return title
