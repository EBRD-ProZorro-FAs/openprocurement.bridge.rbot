from deepmerge import Merger

data_merger = Merger(
    [
        (list, ["override"]),
        (dict, ["merge"])
    ],
    ["override"],
    ["override"]
)


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


def prepare_proforma_data(resource,
                          buyer_data={},
                          supplier_data={},
                          bid_data={},
                          contract_data={}):
    result = {"tender": "resource"}
    if buyer_data:
        result['buyer'] = buyer_data
    if supplier_data:
        result['supplier'] = buyer_data
    if bid_data:
        result['bid'] = bid_data
    if contract_data:
        result['contract'] = contract_data
    return result


def merge_contract_data(base, *rest):
    result = base
    for additional in rest:
        if additional:
            result = Merger.merge(result, additional)
    return result
