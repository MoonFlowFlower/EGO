#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
DOWNLOAD_PLAN_PATH = (
    ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_DOWNLOAD_PLAN.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_cache_v0"


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content: bytes
    content_type: str


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def artifact_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_by_source(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_id")): dict(row) for row in manifest.get("source_rows") or []}


def build_metadata_smoke_actions(manifest: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, str]]:
    rows = _row_by_source(manifest)
    actions: list[dict[str, str]] = []
    for item in plan.get("planned_actions") or []:
        source_id = str(item.get("source_id") or "")
        row = rows.get(source_id)
        if not row:
            raise ValueError(f"planned source missing from manifest: {source_id}")
        if row.get("admission_status") != "candidate_metadata_only":
            raise ValueError(f"planned source is not admissible: {source_id}")
        if row.get("download_status") != "future_local_download_conditional":
            raise ValueError(f"planned source has blocked download status: {source_id}")
        if row.get("gated_terms_required") or row.get("operator_terms_review_required"):
            raise ValueError(f"planned source requires gated/operator terms review: {source_id}")
        if not str(item.get("source_url") or "").startswith("https://huggingface.co/datasets/"):
            raise ValueError(f"planned source URL is not an allowed Hugging Face dataset page: {source_id}")
        actions.append(
            {
                "source_id": source_id,
                "url": str(item.get("source_url")),
                "license_name": str(row.get("license_name") or ""),
                "source_license_tier": str(row.get("source_license_tier") or ""),
            }
        )
    return actions


def fetch_url(url: str) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "EGO-source-cache-metadata-smoke/0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return FetchResult(
                url=url,
                status_code=int(getattr(response, "status", 200)),
                content=response.read(),
                content_type=str(response.headers.get("content-type") or ""),
            )
    except urllib.error.HTTPError as exc:
        return FetchResult(
            url=url,
            status_code=int(exc.code),
            content=exc.read(),
            content_type=str(exc.headers.get("content-type") or ""),
        )


def run_metadata_smoke(
    actions: list[dict[str, str]],
    *,
    fetcher: Callable[[str], FetchResult] = fetch_url,
    created_at: str | None = None,
) -> dict[str, Any]:
    results = []
    for action in actions:
        fetched = fetcher(action["url"])
        results.append(
            {
                "source_id": action["source_id"],
                "url": fetched.url,
                "status_code": fetched.status_code,
                "reachable": 200 <= fetched.status_code < 400,
                "content_type": fetched.content_type,
                "byte_count": len(fetched.content),
                "content_sha256": sha256_bytes(fetched.content),
                "license_name": action["license_name"],
                "source_license_tier": action["source_license_tier"],
                "raw_text_stored": False,
            }
        )
    return {
        "schema": "egodesktop.joi_real_loop.source_cache_metadata_smoke.v0",
        "created_at": created_at or _utc_now(),
        "producer_function": "run_metadata_smoke",
        "claim_ceiling": "source_cache_downloader_tool_and_metadata_smoke_only",
        "download_authority": "metadata_only_no_raw_cache",
        "raw_text_stored": False,
        "raw_cache_created": False,
        "capture_authority": False,
        "scoring_authority": False,
        "runtime_authority": False,
        "program_state_authority": False,
        "evidence_ledger_authority": False,
        "remote_authority": False,
        "results": results,
    }


def write_report(output_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "CACHE_SMOKE_REPORT.json"
    report_path.write_text(artifact_json_text(report), encoding="utf-8")
    report_hash = sha256_text(report_path.read_text(encoding="utf-8"))
    (output_dir / "CACHE_SMOKE_REPORT.sha256").write_text(report_hash + "\n", encoding="utf-8")
    return {
        "schema": "egodesktop.joi_real_loop.source_cache_metadata_smoke_write_report.v0",
        "producer_function": "write_report",
        "cache_smoke_report": str(report_path.relative_to(ROOT)) if report_path.is_relative_to(ROOT) else str(report_path),
        "cache_smoke_report_sha256": report_hash,
        "raw_text_stored": False,
        "raw_cache_created": False,
        "claim_ceiling": "source_cache_downloader_tool_and_metadata_smoke_only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run metadata-only source cache smoke for EgoDesktop G-ABLATION.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--plan", type=Path, default=DOWNLOAD_PLAN_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    plan = load_json(args.plan)
    actions = build_metadata_smoke_actions(manifest, plan)
    report = run_metadata_smoke(actions, created_at=args.created_at)
    write_report(args.out, report)
    print(artifact_json_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
