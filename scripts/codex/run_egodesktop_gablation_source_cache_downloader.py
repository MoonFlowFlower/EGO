#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tarfile
import urllib.error
import urllib.parse
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
RAW_CACHE_DIRNAME = "source_cache"

RAW_CACHE_SOURCE_METHODS = {
    "dailydialog_hf": {
        "method": "hf_rows_api",
        "dataset": "roskoN/dailydialog",
        "config": "full",
    },
    "empathetic_dialogues_hf": {
        "method": "direct_archive_csv",
        "archive_url": "https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz",
        "archive_members": {
            "train": "empatheticdialogues/train.csv",
            "validation": "empatheticdialogues/valid.csv",
            "test": "empatheticdialogues/test.csv",
        },
    },
    "wizard_of_wikipedia_hf": {
        "method": "hf_rows_api",
        "dataset": "chujiezheng/wizard_of_wikipedia",
        "config": "default",
    },
}


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


def jsonl_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


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


def build_raw_cache_actions(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    *,
    split: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    if max_rows <= 0:
        raise ValueError("max_rows must be positive")
    if split not in {"train", "validation", "test"}:
        raise ValueError(f"unsupported split: {split}")

    actions: list[dict[str, Any]] = []
    for base_action in build_metadata_smoke_actions(manifest, plan):
        source_id = base_action["source_id"]
        method_spec = RAW_CACHE_SOURCE_METHODS.get(source_id)
        if method_spec is None:
            raise ValueError(f"no raw-cache method configured for source: {source_id}")
        method = str(method_spec["method"])
        action: dict[str, Any] = {
            "source_id": source_id,
            "method": method,
            "source_url": base_action["url"],
            "split": split,
            "max_rows": max_rows,
            "license_name": base_action["license_name"],
            "source_license_tier": base_action["source_license_tier"],
        }
        if method == "hf_rows_api":
            query = urllib.parse.urlencode(
                {
                    "dataset": method_spec["dataset"],
                    "config": method_spec["config"],
                    "split": split,
                    "offset": 0,
                    "length": max_rows,
                }
            )
            action["url"] = f"https://datasets-server.huggingface.co/rows?{query}"
        elif method == "direct_archive_csv":
            members = method_spec.get("archive_members") or {}
            archive_member = str(members.get(split) or "")
            if not archive_member:
                raise ValueError(f"no archive member configured for source/split: {source_id}/{split}")
            action["url"] = method_spec["archive_url"]
            action["archive_member"] = archive_member
        else:
            raise ValueError(f"unsupported raw-cache method: {method}")
        actions.append(action)
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


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _write_sample_rows(cache_path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("".join(jsonl_text(record) for record in records), encoding="utf-8")
    return {
        "cache_path": _relative(cache_path),
        "cache_sha256": sha256_text(cache_path.read_text(encoding="utf-8")),
        "row_count": len(records),
    }


def _records_from_hf_rows_payload(action: dict[str, Any], fetched: FetchResult) -> tuple[list[dict[str, Any]], int | None]:
    payload = json.loads(fetched.content.decode("utf-8"))
    rows = payload.get("rows") or []
    records = [
        {
            "source_id": action["source_id"],
            "split": action["split"],
            "row_idx": row.get("row_idx"),
            "row": row.get("row"),
        }
        for row in rows[: int(action["max_rows"])]
    ]
    total = payload.get("num_rows_total")
    return records, int(total) if isinstance(total, int) else None


def _records_from_archive_csv(action: dict[str, Any], fetched: FetchResult) -> list[dict[str, Any]]:
    max_rows = int(action["max_rows"])
    with tarfile.open(fileobj=io.BytesIO(fetched.content), mode="r:gz") as archive:
        member = archive.extractfile(str(action["archive_member"]))
        if member is None:
            raise ValueError(f"archive member not found: {action['archive_member']}")
        text = member.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    records = []
    for row_idx, row in enumerate(reader):
        if row_idx >= max_rows:
            break
        records.append(
            {
                "source_id": action["source_id"],
                "split": action["split"],
                "row_idx": row_idx,
                "row": dict(row),
            }
        )
    return records


def run_raw_cache_sample(
    actions: list[dict[str, Any]],
    *,
    output_dir: Path,
    fetcher: Callable[[str], FetchResult] = fetch_url,
    created_at: str | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    cache_root = output_dir / RAW_CACHE_DIRNAME
    for action in actions:
        fetched = fetcher(str(action["url"]))
        result: dict[str, Any] = {
            "source_id": action["source_id"],
            "method": action["method"],
            "url": fetched.url,
            "source_url": action["source_url"],
            "split": action["split"],
            "max_rows": action["max_rows"],
            "status_code": fetched.status_code,
            "reachable": 200 <= fetched.status_code < 400,
            "content_type": fetched.content_type,
            "byte_count": len(fetched.content),
            "content_sha256": sha256_bytes(fetched.content),
            "license_name": action["license_name"],
            "source_license_tier": action["source_license_tier"],
            "raw_text_stored": False,
            "cache_written": False,
            "row_count": 0,
        }
        if result["reachable"]:
            if action["method"] == "hf_rows_api":
                records, total = _records_from_hf_rows_payload(action, fetched)
                if total is not None:
                    result["num_rows_total"] = total
            elif action["method"] == "direct_archive_csv":
                result["archive_member"] = action["archive_member"]
                records = _records_from_archive_csv(action, fetched)
            else:
                raise ValueError(f"unsupported raw-cache method: {action['method']}")
            cache_path = cache_root / str(action["source_id"]) / f"{action['split']}_sample.jsonl"
            cache_result = _write_sample_rows(cache_path, records)
            result.update(cache_result)
            result["raw_text_stored"] = True
            result["cache_written"] = True
        results.append(result)

    return {
        "schema": "egodesktop.joi_real_loop.source_cache_raw_sample.v0",
        "created_at": created_at or _utc_now(),
        "producer_function": "run_raw_cache_sample",
        "claim_ceiling": "bounded_public_raw_cache_sample_only",
        "download_authority": "bounded_public_raw_cache_local_only",
        "raw_text_stored": any(bool(item.get("raw_text_stored")) for item in results),
        "raw_cache_created": any(bool(item.get("cache_written")) for item in results),
        "local_cache_root": _relative(cache_root),
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


def write_raw_cache_report(output_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "RAW_CACHE_REPORT.json"
    report_path.write_text(artifact_json_text(report), encoding="utf-8")
    report_hash = sha256_text(report_path.read_text(encoding="utf-8"))
    (output_dir / "RAW_CACHE_REPORT.sha256").write_text(report_hash + "\n", encoding="utf-8")
    return {
        "schema": "egodesktop.joi_real_loop.source_cache_raw_sample_write_report.v0",
        "producer_function": "write_raw_cache_report",
        "raw_cache_report": _relative(report_path),
        "raw_cache_report_sha256": report_hash,
        "raw_text_stored": bool(report.get("raw_text_stored")),
        "raw_cache_created": bool(report.get("raw_cache_created")),
        "claim_ceiling": "bounded_public_raw_cache_sample_only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run metadata-only source cache smoke for EgoDesktop G-ABLATION.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--plan", type=Path, default=DOWNLOAD_PLAN_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--raw-cache-sample", action="store_true")
    parser.add_argument("--split", default="train")
    parser.add_argument("--max-rows", type=int, default=25)
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    plan = load_json(args.plan)
    if args.raw_cache_sample:
        actions = build_raw_cache_actions(manifest, plan, split=args.split, max_rows=args.max_rows)
        report = run_raw_cache_sample(actions, output_dir=args.out, created_at=args.created_at)
        write_raw_cache_report(args.out, report)
    else:
        actions = build_metadata_smoke_actions(manifest, plan)
        report = run_metadata_smoke(actions, created_at=args.created_at)
        write_report(args.out, report)
    print(artifact_json_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
