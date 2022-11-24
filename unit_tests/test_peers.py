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

import charms_openstack.test_utils as test_utils
from unittest import mock
import peers


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = []
        hook_set = {
            "when": {
                "joined": (
                    "endpoint.{endpoint_name}.joined",),

                "changed": (
                    "endpoint.{endpoint_name}.changed",),
                "departed": ("endpoint.{endpoint_name}.departed",),

                "broken": ("endpoint.{endpoint_name}.broken",),
            },
        }
        # test that the hooks were registered
        self.registered_hooks_test_helper(peers, hook_set, defaults)


class TestVaultPeer(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self._patches = {}
        self._patches_start = {}
        self.patch_object(peers.reactive, "clear_flag")
        self.patch_object(peers.reactive, "set_flag")

        _data = {}
        self.fake_unit_0 = mock.MagicMock()
        self.fake_unit_0.unit_name = "unit/0"
        self.fake_unit_0.received = _data

        self.fake_unit_1 = mock.MagicMock()
        self.fake_unit_1.unit_name = "unit/1"
        self.fake_unit_1.received = _data

        self.fake_unit_2 = mock.MagicMock()
        self.fake_unit_2.unit_name = "unit/2"
        self.fake_unit_2.received = _data

        self.fake_relation_id = "cluster:19"
        self.fake_relation = mock.MagicMock()
        self.fake_relation.relation_id = self.fake_relation_id
        self.fake_relation.units = [
            self.fake_unit_0,
            self.fake_unit_1,
            self.fake_unit_2]
        self.fake_unit_0.relation = self.fake_relation
        self.fake_unit_1.relation = self.fake_relation
        self.fake_unit_2.relation = self.fake_relation

        self.ep_name = "ep"
        self.ep = peers.VaultPeer(
            self.ep_name, [self.fake_relation])
        self.ep.relations[0] = self.fake_relation

    def tearDown(self):
        self.ep = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def test_joined(self):
        self.ep.joined()
        self.set_flag.assert_has_calls([
            mock.call("{}.connected".format(self.ep_name)),
            mock.call("{}.available".format(self.ep_name)),
        ], any_order=True)

    def test_departed(self):
        self.ep.departed()
        _calls = [
            mock.call("{}.available".format(self.ep_name)),
            mock.call("{}.connected".format(self.ep_name))]
        self.clear_flag.assert_has_calls(_calls, any_order=True)

    def test_relation_ids(self):
        self.assertEqual([self.fake_relation_id], self.ep.relation_ids())

    def test__get_data(self):
        self.fake_relation.received_app_raw = {
            "key": '{"get":"cert"}'
        }
        result = self.ep._get_data("key")
        self.assertEqual({'get': 'cert'}, result)

        self.fake_relation.received_app_raw = {"key": None}
        result = self.ep._get_data("key")
        self.assertEqual({}, result)

        self.fake_relation.received_app_raw = {}
        result = self.ep._get_data("key")
        self.assertEqual({}, result)

        self.fake_relation.received_app_raw = None
        result = self.ep._get_data("key")
        self.assertEqual({}, result)

        result = self.ep._get_data("key2")
        self.assertEqual({}, result)

    def test__set_data(self):
        data = self.fake_relation.to_publish_app_raw

        self.ep._set_data('key', {'set': 'cert'})
        data.__setitem__.assert_called_once_with(
            "key", '{"set": "cert"}')

        data.reset_mock()
        self.ep._set_data('key', {})
        data.__setitem__.assert_called_once_with("key", None)

        data.reset_mock()
        self.ep._set_data('key', None)
        data.__setitem__.assert_called_once_with("key", None)
