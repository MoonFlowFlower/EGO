"""Pinned GPT-6 Luna trial adapter; frozen product routes are not changed.

Chat Completions tools require reasoning_effort=none. Temperature is unsupported
and must be omitted explicitly, rather than silently pretending it is zero.
"""
import copy
import json
import urllib.error
import urllib.request

from .proxy import MAX_REQUEST_BYTES, ProxyError, UPSTREAM, UpstreamCall, _json_bytes, prepare_request
from .routing import RoutedTransport, retry_after_seconds

MODEL = "openai/gpt-6-luna"
ROUTE = "azure"


def prepare_luna(request, provider):
    if not isinstance(request, dict):
        raise ProxyError("invalid_request")
    if "temperature" in request:
        raise ProxyError("luna_temperature_must_be_omitted")
    if request.get("reasoning_effort", "none") != "none":
        raise ProxyError("luna_trial_requires_reasoning_none")
    if "reasoning" in request and request["reasoning"] != {"enabled": False}:
        raise ProxyError("luna_trial_requires_reasoning_none")
    if "reasoning" in request and "reasoning_effort" in request:
        raise ProxyError("conflicting_reasoning_parameters")
    normalized = copy.deepcopy(request)
    normalized.pop("reasoning", None)
    normalized["reasoning_effort"] = "none"
    payload, _, _ = prepare_request(normalized, model=MODEL, provider=provider)
    payload["max_completion_tokens"] = payload.pop("max_tokens")
    raw = _json_bytes(payload)
    if len(raw) > MAX_REQUEST_BYTES:
        raise ProxyError("prompt_size_stop", 413)
    reserve = max(.05, (len(raw) + 2048) * .000001 + payload["max_completion_tokens"] * .000002)
    return payload, raw, reserve


def safe_error_metadata(error, now):
    """Retain error classification, never free-form body/header text."""
    headers = error.headers or {}
    safe = {"http_status": error.code,
            "retry_after_s": retry_after_seconds(headers.get("Retry-After"), now)}
    platform_header = False
    for header, name in [("X-RateLimit-Limit", "rate_limit"), ("X-RateLimit-Remaining", "rate_remaining"),
                         ("X-RateLimit-Reset", "rate_reset")]:
        value = headers.get(header, "")
        if str(value).isdigit() and len(str(value)) <= 16:
            safe[name] = int(value)
            platform_header = True
    try:
        body = json.loads(error.read(65537))
        metadata = body.get("error", {}).get("metadata", {})
        code = metadata.get("provider_code")
        if str(code).isdigit() and len(str(code)) == 3:
            safe["provider_code"] = int(code)
        allowed = {"rate_limit_exceeded", "rate_limit_error", "insufficient_quota", "invalid_request_error", "unsupported_parameter", "model_not_found"}
        for key in ("error_type", "code", "type"):
            value = metadata.get(key, body.get("error", {}).get(key))
            if isinstance(value, str) and value in allowed:
                safe[key] = value
    except Exception:
        pass
    if error.code == 429:
        safe["rate_origin_evidence"] = "platform_header" if platform_header else "provider_code" if "provider_code" in safe else "unknown"
    return safe


class LunaTransport(RoutedTransport):
    def __init__(self, *, mode="pinned", route_index=0, **kwargs):
        if mode != "pinned" or route_index != 0:
            raise ValueError("luna_trial_is_pinned")
        super().__init__(mode="pinned", route_index=0, **kwargs)
        self.model, self.route = MODEL, ROUTE
        self.routes = [{"model": MODEL, "route": ROUTE}]
        self.provider = {**copy.deepcopy(self.policy["provider"]), "only": [ROUTE]}

    def preflight(self):
        with self._call_lock:
            self._refresh()
            eligible, reason = self._eligible(self.routes[0], {"max_completion_tokens", "response_format", "reasoning_effort", "tools", "tool_choice"})
            if not eligible:
                raise ProxyError(reason, 503)
            return {"model": MODEL, "route": ROUTE, "mode": "pinned", "zdr_listed": True,
                    "reasoning_effort": "none", "temperature": "omitted", "metadata_at": self._metadata_at}

    def open_call(self, request):
        payload, raw, reserve = prepare_luna(request, self.provider)
        parameters = set(payload) - {"model", "messages", "stream", "stream_options", "provider", "user", "n"}
        with self._call_lock:
            self._refresh()
            eligible, reason = self._eligible(self.routes[0], parameters)
            if not eligible:
                self._event("preflight_rejected", reason=reason, **self.routes[0])
                raise ProxyError(reason, 503)
            charge_id = self.ledger.reserve(reserve)
            self._event("attempt", charge_id=charge_id, reserved_usd=reserve, **self.routes[0])
            self.audit.write("wire.jsonl", {"charge_id": charge_id, "body": payload})
            request = urllib.request.Request(UPSTREAM + "/chat/completions", data=raw,
                headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
            try:
                response = self._open(request, timeout=self.timeout)
                self._event("response_opened", charge_id=charge_id, **self.routes[0])
                return UpstreamCall(response, payload, charge_id, reserve)
            except urllib.error.HTTPError as error:
                safe = safe_error_metadata(error, self._clock())
                error.close()
                self._event("http_error", **safe, charge_id=charge_id, reserved_usd=reserve, **self.routes[0])
                raise ProxyError("upstream_http_" + str(error.code), error.code,
                                 charge_id=charge_id, reserved_usd=reserve) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                self._event("connection_error", charge_id=charge_id, reserved_usd=reserve, **self.routes[0])
                raise ProxyError("upstream_connection_error", 502, charge_id=charge_id, reserved_usd=reserve) from None
            except Exception:
                self._event("unexpected_error", charge_id=charge_id, reserved_usd=reserve, **self.routes[0])
                raise ProxyError("upstream_unavailable", 502, charge_id=charge_id, reserved_usd=reserve) from None
