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
module: consul_acl_token
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
  secret_id:
    description:
      - SecretID of token to update
    required: false
  policies:
    description:
      - List of policies that should be applied to the token
    required: false
  token:
    description:
      - Token to use with requests
    required: false

# informational: requirements for nodes
requirements: [ ]
'''

EXAMPLES = '''
- name: Create token with policy by Name
  consul_acl_token:
    policies:
      - Name: mypolicy
    token: master_token

- name: Update token with no change
  consul_acl_token:
    secret_id: token_secret_id
    policies:
      - Name: policy_1_name
      - ID: policy_2_id
    token: master_token
'''

import json
import string

from collections import OrderedDict
from ansible.module_utils.consul import Consul
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six import string_types

class ConsulACLToken(Consul):

    STATES = [ 'exists' ]

    def __init__(self, module):
        super(ConsulACLToken, self).__init__(module)
        self.state = string.lower(module.params.get('state', ''))
        self.secret_id = module.params.get('secret_id', '')
        self.policies = module.params.get('policies', [])

    def run_cmd(self):
        self._validate()
        method = getattr(self, '_' + self.state)
        method()

    def _validate(self):
        if not self.state or self.state not in self.STATES:
            self.module.fail_json(msg='State is required and must be one of %r' % self.STATES)

    def _exists(self):
        try:
            changed = False
            if self.secret_id:
                response = self._get_token(self.secret_id)
                if response and self._needs_update(response['Policies']):
                    response = self._update_token(response['AccessorID'])
                    changed = True
            else:
                response = self._create_token()
                changed = True
            self.module.exit_json(changed=changed, succeeded=True, token=response)

        except Exception as e:
            self.module.fail_json(msg="Failed: {}".format(str(e)))

    def _get_token(self, id):
        return self._get('/v1/acl/token/self', id)

    def _create_token(self):
        return self._put('/v1/acl/token', self._body())

    def _update_token(self, accessor_id):
        return self._put("/v1/acl/token/%s" % accessor_id, self._body())

    def _needs_update(self, policies):
        policies = policies if policies is not None else []

        if len(self.policies) != len(policies):
            return True

        self_names = [x['Name'] for x in self.policies if 'Name' in x]
        policies_names = [x['Name'] for x in policies if 'Name' in x]
        if len([x for x in self_names if x not in policies_names]) > 0:
            return True

        self_ids = [x['ID'] for x in self.policies if 'ID' in x]
        policies_ids = [x['ID'] for x in policies if 'ID' in x]
        if len([x for x in self_ids if x not in policies_ids]) > 0:
            return True

        return False

    def _body(self):
        valid_attrs = {
            "policies": "Policies"
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
            state=dict(required=False, default='exists'),
            url=dict(require=False, default='http://127.0.0.1:8500'),
            secret_id=dict(required=False, default=''),
            policies=dict(required=False, type='raw', default=[]),
            token=dict(required=False, default=''),
            validate_certs=dict(required=False, default=True)
        ),
        supports_check_mode=True
    )

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=False)

    consul_acl_token = ConsulACLToken(module)
    consul_acl_token.run_cmd()

if __name__ == '__main__':
    main()