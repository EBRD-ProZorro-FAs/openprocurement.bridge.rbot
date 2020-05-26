import json
import os

PWD = os.path.dirname(os.path.realpath(__file__))


class AdaptiveCache(object):

    def __init__(self, data):
        self.data = data

    def get(self, key):
        return self.data.get(key, '')

    def put(self, key, value):
        self.data[key] = value

    def has(self, key):
        return key in self.data

    def __getitem__(self, item):
        return self.data[item]

    def __contains__(self, item):
        return item in self.data


with open(PWD + '/data/tender.json', 'r') as json_file:
    TEST_TENDER = json.load(json_file)

with open(PWD + '/data/profile.v.old.json') as json_file:
    TEST_PROFILE = json.load(json_file)

with open(PWD + '/data/category.v.old.json') as json_file:
    TEST_CATEGORY = json.load(json_file)
