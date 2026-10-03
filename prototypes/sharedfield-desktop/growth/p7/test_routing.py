"""Availability and accounting checks through the real loopback HTTP handler."""
import copy
import json
import sqlite3
import time
import unittest
import urllib.error
import uuid
from email.message import Message

from .proxy import DEFAULT_LOGS, ProxyServer, UPSTREAM
from .routing import RoutedTransport, configuration, retry_after_seconds
from . import test_proxy
from .test_proxy import FAKE_KEY, SUPPORTED, FakeResponse, encode


class RoutesFake:
    def __init__(self, errors=(), *, stream_error=False):
        self.errors = list(errors)
        self.requests, self.preflights = [], 0
        self.stream_error = stream_error
        self.endpoints = [{"model_id": r["model"], "tag": r["route"],
                           "pricing": {"prompt": "0.0000003", "completion": "0.0000012"},
                           "supported_parameters": sorted(SUPPORTED)} for r in configuration()["routes"]]

    def __call__(self, request, timeout):
        assert request.headers["Authorization"] == "Bearer " + FAKE_KEY
        if request.full_url == UPSTREAM + "/endpoints/zdr":
            self.preflights += 1
            if self.endpoints is None:
                raise urllib.error.URLError(FAKE_KEY)
            return FakeResponse(encode({"data": self.endpoints}))
        assert request.full_url == UPSTREAM + "/chat/completions"
        payload = json.loads(request.data)
        self.requests.append(payload)
        error = self.errors.pop(0) if self.errors else None
        if isinstance(error, Exception):
            raise error
        if error:
            headers = Message()
            headers["Retry-After"] = "120"
            raise urllib.error.HTTPError(request.full_url, error, FAKE_KEY, headers, FakeResponse(FAKE_KEY.encode()))
        result = {"id": "fixture", "model": payload["model"], "provider": payload["provider"]["only"][0],
                  "choices": [{"message": {"role": "assistant", "content": "收到"}, "finish_reason": "stop"}],
                  "usage": {"cost": .001, "prompt_tokens": 10, "completion_tokens": 2}}
        if self.stream_error:
            return FakeResponse(b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
                                + encode({"error": {"message": FAKE_KEY}}).join([b'data: ', b'\n\n']), "text/event-stream")
        return FakeResponse(encode(result))


class RoutingTests(unittest.TestCase):
    request = test_proxy.ProxyTests.request
    events = test_proxy.ProxyTests.events
    rows = test_proxy.ProxyTests.rows

    def setUp(self):
        self.path = DEFAULT_LOGS / ("routing-offline-" + uuid.uuid4().hex) / self._testMethodName
        self.path.mkdir(parents=True)
        self.servers = []

    def tearDown(self):
        for server in self.servers:
            server.close()

    def server(self, fake=None, **kwargs):
        fake = fake or RoutesFake()
        transport = RoutedTransport(api_key=FAKE_KEY, budget_path=self.path / "ledger.sqlite",
                                    log_dir=self.path, _opener=fake, **kwargs)
        server = ProxyServer(transport, log_dir=self.path).start()
        self.servers.append(server)
        return server, fake

    @staticmethod
    def prompt(server, **updates):
        return {"model": server.transport.model, "messages": [{"role": "user", "content": "收到"}], **updates}

    def routing_events(self):
        path = self.path / "routing.jsonl"
        return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []

    def test_real_entry_and_models_use_new_configuration(self):
        server, fake = self.server()
        status, _, body = self.request(server, method="GET", path="/v1/models")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["data"][0]["id"], "ego-companion")
        status, _, body = self.request(server, self.prompt(server))
        self.assertEqual(status, 200)
        self.assertEqual(fake.requests[0]["model"], configuration()["routes"][0]["model"])
        self.assertEqual(json.loads(body)["provider"], "wafer")

    def test_429_then_503_uses_cross_family_and_retains_unknown_costs(self):
        server, fake = self.server(RoutesFake([429, 503]))
        original = self.prompt(server, tools=[{"type": "function", "function": {"name": "echo"}}])
        status, _, body = self.request(server, original)
        self.assertEqual(status, 200)
        self.assertEqual([p["provider"]["only"][0] for p in fake.requests], ["wafer", "together", "baseten/fp8"])
        self.assertEqual(json.loads(body)["model"], "z-ai/glm-5.3-flash")
        self.assertEqual([row[1] for row in self.rows(server)], ["reserved_unknown", "reserved_unknown", "reported"])
        self.assertAlmostEqual(server.transport.ledger.total(), .101)
        for payload in fake.requests:
            self.assertEqual(payload["messages"], original["messages"])
            self.assertEqual(payload["tools"], original["tools"])
            self.assertEqual(payload["provider"], {**configuration()["policy"]["provider"], "only": payload["provider"]["only"]})
        evidence = "".join(p.read_text() for p in self.path.glob("*.jsonl"))
        self.assertNotIn(FAKE_KEY, evidence)
        self.assertNotIn(server.token, evidence)
        self.assertEqual(self.events(server)[-1]["requested_providers"], ["baseten/fp8"])

    def test_404_falls_back_same_model(self):
        server, fake = self.server(RoutesFake([404]))
        status, _, _ = self.request(server, self.prompt(server))
        self.assertEqual(status, 200)
        self.assertEqual(len(fake.requests), 2)
        self.assertEqual(fake.requests[0]["model"], fake.requests[1]["model"])

    def test_non_availability_errors_never_fallback(self):
        server, fake = self.server()
        for error in [400, 401, 402, 403, 422]:
            with self.subTest(error=error):
                fake.errors = [error]
                previous = len(fake.requests)
                status, _, body = self.request(server, self.prompt(server))
                self.assertEqual(status, error)
                self.assertEqual(len(fake.requests), previous + 1)
                self.assertNotIn(FAKE_KEY.encode(), body)

    def test_connection_timeout_can_use_backup(self):
        server, fake = self.server(RoutesFake([TimeoutError(FAKE_KEY)]))
        self.assertEqual(self.request(server, self.prompt(server))[0], 200)
        self.assertEqual(len(fake.requests), 2)

    def test_retry_after_cooldown_applies_to_later_requests(self):
        clock = [1000.0]
        server, fake = self.server(RoutesFake([429]), _clock=lambda: clock[0])
        self.assertEqual(self.request(server, self.prompt(server))[0], 200)
        clock[0] += 31
        self.assertEqual(self.request(server, self.prompt(server))[0], 200)
        self.assertEqual(fake.requests[-1]["provider"]["only"], ["together"])
        clock[0] += 90
        self.assertEqual(self.request(server, self.prompt(server))[0], 200)
        self.assertEqual(fake.requests[-1]["provider"]["only"], ["wafer"])

    def test_pinned_failure_is_one_attempt(self):
        server, fake = self.server(RoutesFake([429]), mode="pinned", route_index=1)
        self.assertEqual(self.request(server, self.prompt(server))[0], 429)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(fake.requests[0]["provider"]["only"], ["together"])

    def test_fresh_metadata_required_after_ttl_and_missing_route_skipped(self):
        clock = [1000.0]
        server, fake = self.server(_clock=lambda: clock[0])
        fake.endpoints.pop(0)
        self.assertEqual(self.request(server, self.prompt(server))[0], 200)
        self.assertEqual(fake.requests[-1]["provider"]["only"], ["together"])
        fake.endpoints = None
        clock[0] += 61
        self.assertEqual(self.request(server, self.prompt(server))[0], 502)
        self.assertEqual(len(fake.requests), 1)

    def test_unlisted_all_price_parameters_budget_and_user_override_fail_closed(self):
        server, fake = self.server()
        original = copy.deepcopy(fake.endpoints)
        variants = [[], [{**original[0], "pricing": {"prompt": "1", "completion": "1"}}, *original[1:]],
                    [{**original[0], "supported_parameters": []}, *original[1:]]]
        for endpoints in variants:
            fake.endpoints = endpoints
            server.transport._metadata = None
            self.assertIn(self.request(server, self.prompt(server))[0], [400, 503])
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])
        fake.endpoints = original
        server.transport._metadata = None
        self.assertEqual(self.request(server, self.prompt(server, provider={"zdr": False}))[0], 400)
        server.transport.ledger.reserve(5)
        self.assertEqual(self.request(server, self.prompt(server))[0], 402)
        self.assertEqual(fake.requests, [])

    def test_three_failures_bound_attempts_and_leave_all_reserves(self):
        server, fake = self.server(RoutesFake([502, 503, 504, 429]))
        self.assertEqual(self.request(server, self.prompt(server))[0], 504)
        self.assertEqual(len(fake.requests), 3)
        self.assertAlmostEqual(server.transport.ledger.total(), .15)
        self.assertEqual(self.request(server, self.prompt(server))[0], 503)
        self.assertEqual(len(fake.requests), 3)

    def test_partial_stream_error_never_retries(self):
        server, fake = self.server(RoutesFake(stream_error=True))
        status, _, body = self.request(server, self.prompt(server, stream=True))
        self.assertEqual(status, 200)
        self.assertIn(b"partial", body)
        self.assertIn(b"upstream_stream_error", body)
        self.assertNotIn(FAKE_KEY.encode(), body)
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(self.rows(server)[0][1], "reserved_unknown")

    def test_retry_header_accepts_seconds_and_http_date_only(self):
        self.assertEqual(retry_after_seconds("120", 0), 120)
        self.assertEqual(retry_after_seconds("Thu, 01 Jan 1970 00:02:00 GMT", 0), 120)
        for bad in [None, "nan", "inf", "-3", FAKE_KEY]:
            self.assertEqual(retry_after_seconds(bad, 0), 0)


if __name__ == "__main__":
    unittest.main()
