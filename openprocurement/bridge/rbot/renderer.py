# -*- coding: utf-8 -*-
import requests
import json
from io import BytesIO
from StringIO import StringIO


class HttpRenderer(object):

    def __init__(self, url):
        self.session = requests.Session()
        self.base_url = url

    def render(self, template, json_data, name=None):
        data = {
            'json_data': json.dumps(json_data),
            'include_attachments': 'true'
        }
        if name:
            return self.session.post(self.base_url,
                                     data=data,
                                     files={'template': (name, template)})
        return self.session.post(
            self.base_url,
            data=data,
            files={'template': template}
        )
