#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: consul_acl_policy
version_added: "1.9"
author: MA
short_description: Interact with Consul ACL policy API
description:
   - Use Consul ACL policy API in your playbooks and roles
options:
  state:
    description:
      - One of [exists]
    required: true
  url:
    description:
      - Consul url
    required: true
    default: http://127.0.0.1:8500
  name:
    description:
      - Name of ACL policy
    required: true
  rules:
    description:
      - Policy rules to set or update
    required: false
  token:
    description:
      - Token to use with requests
    required: false

# informational: requirements for nodes
requirements: [ ]
'''

EXAMPLES = '''
- name: Create ACL policy
  consul_acl_policy:
    state: exists
    name: my_policy
    rules: "node_prefix \"\" { policy = \"write\" } service_prefix \"\" { policy = \"read\" }"
    token: master_token
'''

import json
import string
import urllib

from collections import OrderedDict
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

class ConsulACL(object):

    STATES = [ 'exists' ]

    def __init__(self, module):
        """Takes an AnsibleModule object to set up Consul Event interaction"""
        self.module = module
        self.state = string.lower(module.params.get('state', ''))
        self.url = module.params.get('url', 'http://127.0.0.1:8500')
        self.name = module.params.get('name', '')
        self.rules = module.params.get('rules', '')
        self.token = module.params.get('token', '')
        self.params = OrderedDict({})
        self.req_data = ''

    def run_cmd(self):
        self.validate()
        method = getattr(self, '_' + self.state)
        method()

    def validate(self):
        if not self.state or self.state not in self.STATES:
            self.module.fail_json(msg='State is required and must be one of %r' % self.STATES)

    def _exists(self):
        try:
            policy = self._get_policy_by_name(self.name)

            if policy:
                if policy['Rules'] == self.rules:
                    self.module.exit_json(changed=False, succeeded=True, msg="Policy {} already exists".format(self.name))
                self.id = policy['ID']
                self._update_policy()
            else:
                self._create_policy()

        except Exception as e:
            self.module.fail_json(msg="Failed: {}".format(str(e)))

    def _get_policy_by_name(self, name):
        url = "%s/v1/acl/policies" % (self.url)
        headers = { 'X-Consul-Token': self.token }

        (response, info) = fetch_url(module, url, headers=headers, method='GET')

        if not response:
            raise Exception(info)

        policies = json.loads(response.read())
        for p in policies:
            if p['Name'] == self.name:
                return self._get_policy_by_id(p['ID'])

    def _get_policy_by_id(self, id):
        url = "%s/v1/acl/policy/%s" % (self.url, id)
        headers = { 'X-Consul-Token': self.token }

        (response, info) = fetch_url(module, url, headers=headers, method='GET')
        return json.loads(response.read())

    def _create_policy(self):
        url = "%s/v1/acl/policy" % (self.url)
        body = self._body()
        headers = { 'X-Consul-Token': self.token }

        (response, info) = fetch_url(module, url, data=json.dumps(body), headers=headers, method='PUT')
        self._handle_response(response, info)

    def _update_policy(self):
        url = "%s/v1/acl/policy/%s" % (self.url, self.id)
        body = self._body()
        headers = { 'X-Consul-Token': self.token }

        (response, info) = fetch_url(module, url, data=json.dumps(body), headers=headers, method='PUT')
        self._handle_response(response, info)

    def _body(self):
        valid_attrs = {
            "name": "Name",
            "rules": "Rules"
        }
        params = OrderedDict({})
        for attr, name in valid_attrs.iteritems():
            if hasattr(self, attr) and getattr(self, attr):
                params[name] = getattr(self, attr)
        return params

    def _handle_response(self, response, info):
        code = info['status']
        if code != 200:
            self.module.fail_json(msg="Failed with status {}".format(code), value=info)
        else:
            changed = True
            try:
                parsed_response = json.loads(response.read())
            except:
                parsed_response = info
            self.module.exit_json(changed=changed, succeeded=True, status=code, value=parsed_response)

def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True),
            name=dict(required=True, default=''),
            url=dict(require=False, default='http://127.0.0.1:8500'),
            rules=dict(required=False, default=''),
            token=dict(required=False, default=''),
            validate_certs=dict(required=False, default=True)
        ),
        supports_check_mode=True
    )

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=False)

    consul_status = ConsulACL(module)
    consul_status.run_cmd()

if __name__ == '__main__':
    main()