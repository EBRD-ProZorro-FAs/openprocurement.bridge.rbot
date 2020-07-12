import pytest
from openprocurement.bridge.rbot.utils import (
    get_contract_data_documents,
    get_contract_schema_documents,
    get_contract_proforma_documents,
    get_contract_template_documents,
    # prepare_proforma_data,
)
from openprocurement.bridge.rbot.tests.data import TENDER


@pytest.mark.parametrize(
    "doc_type,getter", [
        ("contractTemplate", get_contract_template_documents),
        ("contractData", get_contract_data_documents),
        ("contractSchema", get_contract_schema_documents),
    ])
def test_getters(doc_type, getter):
    doc = getter(TENDER)
    assert doc[-1]['documentType'] == doc_type
    proforma = get_contract_proforma_documents(TENDER)
    doc = getter(TENDER, related_item=proforma[-1]['id'])
    assert doc[-1]['documentType'] == doc_type
