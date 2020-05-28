from os import path
import json


here = path.dirname(path.realpath(__file__))
datadir = path.join(here, 'data')

TEMPLATE_PATH = path.join(datadir, 'paper0000001.docx')

with open(path.join(datadir, 'tender.json')) as in_file:
    TENDER = json.load(in_file)['data']


with open(path.join(datadir, 'buyer.json')) as in_file:
    BUYER = json.load(in_file)


with open(path.join(datadir, 'supplier.json')) as in_file:
    SUPPLIER = json.load(in_file)


with open(path.join(datadir, 'contractData.json')) as in_file:
    CONTRACT_DATA = json.load(in_file)
