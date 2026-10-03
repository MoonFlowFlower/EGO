"""Zero-cost Luna adapter checks through the existing authenticated HTTP server."""
import json
import unittest
import urllib.error
from email.message import Message

from . import test_routing
from .luna import MODEL, ROUTE, LunaTransport
from .proxy import ProxyServer, UPSTREAM
from .test_proxy import FAKE_KEY, FakeResponse, FakeUpstream, encode


class LunaFake(FakeUpstream):
    def __init__(self, mode="json"):
        super().__init__(mode=mode, endpoints=[{
            "model_id": MODEL, "tag": ROUTE,
            "pricing": {"prompt": "0.0000001", "completion": "0.0000005"},
            "supported_parameters": ["max_completion_tokens", "reasoning_effort", "response_format", "tools", "tool_choice"],
        }])
        self.output.update(model=MODEL, provider="Azure")


class LunaTests(unittest.TestCase):
    setUp = test_routing.RoutingTests.setUp
    tearDown = test_routing.RoutingTests.tearDown
    request = test_routing.RoutingTests.request
    rows = test_routing.RoutingTests.rows

    def server(self, fake=None, **kwargs):
        fake = fake or LunaFake()
        transport = LunaTransport(api_key=FAKE_KEY, budget_path=self.path / "ledger.sqlite", log_dir=self.path,
                                  _opener=fake, **kwargs)
        server = ProxyServer(transport, log_dir=self.path).start()
        self.servers.append(server)
        return server, fake

    @staticmethod
    def prompt(**values):
        return {"model": MODEL, "messages": [{"role": "user", "content": "你好"}], **values}

    def test_parameter_mapping_and_messages_preserved_through_http(self):
        server, fake = self.server()
        payload = self.prompt(max_tokens=1024, reasoning={"enabled": False},
                              tools=[{"type": "function", "function": {"name": "echo"}}], tool_choice="auto")
        before = encode(payload)
        status, _, body = self.request(server, payload)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["model"], MODEL)
        sent = fake.requests[0]
        self.assertEqual(sent["max_completion_tokens"], 1024)
        self.assertEqual(sent["reasoning_effort"], "none")
        self.assertFalse({"max_tokens", "reasoning", "temperature"} & set(sent))
        self.assertEqual(encode(payload), before)
        for key in ["messages", "tools", "tool_choice"]:
            self.assertEqual(sent[key], payload[key])
        self.assertEqual(sent["provider"]["only"], ["azure"])
        self.assertTrue(sent["provider"]["zdr"])
        self.assertFalse(sent["provider"]["allow_fallbacks"])
        self.assertEqual(self.rows(server), [(.001, "reported")])

    def test_temperature_reasoning_overrides_and_output_limits_fail_before_spend(self):
        server, fake = self.server()
        bad = [self.prompt(temperature=0), self.prompt(reasoning_effort="high"), self.prompt(reasoning={"enabled": True}),
               self.prompt(reasoning={"enabled": False}, reasoning_effort="none"), self.prompt(max_completion_tokens=2049),
               self.prompt(max_tokens=512, max_completion_tokens=512), self.prompt(provider={"zdr": False})]
        for payload in bad:
            self.assertEqual(self.request(server, payload)[0], 400)
        self.assertEqual(fake.requests, [])
        self.assertEqual(fake.preflights, 0)
        self.assertEqual(self.rows(server), [])

    def test_unlisted_or_price_rejected_endpoint_has_no_completion(self):
        server, fake = self.server()
        for endpoints in [[], [{**fake.endpoints[0], "pricing": {"prompt": "0.1", "completion": "0.5"}}]]:
            fake.endpoints = endpoints
            server.transport._metadata = None
            self.assertEqual(self.request(server, self.prompt())[0], 503)
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])

    def test_shared_budget_rejects_before_completion(self):
        server, fake = self.server(limit=.01)
        self.assertEqual(self.request(server, self.prompt())[0], 402)
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])

    def test_429_retains_reserve_and_whitelists_classification(self):
        fake = LunaFake()
        def opener(request, timeout):
            if request.full_url.endswith("/endpoints/zdr"):
                return fake(request, timeout)
            fake.requests.append(json.loads(request.data))
            headers = Message()
            headers['Retry-After'] = '30'
            body = {"error": {"message": FAKE_KEY, "metadata": {"provider_code": 429, "error_type": "rate_limit_exceeded", "raw": FAKE_KEY}}}
            raise urllib.error.HTTPError(UPSTREAM + '/chat/completions', 429, FAKE_KEY, headers, FakeResponse(encode(body)))
        server, _ = self.server()
        server.transport._open = opener
        status, _, body = self.request(server, self.prompt())
        self.assertEqual(status, 429)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(self.rows(server)[0][1], 'reserved_unknown')
        records = [json.loads(line) for line in (self.path/'routing.jsonl').read_text().splitlines()]
        error = next(r for r in records if r['outcome']=='http_error')
        self.assertEqual(error['provider_code'], 429)
        self.assertEqual(error['rate_origin_evidence'], 'provider_code')
        self.assertEqual(error['retry_after_s'], 30)
        for path in self.path.glob('*.jsonl'):
            self.assertNotIn(FAKE_KEY, path.read_text())
            self.assertNotIn(server.token, path.read_text())
        self.assertNotIn(FAKE_KEY.encode(), body)

    def test_stream_accounting_and_partial_stream_no_replay(self):
        server, fake = self.server(LunaFake(mode="stream"))
        status, _, body = self.request(server, self.prompt(stream=True, max_completion_tokens=512))
        self.assertEqual(status, 200)
        self.assertIn(b'data: [DONE]', body)
        self.assertEqual(self.rows(server), [(.001, 'reported')])
        fake.mode = 'stream_error'
        status, _, body = self.request(server, self.prompt(stream=True))
        self.assertEqual(status, 200)
        self.assertIn(b'upstream_stream_error', body)
        self.assertEqual(len(fake.requests), 2)


if __name__ == '__main__':
    unittest.main()
