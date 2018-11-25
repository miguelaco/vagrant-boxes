# -*- coding: utf-8 -*-

# Copyright 2018 MA <ma@somewhere-cool.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json

from ansible.module_utils.urls import fetch_url

class Consul(object):

    def __init__(self, module):
        self.module = module
        self.url = module.params.get('url', 'http://127.0.0.1:8500')
        self.token = module.params.get('token', '')

    def _do(self, path, body=None, method='GET', token=None):
        url = self.url + path
        token = token if token else self.token
        headers = { 'X-Consul-Token': token }

        response, info = fetch_url(self.module, url, data=json.dumps(body), headers=headers, method=method)

        if info['status'] != 200 or not response:
            raise Exception(info)
        return json.loads(response.read())

    def _get(self, path, token=None):
        return self._do(path=path, token=token)

    def _put(self, path, body=None, token=None):
        return self._do(path=path, body=body, method='PUT', token=token)

    def _post(self, path, body=None, token=None):
        return self._do(path=path, body=body, method='POST', token=token)