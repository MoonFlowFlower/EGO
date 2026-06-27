#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_CACHE_REPORT = (
    ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_cache_v0" / "RAW_CACHE_REPORT.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_capture_manifest_v0"
REQUIRED_TRACE_FIELDS = [
    "run_id",
    "condition_id",
    "split_id",
    "source_id",
    "source_text_sha256",
    "source_cache_sha256",
    "serialized_state",
    "public_inputs",
    "adapter_output",
    "d_field_provenance",
    "replay_inputs",
    "row_hash",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def artifact_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _resolve_cache_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def _read_jsonl_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_capture_manifest(
    *,
    raw_cache_report_path: Path = DEFAULT_RAW_CACHE_REPORT,
    rows_per_source: int = 5,
    privacy_mode: str = "raw_local_only",
    created_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if rows_per_source <= 0:
        raise ValueError("rows_per_source must be positive")
    if privacy_mode not in {"hash_only", "redacted_excerpt", "raw_local_only"}:
        raise ValueError(f"unsupported privacy_mode: {privacy_mode}")

    raw_cache_report = load_json(raw_cache_report_path)
    raw_cache_report_hash = sha256_text(raw_cache_report_path.read_text(encoding="utf-8"))
    selected_rows: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []

    for result in raw_cache_report.get("results") or []:
        if not result.get("cache_written"):
            continue
        source_id = str(result["source_id"])
        split = str(result["split"])
        cache_path = _resolve_cache_path(str(result["cache_path"]))
        cache_text = cache_path.read_text(encoding="utf-8")
        cache_hash = sha256_text(cache_text)
        expected_cache_hash = str(result["cache_sha256"])
        if cache_hash != expected_cache_hash:
            raise ValueError(f"cache hash mismatch for {source_id}: expected {expected_cache_hash}, got {cache_hash}")

        lines = _read_jsonl_lines(cache_path)
        selected_count = min(rows_per_source, len(lines))
        source_summaries.append(
            {
                "source_id": source_id,
                "split": split,
                "cache_path": _relative(cache_path),
                "cache_sha256": cache_hash,
                "available_rows": len(lines),
                "selected_rows": selected_count,
                "source_url": result.get("source_url"),
                "method": result.get("method"),
                "license_name": result.get("license_name"),
                "source_license_tier": result.get("source_license_tier"),
            }
        )

        for line_number, line in enumerate(lines[:rows_per_source]):
            row_payload = json.loads(line)
            row_idx = row_payload.get("row_idx", line_number)
            selected_rows.append(
                {
                    "selection_id": f"{source_id}:{split}:{row_idx}",
                    "source_id": source_id,
                    "split": split,
                    "row_idx": row_idx,
                    "source_cache_path": _relative(cache_path),
                    "source_cache_sha256": cache_hash,
                    "row_content_sha256": sha256_text(line),
                    "raw_text_privacy_mode": privacy_mode,
                    "source_url": result.get("source_url"),
                    "license_name": result.get("license_name"),
                    "source_license_tier": result.get("source_license_tier"),
                    "desktop_trigger_required": "window.egoDesktop.sendChatTurn",
                    "writer_required": "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
                    "future_trace_required_fields": REQUIRED_TRACE_FIELDS,
                }
            )

    manifest = {
        "schema": "egodesktop.joi_real_loop.capture_manifest.v0",
        "manifest_id": "egodesktop_joi_real_loop_g_ablation_capture_manifest_v0",
        "created_at": created_at or _utc_now(),
        "producer_function": "build_capture_manifest",
        "claim_ceiling": "capture_manifest_hash_selection_only",
        "raw_cache_report": _relative(raw_cache_report_path),
        "raw_cache_report_sha256": raw_cache_report_hash,
        "row_selection_rule": f"first_{rows_per_source}_rows_per_source_in_cached_jsonl_order",
        "raw_text_in_manifest": False,
        "capture_authority": False,
        "scoring_authority": False,
        "runtime_authority": False,
        "program_state_authority": False,
        "evidence_ledger_authority": False,
        "remote_authority": False,
        "source_summaries": source_summaries,
        "selected_rows": selected_rows,
    }
    build_report = {
        "schema": "egodesktop.joi_real_loop.capture_manifest_build_report.v0",
        "producer_function": "build_capture_manifest",
        "raw_cache_report": _relative(raw_cache_report_path),
        "raw_cache_report_sha256": raw_cache_report_hash,
        "source_count": len(source_summaries),
        "selected_row_count": len(selected_rows),
        "claim_ceiling": "capture_manifest_hash_selection_only",
        "raw_text_in_manifest": False,
        "capture_authority": False,
        "scoring_authority": False,
        "runtime_authority": False,
    }
    return manifest, build_report


def write_artifacts(output_dir: Path, manifest: dict[str, Any], build_report: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "CAPTURE_MANIFEST.json"
    manifest_path.write_text(artifact_json_text(manifest), encoding="utf-8")
    manifest_hash = sha256_text(manifest_path.read_text(encoding="utf-8"))
    (output_dir / "CAPTURE_MANIFEST.sha256").write_text(manifest_hash + "\n", encoding="utf-8")
    report = dict(build_report)
    report.update(
        {
            "capture_manifest": _relative(manifest_path),
            "capture_manifest_sha256": manifest_hash,
        }
    )
    (output_dir / "BUILD_REPORT.json").write_text(artifact_json_text(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build hash-only EgoDesktop G-ABLATION capture manifest.")
    parser.add_argument("--raw-cache-report", type=Path, default=DEFAULT_RAW_CACHE_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--rows-per-source", type=int, default=5)
    parser.add_argument("--privacy-mode", default="raw_local_only")
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args(argv)

    manifest, build_report = build_capture_manifest(
        raw_cache_report_path=args.raw_cache_report,
        rows_per_source=args.rows_per_source,
        privacy_mode=args.privacy_mode,
        created_at=args.created_at,
    )
    write_artifacts(args.out, manifest, build_report)
    print(artifact_json_text(manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
