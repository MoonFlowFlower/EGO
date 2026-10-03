"""Freeze before the first metered request; nine predeclared probes, no retries."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from growthlab.models import read_key
from .proxy import BudgetLedger, ProxyError, ProxyServer, ROOT
from .routing import RoutedTransport, configuration

OUT = ROOT / "evidence/routing"
MANIFEST = OUT / "frozen_v1.json"
BASE = ROOT / "runs/routing/live_v1"
SOURCES = ["p7/proxy.py", "p7/routing.py", "p7/routing_v1.json", "p7/runtime_session.py",
           "p7/launch_proxy.py", "p7/smoke_routing.py", "p7/test_proxy.py", "p7/test_routing.py",
           "growthlab/models.py", "evidence/routing/ROUTING_V1_PRE_RUN.md"]
PROMPTS = [
    {"kind": "json", "request": {"messages": [{"role": "user", "content": 'Return only this JSON object: {"ok":true}'}],
                                  "response_format": {"type": "json_object"}}},
    {"kind": "stream", "request": {"messages": [{"role": "user", "content": "请只回复：收到"}], "stream": True}},
    {"kind": "tool", "request": {"messages": [{"role": "user", "content": "Call echo with value p7. Do not execute anything."}],
                                  "tools": [{"type": "function", "function": {"name": "echo", "description": "Return a value (inspection only; never executed)",
                                              "parameters": {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False}}}],
                                  "tool_choice": {"type": "function", "function": {"name": "echo"}}}},
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def freeze():
    write_new(MANIFEST, {"version": "routing-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                        "sources": {path: sha(ROOT / path) for path in SOURCES}, "configuration": configuration(),
                        "prompts": PROMPTS, "max_calls": 9, "additional_budget_cap_usd": .60,
                        "inference": {"temperature": 0, "reasoning": {"enabled": False}, "max_tokens": 512},
                        "u1_v1_manifest_sha256": sha(ROOT / "evidence/u1/frozen_v1.json"),
                        "official_metadata_sha256": sha(ROOT / "runs/routing/metadata_20261003/zdr.json")})
    print(json.dumps({"frozen_manifest_sha256": sha(MANIFEST)}))


def inspect_response(kind, raw):
    """Validate only the fixed transport probe. This is not an ability benchmark."""
    if kind == "stream":
        chunks = [json.loads(line[6:]) for line in raw.decode().splitlines()
                  if line.startswith("data: ") and line != "data: [DONE]"]
        content = "".join(choice.get("delta", {}).get("content") or "" for chunk in chunks for choice in chunk.get("choices", []))
        data = {"model": next((c.get("model") for c in chunks if c.get("model")), None),
                "provider": next((c.get("provider") for c in chunks if c.get("provider")), None),
                "usage": next((c["usage"] for c in reversed(chunks) if c.get("usage")), {})}
        valid = content.strip() == "收到" and b"data: [DONE]" in raw and not any(c.get("error") for c in chunks)
    else:
        data = json.loads(raw)
        message = data["choices"][0]["message"]
        if kind == "json":
            answer = json.loads(message["content"])
            valid = isinstance(answer, dict) and set(answer) == {"ok"} and answer["ok"] is True
        else:
            calls = message.get("tool_calls", [])
            valid = len(calls) == 1 and calls[0]["function"]["name"] == "echo" and json.loads(calls[0]["function"]["arguments"]) == {"value": "p7"}
    cost = data.get("usage", {}).get("cost")
    valid = valid and isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0
    return bool(valid), {"actual_model": data.get("model"), "actual_provider": data.get("provider"),
                         "cost_usd": cost, "usage": data.get("usage")}


def run():
    manifest = json.loads(MANIFEST.read_bytes())
    if any(sha(ROOT / path) != expected for path, expected in manifest["sources"].items()):
        raise RuntimeError("frozen_source_changed")
    if manifest["u1_v1_manifest_sha256"] != sha(ROOT / "evidence/u1/frozen_v1.json"):
        raise RuntimeError("u1_manifest_changed")
    BASE.mkdir(parents=True, exist_ok=False)  # A repeated command cannot silently rerun probes.
    ledger = BudgetLedger()
    start_budget = ledger.total()
    rows = []
    key = read_key()  # Existing owner-authorized credential reader; never printed or copied.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for index, route in enumerate(manifest["configuration"]["routes"]):
        transport = RoutedTransport(api_key=key, mode="pinned", route_index=index, log_dir=BASE / str(index))
        with ProxyServer(transport, log_dir=BASE / str(index)) as server:
            for probe in manifest["prompts"]:
                if ledger.total() - start_budget + .05 > manifest["additional_budget_cap_usd"]:
                    raise RuntimeError("additional_budget_stop")
                started = time.perf_counter()
                row = {"route_index": index, **route, "probe": probe["kind"], "pass": False}
                payload = {"model": transport.model, **manifest["inference"], **probe["request"]}
                request = urllib.request.Request(server.base_url + "/chat/completions",
                    data=json.dumps(payload, ensure_ascii=False).encode(),
                    headers={"Authorization": "Bearer " + server.token, "Content-Type": "application/json"})
                try:
                    with opener.open(request, timeout=55) as response:
                        raw = response.read(4_000_001)
                        row["http_status"] = response.status
                    valid, details = inspect_response(probe["kind"], raw)
                    row.update(details)
                    row["pass"] = valid
                except urllib.error.HTTPError as error:
                    row.update(http_status=error.code, error="http_error")
                    error.close()
                except Exception as error:
                    row["error"] = type(error).__name__  # No exception text / headers / tokens.
                row["latency_s"] = round(time.perf_counter() - started, 4)
                row["ledger_total_usd"] = ledger.total()
                rows.append(row)
                with (BASE / "probes.jsonl").open("ab") as output:
                    output.write((json.dumps(row, ensure_ascii=False) + "\n").encode())
                print(json.dumps({k: row.get(k) for k in ["route_index", "probe", "pass", "http_status", "error", "actual_model", "actual_provider", "cost_usd", "latency_s"]}), flush=True)
    report = {"manifest_sha256": sha(MANIFEST), "route_pass": [all(r["pass"] for r in rows if r["route_index"] == i) for i in range(3)],
              "probes": rows, "budget_before_usd": start_budget, "budget_after_usd": ledger.total(),
              "additional_reserved_or_reported_usd": ledger.total() - start_budget,
              "reported_success_cost_usd": sum(r.get("cost_usd") or 0 for r in rows),
              "temporary_proxies_closed": True, "generated_tools_executed": 0,
              "claim": "connectivity_only_not_unlimited_or_learning_quality"}
    write_new(OUT / "live_v1.json", report)
    print(json.dumps({k: report[k] for k in ["route_pass", "reported_success_cost_usd", "additional_reserved_or_reported_usd", "budget_after_usd"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze", "run"])
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    else:
        run()
