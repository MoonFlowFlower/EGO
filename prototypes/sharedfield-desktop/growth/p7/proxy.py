"""Loopback-only Chat Completions bridge with the P2 route and budget policy.

Secrets are injected in memory. No read_key(), CLI secret, body echo on failure,
environment HTTP proxy, remote redirect, model fallback, or code execution.
"""
from __future__ import annotations

import copy
import hmac
import json
import math
import re
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from growthlab.models import MODEL, ROUTE

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUDGET = ROOT / "runs/phase1/budget.sqlite"
DEFAULT_LOGS = ROOT / "runs/p7/proxy"
UPSTREAM = "https://openrouter.ai/api/v1"
MAX_REQUEST_BYTES = 60_000
MAX_RESPONSE_BYTES = 4_000_000
DEFAULT_ORIGINS = frozenset({"http://tauri.localhost", "tauri://localhost", "app://localhost"})
PROVIDER = {
    "only": [ROUTE], "allow_fallbacks": False, "data_collection": "deny",
    "zdr": True, "require_parameters": True,
    "max_price": {"prompt": 1, "completion": 2},
}


class ProxyError(Exception):
    """Only fixed, non-sensitive error codes cross this boundary."""

    def __init__(self, code, status=400, *, charge_id=None, reserved_usd=None):
        super().__init__(code)
        self.code, self.status = code, status
        self.charge_id, self.reserved_usd = charge_id, reserved_usd


def before_forward(request):
    """U1 insertion point. P7 is an identity function."""
    return request


def after_forward(response):
    """U1 insertion point. P7 is an identity function, including SSE chunks."""
    return response


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _finite_number(value):
    return not isinstance(value, bool) and isinstance(value, (float, int)) and math.isfinite(value)


def _reject_constant(_value):
    raise ValueError("non_finite_json")


def _parse_json(raw):
    return json.loads(raw, parse_constant=_reject_constant)


def _validate_function(function):
    if not isinstance(function, dict) or not isinstance(function.get("name"), str):
        raise ProxyError("invalid_function")


def prepare_request(request):
    """Preserve message/tool objects; own only transport and bounded output fields."""
    if not isinstance(request, dict):
        raise ProxyError("invalid_request")
    allowed = {
        "model", "messages", "stream", "stream_options", "temperature", "top_p",
        "max_tokens", "max_completion_tokens", "stop", "presence_penalty", "frequency_penalty",
        "seed", "response_format", "tools", "tool_choice", "parallel_tool_calls", "reasoning",
        "reasoning_effort", "n", "logit_bias", "logprobs", "top_logprobs", "user",
    }
    if set(request) - allowed:
        raise ProxyError("unsupported_request_field")
    if request.get("model", MODEL) != MODEL:
        raise ProxyError("model_not_authorized")
    if request.get("n", 1) != 1 or isinstance(request.get("n", 1), bool):
        raise ProxyError("multiple_completions_not_allowed")
    if not isinstance(request.get("stream", False), bool):
        raise ProxyError("invalid_stream")
    options = request.get("stream_options", {})
    if not isinstance(options, dict) or set(options) - {"include_usage"}:
        raise ProxyError("invalid_stream_options")
    if "include_usage" in options and not isinstance(options["include_usage"], bool):
        raise ProxyError("invalid_stream_options")
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ProxyError("invalid_messages")
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in {"system", "developer", "user", "assistant", "tool"}:
            raise ProxyError("invalid_message")
        if set(message) - {"role", "content", "name", "tool_call_id", "tool_calls", "refusal", "reasoning", "reasoning_details"}:
            raise ProxyError("unsupported_message_field")
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if not isinstance(part, dict) or set(part) != {"type", "text"} or part.get("type") != "text" or not isinstance(part.get("text"), str):
                    raise ProxyError("only_text_content_allowed")
        elif content is not None and not isinstance(content, str):
            raise ProxyError("only_text_content_allowed")
        if "tool_calls" in message:
            calls = message["tool_calls"]
            if not isinstance(calls, list):
                raise ProxyError("invalid_tool_calls")
            for call in calls:
                if not isinstance(call, dict) or call.get("type") != "function" or set(call) - {"id", "type", "function"}:
                    raise ProxyError("only_function_tools_allowed")
                _validate_function(call.get("function"))
                if not isinstance(call["function"].get("arguments"), str):
                    raise ProxyError("invalid_tool_arguments")
    if "tools" in request:
        if not isinstance(request["tools"], list):
            raise ProxyError("invalid_tools")
        for tool in request["tools"]:
            if not isinstance(tool, dict) or tool.get("type") != "function" or set(tool) != {"type", "function"}:
                raise ProxyError("only_function_tools_allowed")
            _validate_function(tool["function"])
    if "tool_choice" in request:
        choice = request["tool_choice"]
        if isinstance(choice, dict):
            if set(choice) != {"type", "function"} or choice.get("type") != "function":
                raise ProxyError("invalid_tool_choice")
            _validate_function(choice.get("function"))
        elif choice not in ("none", "auto", "required"):
            raise ProxyError("invalid_tool_choice")
    reasoning = request.get("reasoning", {"enabled": False})
    if not isinstance(reasoning, dict) or set(reasoning) - {"enabled", "effort", "exclude", "max_tokens"}:
        raise ProxyError("invalid_reasoning")
    enabled = reasoning.get("enabled", "effort" in reasoning or "max_tokens" in reasoning)
    if not isinstance(enabled, bool):
        raise ProxyError("invalid_reasoning")
    effort = request.get("reasoning_effort")
    if effort is not None:
        if effort not in {"none", "minimal", "low", "medium", "high", "xhigh"} or "reasoning" in request:
            raise ProxyError("invalid_reasoning")
        enabled = effort != "none"
    if "max_tokens" in request and "max_completion_tokens" in request:
        raise ProxyError("conflicting_output_limits")
    maximum = request.get("max_tokens", request.get("max_completion_tokens", 512))
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= (8192 if enabled else 2048):
        raise ProxyError("output_limit_stop")
    if "max_tokens" in reasoning and (not isinstance(reasoning["max_tokens"], int) or isinstance(reasoning["max_tokens"], bool) or not 0 <= reasoning["max_tokens"] <= maximum):
        raise ProxyError("invalid_reasoning_limit")
    payload = copy.deepcopy(before_forward(request))
    payload.pop("max_completion_tokens", None)
    payload.update(model=MODEL, max_tokens=maximum, provider=copy.deepcopy(PROVIDER))
    payload.setdefault("stream", False)
    if effort is None:
        payload.setdefault("reasoning", {"enabled": False})
    if payload["stream"]:
        # Accounting, not content: ask for a final usage frame even if omitted.
        payload["stream_options"] = {"include_usage": True}
    raw = _json_bytes(payload)
    if len(raw) > MAX_REQUEST_BYTES:
        raise ProxyError("prompt_size_stop", 413)
    reserve = max(.05, (len(raw) + 2048) * .000001 + maximum * .000002)
    return payload, raw, reserve


class BudgetLedger:
    """Same charges table and BEGIN IMMEDIATE reservation rule as P2 Cloud."""

    def __init__(self, path=DEFAULT_BUDGET, limit=5):
        if not _finite_number(limit) or not 0 < limit <= 5:
            raise ValueError("budget_limit_must_be_at_most_5")
        self.path, self.limit = Path(path), limit
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS charges (id TEXT PRIMARY KEY, usd REAL NOT NULL, status TEXT NOT NULL)")

    @contextmanager
    def _connect(self):
        # One connection per operation works across HTTP threads and other P2 processes.
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, amount):
        identity = uuid.uuid4().hex
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            spent = db.execute("SELECT COALESCE(SUM(usd),0) FROM charges").fetchone()[0]
            if not _finite_number(spent) or spent + amount > self.limit:
                raise ProxyError("budget_stop", 402)
            db.execute("INSERT INTO charges VALUES (?,?,?)", (identity, amount, "reserved_unknown"))
        return identity

    def settle(self, identity, usage):
        cost = usage.get("cost") if isinstance(usage, dict) else None
        if _finite_number(cost) and cost >= 0:
            with self._connect() as db:
                db.execute("UPDATE charges SET usd=?,status=? WHERE id=?", (cost, "reported", identity))
            return cost
        return None  # Unknown spend is never released or guessed to be zero.

    def total(self):
        with self._connect() as db:
            return db.execute("SELECT COALESCE(SUM(usd),0) FROM charges").fetchone()[0]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect_refused", headers, fp)


@dataclass(repr=False)
class UpstreamCall:
    response: object
    payload: dict
    charge_id: str
    reserved_usd: float
    usage: dict = field(default_factory=dict)


class FixedRouteTransport:
    """P2 policy adapter, without Cloud's legacy file-based credential reader."""

    model, route = MODEL, ROUTE

    def __init__(self, *, api_key, budget_path=DEFAULT_BUDGET, limit=5, timeout=90, _opener=None):
        if not isinstance(api_key, str) or not api_key or "\r" in api_key or "\n" in api_key:
            raise ValueError("invalid_memory_credential")
        self._key = api_key
        self.ledger = BudgetLedger(budget_path, limit)
        self.timeout = timeout
        self._open = _opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open
        self._supported = None
        self._preflight_lock = threading.Lock()
        self.preflight_metadata = None

    def preflight(self):
        with self._preflight_lock:
            if self._supported is not None:
                return self.preflight_metadata
            request = urllib.request.Request(UPSTREAM + "/endpoints/zdr", headers={"Authorization": "Bearer " + self._key})
            try:
                with self._open(request, timeout=min(self.timeout, 20)) as response:
                    raw = response.read(8_000_001)
                    if len(raw) > 8_000_000:
                        raise ValueError("large_preflight")
                    endpoints = _parse_json(raw)["data"]
                compatible = []
                for endpoint in endpoints:
                    pricing = endpoint.get("pricing", {})
                    prompt, completion = float(pricing.get("prompt", "nan")), float(pricing.get("completion", "nan"))
                    parameters = set(endpoint.get("supported_parameters", []))
                    if (endpoint.get("model_id") == MODEL and endpoint.get("tag") == ROUTE
                            and 0 <= prompt <= .000001 and 0 <= completion <= .000002
                            and float(pricing.get("request", 0)) == 0
                            and {"response_format", "max_tokens", "temperature", "reasoning"} <= parameters):
                        compatible.append((parameters, prompt, completion))
                if not compatible:
                    raise ProxyError("route_preflight_rejected", 503)
                self._supported, prompt, completion = compatible[0]
                self.preflight_metadata = {"model": MODEL, "route": ROUTE, "zdr_listed": True,
                                           "prompt_usd_per_token": prompt, "completion_usd_per_token": completion}
                return dict(self.preflight_metadata)
            except ProxyError:
                raise
            except Exception:
                raise ProxyError("route_preflight_unavailable", 502) from None

    def open_call(self, request):
        payload, raw, reserve = prepare_request(request)
        self.preflight()
        # Fail before spend if the fixed endpoint cannot honour requested optional parameters.
        parameters = set(payload) - {"model", "messages", "stream", "stream_options", "provider", "user", "n"}
        if parameters - self._supported:
            raise ProxyError("route_parameter_not_supported", 400)
        identity = self.ledger.reserve(reserve)
        upstream = urllib.request.Request(UPSTREAM + "/chat/completions", data=raw,
                                         headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
        try:
            response = self._open(upstream, timeout=self.timeout)
            return UpstreamCall(response, payload, identity, reserve)
        except Exception:
            raise ProxyError("upstream_unavailable", 502, charge_id=identity, reserved_usd=reserve) from None


class AuditLog:
    """Bodies stay under runs/, with exact secrets and credential patterns redacted."""

    def __init__(self, path, secret_values=()):
        self.path = Path(path)
        if not self.path.resolve().is_relative_to((ROOT / "runs").resolve()):
            raise ValueError("audit_path_must_be_under_growth_runs")
        self.path.mkdir(parents=True, exist_ok=True)
        self._secrets = tuple(value for value in secret_values if value)
        self._lock = threading.Lock()

    def _redact(self, value):
        if isinstance(value, dict):
            return {self._redact(key): ("[REDACTED]" if re.search(r"api.?key|authorization|password|secret|access.?token", key, re.I)
                          else self._redact(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, "[REDACTED]")
            return re.sub(r"sk-(?:or-)?[A-Za-z0-9_-]{8,}", "[REDACTED]", value)
        return value

    def write(self, filename, value):
        encoded = _json_bytes(self._redact(value)) + b"\n"
        with self._lock:
            with (self.path / filename).open("ab") as output:
                output.write(encoded)


class _LoopbackHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        # Base implementation prints exception/body context to stderr.
        self.owner.audit.write("events.jsonl", {"unix_s": time.time(), "outcome": "internal_error"})


class ProxyServer:
    """Own the returned token in memory; never print or persist it."""

    def __init__(self, transport, *, port=0, log_dir=DEFAULT_LOGS, allowed_origins=DEFAULT_ORIGINS):
        self.transport = transport
        self.token = secrets.token_urlsafe(32)
        self.allowed_origins = frozenset(allowed_origins)
        self.audit = AuditLog(log_dir, (self.token, transport._key))
        self.httpd = _LoopbackHTTPServer(("127.0.0.1", port), _Handler)
        self.httpd.owner = self
        self.base_url = "http://127.0.0.1:%d/v1" % self.httpd.server_address[1]
        self._thread = None

    def start(self):
        if self._thread is not None:
            raise RuntimeError("server_already_started")
        self._thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": .1}, daemon=True)
        self._thread.start()
        self.audit.write("events.jsonl", {"unix_s": time.time(), "outcome": "started", "base_url": self.base_url,
                                          "model": MODEL, "route": ROUTE, "budget_limit_usd": self.transport.ledger.limit})
        return self

    def close(self):
        if self._thread is not None:
            self.httpd.shutdown()
            self._thread.join(timeout=5)
        self.httpd.server_close()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "P7Proxy"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    @property
    def owner(self):
        return self.server.owner

    def setup(self):
        super().setup()
        self.connection.settimeout(100)

    def _headers(self, status, content_type, length=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.close_connection = True
        if length is not None:
            self.send_header("Content-Length", str(length))
        origin = self.headers.get("Origin")
        if origin in self.owner.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _json(self, status, data):
        raw = _json_bytes(data)
        self._headers(status, "application/json; charset=utf-8", len(raw))
        self.wfile.write(raw)

    def _error(self, error):
        self._json(error.status, {"error": {"message": error.code, "type": "p7_proxy_error", "code": error.code}})

    def _check_request(self, auth=True):
        host = self.headers.get("Host", "")
        if host not in {"127.0.0.1:%d" % self.server.server_address[1], "localhost:%d" % self.server.server_address[1]}:
            raise ProxyError("host_not_allowed", 403)
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self.owner.allowed_origins:
            raise ProxyError("origin_not_allowed", 403)
        if auth:
            credentials = self.headers.get_all("Authorization", [])
            if len(credentials) != 1 or not credentials[0].isascii() or not hmac.compare_digest(credentials[0], "Bearer " + self.owner.token):
                raise ProxyError("unauthorized", 401)

    def _event(self, outcome, started, *, error=None, call=None, usage=None):
        event = {"unix_s": time.time(), "outcome": outcome, "latency_s": time.perf_counter() - started,
                 "endpoint": "chat" if self.command == "POST" else "models" if self.command == "GET" else "options"}
        if error:
            event.update(error_code=error.code, http_status=error.status)
            if error.charge_id:
                event.update(charge_id=error.charge_id, reserved_usd=error.reserved_usd)
        if call:
            usage = usage if isinstance(usage, dict) and usage else call.usage
            cost = self.owner.transport.ledger.settle(call.charge_id, usage)
            event.update(charge_id=call.charge_id, reserved_usd=call.reserved_usd, cost_usd=cost,
                         input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
                         stream=call.payload["stream"])
        event["budget_reserved_or_reported_usd"] = self.owner.transport.ledger.total()
        self.owner.audit.write("events.jsonl", event)

    def do_OPTIONS(self):
        start = time.perf_counter()
        try:
            self._check_request(auth=False)
            if self.path not in {"/v1/models", "/v1/chat/completions"}:
                raise ProxyError("not_found", 404)
            self._headers(204, "application/json", 0)
            self._event("cors_preflight", start)
        except ProxyError as error:
            self._event("rejected", start, error=error)
            self._error(error)

    def do_GET(self):
        start = time.perf_counter()
        try:
            self._check_request()
            if self.path != "/v1/models":
                raise ProxyError("not_found", 404)
            self._json(200, {"object": "list", "data": [{"id": MODEL, "object": "model", "created": 0, "owned_by": "p7-fixed-route"}]})
            self._event("models", start)
        except ProxyError as error:
            self._event("rejected", start, error=error)
            self._error(error)

    def do_POST(self):
        started, call, usage, streamed = time.perf_counter(), None, {}, False
        try:
            self._check_request()
            if self.path != "/v1/chat/completions":
                raise ProxyError("not_found", 404)
            if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Encoding"):
                raise ProxyError("encoded_body_not_allowed", 400)
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isdigit():
                raise ProxyError("content_length_required", 411)
            length = int(lengths[0])
            if not 0 < length <= MAX_REQUEST_BYTES:
                raise ProxyError("prompt_size_stop", 413)
            if self.headers.get_content_type() != "application/json":
                raise ProxyError("json_required", 415)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ProxyError("incomplete_body", 400)
            try:
                request = _parse_json(raw)
            except (ValueError, UnicodeError):
                raise ProxyError("invalid_json", 400) from None
            call = self.owner.transport.open_call(request)
            self.owner.audit.write("content.jsonl", {"charge_id": call.charge_id, "direction": "request", "body": request})
            with call.response as response:
                content_type = response.headers.get_content_type()
                if call.payload["stream"]:
                    if content_type != "text/event-stream":
                        raise ProxyError("invalid_upstream_content_type", 502)
                    self._headers(200, "text/event-stream; charset=utf-8")
                    streamed = True
                    usage = self._stream(response, call)
                else:
                    if content_type != "application/json":
                        raise ProxyError("invalid_upstream_content_type", 502)
                    raw = response.read(MAX_RESPONSE_BYTES + 1)
                    if len(raw) > MAX_RESPONSE_BYTES:
                        raise ProxyError("upstream_response_too_large", 502)
                    data = _parse_json(raw)
                    if not isinstance(data, dict) or data.get("error") or not isinstance(data.get("choices"), list):
                        raise ProxyError("upstream_error", 502)
                    data = after_forward(data)
                    usage = data.get("usage", {})
                    self.owner.audit.write("content.jsonl", {"charge_id": call.charge_id, "direction": "response", "body": data})
                    # Commit cost and audit before a client can observe a complete success.
                    self._event("completed", started, call=call, usage=usage)
                    self._json(200, data)
                    return
            self._event("completed", started, call=call, usage=usage)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self._event("client_disconnected", started, call=call, usage=usage)
        except Exception as caught:
            error = caught if isinstance(caught, ProxyError) else ProxyError("upstream_or_internal_error", 502)
            self._event("rejected" if call is None else "failed", started, error=error, call=call, usage=usage)
            try:
                if streamed:
                    self.wfile.write(b"data: " + _json_bytes({"error": {"code": error.code, "message": error.code}}) + b"\n\ndata: [DONE]\n\n")
                    self.wfile.flush()
                else:
                    self._error(error)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    def _stream(self, response, call):
        data_lines, size, usage, saw_done = [], 0, {}, False
        while True:
            line = response.readline(MAX_RESPONSE_BYTES + 1)
            if not line:
                break
            size += len(line)
            if size > MAX_RESPONSE_BYTES:
                raise ProxyError("upstream_response_too_large", 502)
            stripped = line.rstrip(b"\r\n")
            if stripped.startswith(b":"):
                # Do not log/echo arbitrary comments; they may carry upstream errors.
                self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
            elif stripped.startswith(b"data:"):
                data_lines.append(stripped[5:].lstrip(b" "))
            elif stripped == b"" and data_lines:
                payload = b"\n".join(data_lines)
                data_lines = []
                if payload == b"[DONE]":
                    saw_done = True
                    break
                try:
                    data = _parse_json(payload)
                except (ValueError, UnicodeError):
                    raise ProxyError("invalid_upstream_stream", 502) from None
                if not isinstance(data, dict) or data.get("error"):
                    raise ProxyError("upstream_stream_error", 502)
                data = after_forward(data)
                if isinstance(data.get("usage"), dict):
                    usage = data["usage"]
                    call.usage = usage
                    # Settle at the known usage frame even if the downstream disappears later.
                    self.owner.transport.ledger.settle(call.charge_id, usage)
                self.owner.audit.write("content.jsonl", {"charge_id": call.charge_id, "direction": "response_chunk", "body": data})
                self.wfile.write(b"data: " + _json_bytes(data) + b"\n\n")
                self.wfile.flush()
        if not saw_done:
            raise ProxyError("upstream_stream_incomplete", 502)
        return usage
