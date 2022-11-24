# Copyright 2022 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from charms import reactive
import charmhelpers.core as ch_core


class VaultPeer(reactive.Endpoint):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def relation_ids(self):
        return [x.relation_id for x in self.relations]

    @property
    def peer_relation(self):
        # Get the first relation object as we only have one relation to peers
        for relation in self.relations:
            return relation

    @reactive.when('endpoint.{endpoint_name}.joined')
    def joined(self):
        reactive.set_flag(self.expand_name('{endpoint_name}.connected'))
        reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    @reactive.when('endpoint.{endpoint_name}.changed')
    def changed(self):
        reactive.set_flag(self.expand_name('{endpoint_name}.clustered'))

    def remove(self):
        flags = (
            self.expand_name('{endpoint_name}.connected'),
            self.expand_name('{endpoint_name}.available'),
        )
        for flag in flags:
            reactive.clear_flag(flag)

    @reactive.when('endpoint.{endpoint_name}.departed')
    def departed(self):
        self.remove()

    @reactive.when('endpoint.{endpoint_name}.broken')
    def broken(self):
        self.remove()

    def _get_data(self, key):
        result = '{}'
        if not self.peer_relation:
            ch_core.hookenv.log(
                "No vault peer relation: possibly departing.", "WARNING")
            return
        try:
            result = self.peer_relation.received_app_raw.get(key) or '{}'
        except AttributeError as e:
            ch_core.hookenv.log(
                "Retrieving key {} from vault-ha application "
                "databag caused error: {}".format(key, e), "WARNING")
            pass
        return json.loads(result)

    def _set_data(self, key, value):
        if not self.peer_relation:
            ch_core.hookenv.log(
                "No vault peer relation: possibly departing.", "WARNING")
            return
        data = json.dumps(value) if value else None
        self.peer_relation.to_publish_app_raw[key] = data

    def get_global_client_cert(self):
        return self._get_data('charm.vault.global-client-cert')

    def set_global_client_cert(self, bundle):
        self._set_data('charm.vault.global-client-cert', bundle)

    def get_unit_pki(self, unit_key):
        return self._get_data(unit_key)

    def set_unit_pki(self, unit_key, pki_data):
        self._set_data(unit_key, pki_data)
