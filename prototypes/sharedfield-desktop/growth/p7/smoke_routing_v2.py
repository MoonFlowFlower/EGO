"""A new candidate only; import the exact v1 prompts and response validator."""
import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from growthlab.models import read_key
from .proxy import BudgetLedger, ProxyServer, ROOT
from .routing_v2 import RoutedTransportV2, configuration
from .smoke_routing import PROMPTS, MANIFEST as V1_MANIFEST, inspect_response, sha, write_new

MANIFEST = ROOT / "evidence/routing/frozen_v2.json"
BASE = ROOT / "runs/routing/live_v2"
SOURCES = ["p7/routing_v2.py", "p7/routing_v2.json", "p7/active_proxy.py", "p7/smoke_routing_v2.py",
           "p7/test_routing_v2.py", "evidence/routing/ROUTING_V2_PRE_RUN.md"]


def check_v1():
    original = json.loads(V1_MANIFEST.read_bytes())
    if any(sha(ROOT / path) != expected for path, expected in original["sources"].items()):
        raise RuntimeError("v1_frozen_source_changed")
    return original


def freeze():
    v1 = check_v1()
    write_new(MANIFEST, {"version": "routing-v2", "created_utc": datetime.now(timezone.utc).isoformat(),
                        "sources": {path: sha(ROOT / path) for path in SOURCES},
                        "v1_manifest_sha256": sha(V1_MANIFEST), "configuration": configuration(),
                        "route_index": 2, "prompts": PROMPTS, "inference": v1["inference"],
                        "max_calls": 3, "additional_budget_cap_usd": .20, "v1_v2_cap_usd": .60})
    print(json.dumps({"frozen_manifest_sha256": sha(MANIFEST)}))


def run():
    check_v1()
    manifest = json.loads(MANIFEST.read_bytes())
    if sha(V1_MANIFEST) != manifest["v1_manifest_sha256"] or any(sha(ROOT / path) != expected for path, expected in manifest["sources"].items()):
        raise RuntimeError("frozen_source_changed")
    BASE.mkdir(parents=True, exist_ok=False)
    ledger = BudgetLedger()
    before = ledger.total()
    v1_result = json.loads((ROOT / "evidence/routing/live_v1.json").read_bytes())
    transport = RoutedTransportV2(api_key=read_key(), mode="pinned", route_index=2, log_dir=BASE)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    rows = []
    with ProxyServer(transport, log_dir=BASE) as server:
        for probe in manifest["prompts"]:
            if ledger.total() - before + .05 > .20 or ledger.total() - v1_result["budget_before_usd"] + .05 > .60:
                raise RuntimeError("additional_budget_stop")
            started = time.perf_counter()
            row = {"route_index": 2, **manifest["configuration"]["routes"][2], "probe": probe["kind"], "pass": False}
            request = urllib.request.Request(server.base_url + "/chat/completions",
                data=json.dumps({"model": transport.model, **manifest["inference"], **probe["request"]}, ensure_ascii=False).encode(),
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
                row["error"] = type(error).__name__
            row["latency_s"] = round(time.perf_counter() - started, 4)
            row["ledger_total_usd"] = ledger.total()
            rows.append(row)
            with (BASE / "probes.jsonl").open("ab") as output:
                output.write((json.dumps(row, ensure_ascii=False) + "\n").encode())
            print(json.dumps(row, ensure_ascii=False), flush=True)
    result = {"manifest_sha256": sha(MANIFEST), "pass": len(rows) == 3 and all(r["pass"] for r in rows),
              "probes": rows, "budget_before_usd": before, "budget_after_usd": ledger.total(),
              "additional_reserved_or_reported_usd": ledger.total() - before,
              "reported_success_cost_usd": sum(r.get("cost_usd") or 0 for r in rows),
              "temporary_proxy_closed": True, "generated_tools_executed": 0,
              "claim": "connectivity_only_not_unlimited_or_learning_quality"}
    write_new(ROOT / "evidence/routing/live_v2.json", result)
    print(json.dumps({k: result[k] for k in ["pass", "reported_success_cost_usd", "additional_reserved_or_reported_usd", "budget_after_usd"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["freeze", "run"])
    args = parser.parse_args()
    freeze() if args.action == "freeze" else run()
