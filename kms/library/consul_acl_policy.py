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
    required: false
    default: exists
  url:
    description:
      - Consul url
    required: false
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

from collections import OrderedDict
from ansible.module_utils.consul import Consul
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

class ConsulACLPolicy(Consul):

    STATES = [ 'exists' ]

    def __init__(self, module):
        super(ConsulACLPolicy, self).__init__(module)
        self.state = string.lower(module.params.get('state', ''))
        self.name = module.params.get('name', '')
        self.rules = module.params.get('rules', '')

    def run_cmd(self):
        self._validate()
        method = getattr(self, '_' + self.state)
        method()

    def _validate(self):
        if not self.state or self.state not in self.STATES:
            self.module.fail_json(msg='State is required and must be one of %r' % self.STATES)

    def _exists(self):
        try:
            response = self._get_policy_by_name(self.name)
            changed = False

            if response:
                if response['Rules'] != self.rules:
                    self.id = response['ID']
                    response = self._update_policy()
                    changed = True
            else:
                response = self._create_policy()
                changed = True

            self.module.exit_json(changed=changed, succeeded=True, policy=response)

        except Exception as e:
            self.module.fail_json(msg="Failed: {}".format(str(e)))

    def _get_policy_by_name(self, name):
        policies = self._get('/v1/acl/policies')
        for p in policies:
            if p['Name'] == self.name:
                return self._get_policy_by_id(p['ID'])

    def _get_policy_by_id(self, id):
        return self._get("/v1/acl/policy/%s" % id)

    def _create_policy(self):
        return self._put('/v1/acl/policy', self._body())

    def _update_policy(self):
        return self._put("/v1/acl/policy/%s" % self.id, self._body())

    def _body(self):
        valid_attrs = {
            "name": "Name",
            "rules": "Rules"
        }
        body = OrderedDict({})
        for attr, name in valid_attrs.iteritems():
            if hasattr(self, attr) and getattr(self, attr):
                body[name] = getattr(self, attr)
        return body

def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(required=False, default='exists'),
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

    consul_acl_policy = ConsulACLPolicy(module)
    consul_acl_policy.run_cmd()

if __name__ == '__main__':
    main()