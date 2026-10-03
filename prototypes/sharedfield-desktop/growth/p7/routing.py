"""Bounded, audited availability routing; a pinned mode never changes endpoints.

All retries happen before an upstream response is returned to the HTTP handler.
This layer cannot replay a partial stream or execute a tool or generated code.
"""
from __future__ import annotations

import copy
import json
import math
import threading
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

from .proxy import (
    AuditLog, DEFAULT_LOGS, FixedRouteTransport, ProxyError, UPSTREAM, UpstreamCall,
    _parse_json, prepare_request,
)

CONFIG_PATH = Path(__file__).with_name("routing_v1.json")


def configuration():
    return json.loads(CONFIG_PATH.read_bytes())


def retry_after_seconds(value, now):
    """Whitelist only a duration; never persist an arbitrary response header."""
    try:
        duration = float(value)
    except (TypeError, ValueError):
        try:
            duration = parsedate_to_datetime(value).timestamp() - now
        except (TypeError, ValueError, OverflowError):
            return 0.0
    return max(0.0, duration) if math.isfinite(duration) else 0.0


class RoutedTransport(FixedRouteTransport):
    def __init__(self, *, mode="product", route_index=0, log_dir=DEFAULT_LOGS / "routing-v1",
                 _clock=time.time, **kwargs):
        super().__init__(**kwargs)
        if mode not in {"product", "pinned"}:
            raise ValueError("invalid_routing_mode")
        self.config = configuration()
        self.policy = self.config["policy"]
        if not 0 <= route_index < len(self.config["routes"]):
            raise ValueError("invalid_route_index")
        self.routes = self.config["routes"] if mode == "product" else [self.config["routes"][route_index]]
        self.mode, self._clock = mode, _clock
        self.model = self.config["public_model"] if mode == "product" else self.routes[0]["model"]
        self.route = self.config["version"] if mode == "product" else self.routes[0]["route"]
        self.timeout = min(self.timeout, self.policy["timeout_seconds"])
        self.audit = AuditLog(log_dir, (self._key,))
        self._metadata = None
        self._metadata_at = 0.0
        self._cooldown = {}
        self._call_lock = threading.Lock()

    def set_audit(self, audit):
        self.audit = audit

    def _event(self, outcome, **fields):
        self.audit.write("routing.jsonl", {"unix_s": self._clock(), "outcome": outcome,
                                          "mode": self.mode, **fields})

    def _refresh(self):
        if self._metadata is not None and self._clock() - self._metadata_at < self.policy["metadata_ttl_seconds"]:
            return
        request = urllib.request.Request(UPSTREAM + "/endpoints/zdr",
                                         headers={"Authorization": "Bearer " + self._key})
        try:
            with self._open(request, timeout=min(self.timeout, 20)) as response:
                raw = response.read(8_000_001)
            if len(raw) > 8_000_000:
                raise ValueError("large_metadata")
            rows = _parse_json(raw)["data"]
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise ValueError("invalid_metadata")
        except Exception:
            self._event("metadata_unavailable")
            raise ProxyError("route_preflight_unavailable", 502) from None
        self._metadata, self._metadata_at = rows, self._clock()

    def _eligible(self, spec, parameters):
        matching = [row for row in self._metadata
                    if row.get("model_id") == spec["model"] and row.get("tag") == spec["route"]]
        if not matching:
            return False, "route_not_zdr_listed"
        # A tag can describe multiple deployments: every matching entry must fit.
        for row in matching:
            try:
                price = row["pricing"]
                a, b = float(price["prompt"]), float(price["completion"])
                if not (0 <= a <= 1e-6 and 0 <= b <= 2e-6 and float(price.get("request", 0)) == 0):
                    return False, "route_price_rejected"
                if not parameters <= set(row.get("supported_parameters", [])):
                    return False, "route_parameter_not_supported"
            except (KeyError, TypeError, ValueError):
                return False, "invalid_route_metadata"
        return True, "eligible"

    def preflight(self):
        with self._call_lock:
            self._refresh()
            eligible = [spec for spec in self.routes
                        if self._eligible(spec, {"response_format", "max_tokens", "temperature", "reasoning", "tools"})[0]]
            if not eligible:
                raise ProxyError("route_preflight_rejected", 503)
            self.preflight_metadata = {"model": self.model, "mode": self.mode, "eligible_routes": eligible,
                                       "zdr_listed": True, "metadata_at": self._metadata_at}
            return copy.deepcopy(self.preflight_metadata)

    def open_call(self, request):
        # Validate the caller before any network access or expenditure.
        base, _, _ = prepare_request(request, model=self.model, provider=self.policy["provider"])
        parameters = set(base) - {"model", "messages", "stream", "stream_options", "provider", "user", "n"}
        with self._call_lock:
            self._refresh()
            tried = 0
            last_error = ProxyError("routes_unavailable_or_cooling_down", 503)
            for spec in self.routes:
                identity_key = (spec["model"], spec["route"])
                if self._cooldown.get(identity_key, 0) > self._clock():
                    self._event("cooldown_skip", **spec)
                    continue
                allowed, reason = self._eligible(spec, parameters)
                if not allowed:
                    self._event("preflight_skip", reason=reason, **spec)
                    # A listed endpoint with unacceptable price/parameters is not
                    # an availability failure. Never relax policy to get through.
                    if reason != "route_not_zdr_listed":
                        raise ProxyError(reason, 400)
                    last_error = ProxyError("route_preflight_rejected", 503)
                    continue
                if tried >= self.policy["max_attempts_per_request"]:
                    break
                tried += 1
                payload = copy.deepcopy(base)
                payload["model"] = spec["model"]
                provider = copy.deepcopy(self.policy["provider"])
                provider["only"] = [spec["route"]]
                payload["provider"] = provider
                # Revalidate byte bound and reservation after replacing the alias.
                prepared = {k: v for k, v in payload.items() if k != "provider"}
                payload, raw, reserve = prepare_request(prepared, model=spec["model"], provider=provider)
                charge_id = self.ledger.reserve(reserve)
                self._event("attempt", attempt=tried, charge_id=charge_id, reserved_usd=reserve, **spec)
                upstream = urllib.request.Request(UPSTREAM + "/chat/completions", data=raw,
                    headers={"Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
                try:
                    response = self._open(upstream, timeout=self.timeout)
                    self._event("response_opened", charge_id=charge_id, **spec)
                    return UpstreamCall(response, payload, charge_id, reserve)
                except urllib.error.HTTPError as error:
                    status = error.code
                    retry_after = retry_after_seconds(error.headers.get("Retry-After") if error.headers else None, self._clock())
                    # Never echo or persist provider text, headers, or request objects.
                    error.close()
                    transient = status in self.policy["fallback_http_statuses"]
                    self._event("http_error", http_status=status, retry_after_s=retry_after,
                                charge_id=charge_id, reserved_usd=reserve, **spec)
                    last_error = ProxyError("upstream_http_" + str(status), status,
                                            charge_id=charge_id, reserved_usd=reserve)
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    transient, retry_after = True, 0
                    self._event("connection_error", charge_id=charge_id, reserved_usd=reserve, **spec)
                    last_error = ProxyError("upstream_connection_error", 502,
                                            charge_id=charge_id, reserved_usd=reserve)
                except Exception:
                    self._event("unexpected_error", charge_id=charge_id, reserved_usd=reserve, **spec)
                    raise ProxyError("upstream_unavailable", 502, charge_id=charge_id, reserved_usd=reserve) from None
                if not transient or self.mode == "pinned":
                    raise last_error from None
                self._cooldown[identity_key] = self._clock() + max(self.policy["cooldown_seconds"], retry_after)
            raise last_error from None
