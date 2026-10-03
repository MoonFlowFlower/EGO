"""Verify the replacement is used by the HTTP and actual application entries."""
import json
import sys
import unittest
from unittest.mock import patch

from . import active_proxy, launch_proxy, runtime_session, test_routing
from .proxy import ProxyServer
from .routing_v2 import RoutedTransportV2, configuration
from .test_proxy import FAKE_KEY


class V2Tests(unittest.TestCase):
    def test_cross_family_mapping_through_http(self):
        helper = test_routing.RoutingTests("test_real_entry_and_models_use_new_configuration")
        helper.setUp()
        try:
            fake = test_routing.RoutesFake([429, 503])
            fake.endpoints[2].update(model_id=configuration()["routes"][2]["model"], tag=configuration()["routes"][2]["route"])
            transport = RoutedTransportV2(api_key=FAKE_KEY, budget_path=helper.path / "ledger.sqlite", log_dir=helper.path, _opener=fake)
            with ProxyServer(transport, log_dir=helper.path) as server:
                status, _, body = helper.request(server, helper.prompt(server))
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)["model"], "google/gemini-3.1-flash-lite")
                self.assertEqual(fake.requests[-1]["provider"]["only"], ["google-vertex/eu"])
                self.assertEqual(server.transport.route, "routing-v2")
        finally:
            helper.tearDown()

    def test_gui_and_private_pipe_entry_select_v2_factory(self):
        for argv, module in [(["active_proxy"], launch_proxy), (["active_proxy", "--private-pipe"], runtime_session)]:
            old_class = module.RoutedTransport
            old_config = getattr(module, "configuration", None)
            try:
                with patch.object(sys, "argv", argv), patch.object(module, "main") as start:
                    active_proxy.main()
                    start.assert_called_once_with()
                    self.assertIs(module.RoutedTransport, RoutedTransportV2)
                    self.assertEqual(module.configuration()["version"], "routing-v2")
            finally:
                module.RoutedTransport = old_class
                if old_config is None:
                    del module.configuration
                else:
                    module.configuration = old_config


if __name__ == "__main__":
    unittest.main()
