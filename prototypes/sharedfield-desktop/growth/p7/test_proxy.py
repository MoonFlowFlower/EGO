"""Zero-cost local HTTP checks. All upstream calls are an in-memory fixture."""
from __future__ import annotations

import concurrent.futures
import contextlib
import hashlib
import http.client
import io
import json
import sqlite3
import threading
import time
import unittest
import urllib.error
import uuid
from email.message import Message
from pathlib import Path

from .proxy import (
    DEFAULT_BUDGET, DEFAULT_LOGS, MODEL, PROVIDER, ROOT, ROUTE, UPSTREAM,
    BudgetLedger, FixedRouteTransport, ProxyError, ProxyServer, prepare_request,
)

FAKE_KEY = "fixture-only-upstream-credential-never-a-real-key"
RUN_DIR = DEFAULT_LOGS / ("offline-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8])
SUPPORTED = {"response_format", "max_tokens", "temperature", "reasoning", "tools", "tool_choice",
             "top_p", "parallel_tool_calls", "stop", "presence_penalty", "frequency_penalty", "seed"}


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


class FakeResponse(io.BytesIO):
    def __init__(self, body, content_type="application/json"):
        super().__init__(body)
        self.headers = Message()
        self.headers["Content-Type"] = content_type


class FakeUpstream:
    def __init__(self, *, mode="json", cost=.001, endpoints=None):
        self.mode, self.cost = mode, cost
        self.requests, self.preflights = [], 0
        self.endpoints = endpoints if endpoints is not None else [{
            "model_id": MODEL, "tag": ROUTE, "pricing": {"prompt": "0.00000025", "completion": "0.00000065"},
            "supported_parameters": sorted(SUPPORTED),
        }]
        self.output = {"id": "fixture-completion", "object": "chat.completion", "created": 0,
                       "model": MODEL, "provider": "Open Inference",
                       "choices": [{"index": 0, "message": {"role": "assistant", "content": "你好"}, "finish_reason": "stop"}],
                       "usage": {"prompt_tokens": 12, "completion_tokens": 3, "cost": cost}}
        self.stream_objects = [
            {"id": "fixture-stream", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {"role": "assistant", "content": "你好"}, "finish_reason": None}]},
            {"id": "fixture-stream", "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "usage": self.output["usage"]},
        ]

    def __call__(self, request, timeout):
        if request.headers.get("Authorization") != "Bearer " + FAKE_KEY:
            raise AssertionError("fixture_credential_not_forwarded")
        if request.full_url == UPSTREAM + "/endpoints/zdr":
            self.preflights += 1
            if self.mode == "preflight_offline":
                raise urllib.error.URLError("fixture failure text must never be written " + FAKE_KEY)
            return FakeResponse(encode({"data": self.endpoints}))
        if request.full_url != UPSTREAM + "/chat/completions":
            raise AssertionError("outbound_url_changed")
        self.requests.append(json.loads(request.data))
        if self.mode == "offline":
            raise urllib.error.URLError("fixture failure text must never be written " + FAKE_KEY)
        if self.mode == "http_error":
            raise urllib.error.HTTPError(request.full_url, 401, FAKE_KEY, Message(), None)
        if self.mode == "malformed":
            return FakeResponse(b"not json " + FAKE_KEY.encode())
        if self.mode in {"stream", "stream_incomplete", "stream_error"}:
            chunks = b": upstream comment\n\n"
            for item in self.stream_objects:
                chunks += b"data: " + encode(item) + b"\n\n"
            if self.mode == "stream_error":
                chunks += b"data: " + encode({"error": {"message": FAKE_KEY}}) + b"\n\n"
            if self.mode != "stream_incomplete":
                chunks += b"data: [DONE]\n\n"
            return FakeResponse(chunks, "text/event-stream")
        return FakeResponse(encode(self.output))


class ProxyTests(unittest.TestCase):
    def setUp(self):
        self.path = RUN_DIR / self._testMethodName
        self.path.mkdir(parents=True, exist_ok=True)
        self.servers = []

    def tearDown(self):
        for server in self.servers:
            server.close()

    def server(self, *, upstream=None, limit=5, name="server", origins=()):
        fake = upstream or FakeUpstream()
        transport = FixedRouteTransport(api_key=FAKE_KEY, budget_path=self.path / (name + ".sqlite"), limit=limit, _opener=fake)
        server = ProxyServer(transport, log_dir=self.path / name, allowed_origins=origins).start()
        self.servers.append(server)
        return server, fake

    def request(self, server, payload=None, *, token=None, method="POST", path="/v1/chat/completions", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.httpd.server_address[1], timeout=5)
        body = None if payload is None else encode(payload)
        request_headers = {"Authorization": "Bearer " + (server.token if token is None else token)}
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})
        try:
            connection.request(method, path, body, request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    @staticmethod
    def prompt(**updates):
        return {"model": MODEL, "messages": [{"role": "user", "content": "说你好"}], **updates}

    def events(self, server):
        return [json.loads(line) for line in (server.audit.path / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def rows(self, server):
        with contextlib.closing(sqlite3.connect(server.transport.ledger.path)) as db:
            return db.execute("SELECT usd,status FROM charges").fetchall()

    def test_loopback_tokens_and_models_are_local(self):
        server, fake = self.server()
        other, _ = self.server(name="other")
        self.assertEqual(server.httpd.server_address[0], "127.0.0.1")
        self.assertNotEqual(server.token, other.token)
        self.assertGreaterEqual(len(server.token), 40)
        status, _, body = self.request(server, method="GET", path="/v1/models")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["data"][0]["id"], MODEL)
        self.assertEqual(fake.preflights, 0)
        self.assertEqual(fake.requests, [])

    def test_bad_and_absent_auth_reject_without_upstream(self):
        server, fake = self.server()
        for token in ("bad-token", ""):
            status, _, body = self.request(server, self.prompt(), token=token)
            self.assertEqual(status, 401)
            self.assertEqual(json.loads(body)["error"]["code"], "unauthorized")
        self.assertEqual(fake.preflights, 0)
        self.assertEqual(fake.requests, [])
        self.assertEqual([e["error_code"] for e in self.events(server) if "error_code" in e], ["unauthorized", "unauthorized"])

    def test_message_and_tool_objects_preserved(self):
        server, fake = self.server()
        payload = self.prompt(
            messages=[{"role": "system", "content": "保持原文"}, {"role": "user", "content": [{"type": "text", "text": "砍树"}]},
                      {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "look", "arguments": "{\"radius\":3}"}}]},
                      {"role": "tool", "tool_call_id": "call_1", "content": "树就在前面"}],
            tools=[{"type": "function", "function": {"name": "look", "description": "Observe", "parameters": {"type": "object", "properties": {"radius": {"type": "integer"}}}}}],
            tool_choice="auto", temperature=.2)
        before = encode(payload)
        status, _, body = self.request(server, payload)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), fake.output)
        self.assertEqual(before, encode(payload))
        for field in ("messages", "tools", "tool_choice", "temperature"):
            self.assertEqual(fake.requests[0][field], payload[field])
        self.assertEqual(fake.requests[0]["provider"], PROVIDER)
        self.assertEqual(fake.requests[0]["model"], MODEL)
        self.assertEqual(self.rows(server), [(.001, "reported")])

    def test_sse_and_tool_call_deltas_preserved(self):
        fake = FakeUpstream(mode="stream")
        fake.stream_objects.insert(1, {"id": "fixture-stream", "choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": "call_2", "type": "function", "function": {"name": "stop", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]})
        server, _ = self.server(upstream=fake)
        status, headers, body = self.request(server, self.prompt(stream=True))
        self.assertEqual(status, 200)
        self.assertIn("text/event-stream", headers["Content-Type"])
        events = [line[6:] for line in body.splitlines() if line.startswith(b"data: ")]
        self.assertEqual(events[-1], b"[DONE]")
        self.assertEqual([json.loads(value) for value in events[:-1]], fake.stream_objects)
        self.assertTrue(fake.requests[0]["stream_options"]["include_usage"])
        self.assertEqual(self.rows(server), [(.001, "reported")])

    def test_budget_rejection_blocks_completion(self):
        server, fake = self.server(limit=.01)
        status, _, body = self.request(server, self.prompt())
        self.assertEqual(status, 402)
        self.assertEqual(json.loads(body)["error"]["code"], "budget_stop")
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])
        self.assertEqual(self.events(server)[-1]["error_code"], "budget_stop")

    def test_atomic_budget_reservations_across_instances(self):
        path = self.path / "shared.sqlite"
        ledgers = [BudgetLedger(path, .11) for _ in range(12)]
        barrier = threading.Barrier(len(ledgers))
        def reserve(ledger):
            barrier.wait(timeout=5)
            try:
                ledger.reserve(.05)
                return "reserved"
            except ProxyError as error:
                return error.code
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(ledgers)) as pool:
            results = list(pool.map(reserve, ledgers))
        self.assertEqual(results.count("reserved"), 2)
        self.assertEqual(results.count("budget_stop"), 10)
        self.assertAlmostEqual(ledgers[0].total(), .1)

    def test_network_failure_keeps_reservation_and_records(self):
        server, fake = self.server(upstream=FakeUpstream(mode="offline"))
        status, _, body = self.request(server, self.prompt())
        self.assertEqual(status, 502)
        self.assertEqual(json.loads(body)["error"]["code"], "upstream_unavailable")
        self.assertEqual(len(fake.requests), 1)
        amount, state = self.rows(server)[0]
        self.assertGreaterEqual(amount, .05)
        self.assertEqual(state, "reserved_unknown")
        event = self.events(server)[-1]
        self.assertEqual(event["error_code"], "upstream_unavailable")
        self.assertEqual(event["reserved_usd"], amount)

    def test_http_error_body_not_forwarded_or_logged(self):
        server, _ = self.server(upstream=FakeUpstream(mode="http_error"))
        status, _, body = self.request(server, self.prompt())
        self.assertEqual(status, 502)
        self.assertNotIn(FAKE_KEY.encode(), body)
        for path in server.audit.path.glob("*.jsonl"):
            self.assertNotIn(FAKE_KEY, path.read_text(encoding="utf-8"))

    def test_route_overrides_and_multimodal_rejected_before_preflight(self):
        server, fake = self.server()
        invalid = [self.prompt(model="some/other-model"), self.prompt(provider={"only": ["elsewhere"]}),
                   self.prompt(plugins=[{"id": "web"}]), self.prompt(base_url="https://example.com"),
                   self.prompt(tools=[{"type": "web_search"}]),
                   self.prompt(messages=[{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "https://example.com/a.png"}}]}]),
                   self.prompt(messages=[{"role": "user", "content": [{"type": "input_audio", "input_audio": {"data": "abc", "format": "wav"}}]}])]
        for payload in invalid:
            self.assertEqual(self.request(server, payload)[0], 400)
        self.assertEqual(fake.preflights, 0)
        self.assertEqual(fake.requests, [])

    def test_preflight_missing_route_and_high_price_reject(self):
        for index, endpoints in enumerate(([], [{"model_id": MODEL, "tag": ROUTE, "pricing": {"prompt": "0.000002", "completion": "0.000001"}, "supported_parameters": sorted(SUPPORTED)}])):
            server, fake = self.server(upstream=FakeUpstream(endpoints=endpoints), name=str(index))
            status, _, body = self.request(server, self.prompt())
            self.assertEqual(status, 503)
            self.assertEqual(json.loads(body)["error"]["code"], "route_preflight_rejected")
            self.assertEqual(fake.requests, [])
            self.assertEqual(self.rows(server), [])

    def test_preflight_network_error_no_completion(self):
        server, fake = self.server(upstream=FakeUpstream(mode="preflight_offline"))
        self.assertEqual(self.request(server, self.prompt())[0], 502)
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])
        self.assertEqual(self.events(server)[-1]["error_code"], "route_preflight_unavailable")

    def test_requested_parameter_support_enforced_before_reserve(self):
        server, fake = self.server()
        self.assertEqual(self.request(server, self.prompt(logprobs=True))[0], 400)
        self.assertEqual(fake.requests, [])
        self.assertEqual(self.rows(server), [])

    def test_unknown_cost_retains_reservation(self):
        fake = FakeUpstream(cost=None)
        server, _ = self.server(upstream=fake)
        self.assertEqual(self.request(server, self.prompt())[0], 200)
        self.assertEqual(self.rows(server)[0][1], "reserved_unknown")
        self.assertGreaterEqual(self.rows(server)[0][0], .05)

    def test_sse_incomplete_is_failed_not_completed(self):
        fake = FakeUpstream(mode="stream_incomplete")
        fake.stream_objects = fake.stream_objects[:1]  # no usage; cost remains unknown
        server, _ = self.server(upstream=fake)
        status, _, body = self.request(server, self.prompt(stream=True))
        self.assertEqual(status, 200)  # SSE headers have already been sent.
        self.assertIn(b"upstream_stream_incomplete", body)
        self.assertEqual(self.rows(server)[0][1], "reserved_unknown")
        self.assertEqual(self.events(server)[-1]["outcome"], "failed")

    def test_sse_error_is_sanitized_and_failed(self):
        server, _ = self.server(upstream=FakeUpstream(mode="stream_error"))
        _, _, body = self.request(server, self.prompt(stream=True))
        self.assertNotIn(FAKE_KEY.encode(), body)
        self.assertIn(b"upstream_stream_error", body)
        self.assertEqual(self.events(server)[-1]["outcome"], "failed")

    def test_secrets_redacted_from_content_and_events(self):
        server, fake = self.server()
        fake.output["choices"][0]["message"]["content"] = "response " + FAKE_KEY + " " + server.token
        payload = self.prompt(messages=[{"role": "user", "content": "request " + FAKE_KEY + " " + server.token}])
        self.assertEqual(self.request(server, payload)[0], 200)
        self.assertEqual(fake.requests[0]["messages"], payload["messages"])
        for path in server.audit.path.glob("*.jsonl"):
            saved = path.read_text(encoding="utf-8")
            self.assertNotIn(FAKE_KEY, saved)
            self.assertNotIn(server.token, saved)
        saved = (server.audit.path / "content.jsonl").read_text(encoding="utf-8")
        self.assertIn("[REDACTED]", saved)

    def test_cors_and_host_validation(self):
        server, fake = self.server(origins={"http://tauri.localhost"})
        status, headers, _ = self.request(server, method="OPTIONS", headers={"Origin": "http://tauri.localhost", "Authorization": ""})
        self.assertEqual(status, 204)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "http://tauri.localhost")
        self.assertEqual(self.request(server, self.prompt(), headers={"Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.request(server, self.prompt(), headers={"Host": "example.com"})[0], 403)
        self.assertEqual(fake.requests, [])

    def test_limits_and_nonfinite_input_reject(self):
        server, fake = self.server()
        for payload in (self.prompt(n=2), self.prompt(max_tokens=2049), self.prompt(max_tokens=True),
                        self.prompt(max_tokens=8193, reasoning={"enabled": True}),
                        self.prompt(messages=[{"role": "user", "content": "x" * 60_000}]), self.prompt(temperature=float("nan"))):
            self.assertIn(self.request(server, payload)[0], {400, 413})
        self.assertEqual(fake.requests, [])

    def test_default_phase1_ledger_and_cap(self):
        self.assertEqual(DEFAULT_BUDGET, ROOT / "runs/phase1/budget.sqlite")
        with self.assertRaisesRegex(ValueError, "budget_limit"):
            BudgetLedger(self.path / "over-limit.sqlite", 5.01)
        payload, raw, reserve = prepare_request(self.prompt(max_completion_tokens=100))
        self.assertEqual(payload["max_tokens"], 100)
        self.assertNotIn("max_completion_tokens", payload)
        self.assertEqual(reserve, max(.05, (len(raw) + 2048) * .000001 + 100 * .000002))


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"test": test._testMethodName, "status": "passed"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"test": test._testMethodName, "status": "failed"})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"test": test._testMethodName, "status": "error"})


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    files = ("proxy.py", "test_proxy.py", "launch_proxy.py")
    hashes = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in files}
    criteria = (ROOT / "evidence/p7/PROXY.md").read_text(encoding="utf-8").split("## 实现与接口")[0]
    started = time.time()
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProxyTests))
    report = {"kind": "p7_proxy_offline_engineering", "unix_s": started, "duration_s": time.time() - started,
              "actual_cloud_calls": 0, "actual_cloud_cost_usd": 0, "upstream": "in_memory_fixture",
              "airi_ping": "NOT_RUN", "physical_network_disconnect": "NOT_RUN", "model": MODEL, "route": ROUTE,
              "criteria_sha256": hashlib.sha256(criteria.encode()).hexdigest(), "source_sha256": hashes,
              "passed": result.wasSuccessful(), "tests_run": result.testsRun, "results": result.records,
              "raw_run_dir": str(RUN_DIR.relative_to(ROOT)), "limitations": ["Fake upstream does not establish live route or AIRI compatibility.", "Network failure is simulated, not a physical disconnection.", "No generated code is executed."]}
    (RUN_DIR / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Offline evidence:", RUN_DIR / "result.json")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
