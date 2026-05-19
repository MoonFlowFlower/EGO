#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from h1_e4_sampling_common import (
    ROOT,
    build_appearance_payload,
    build_failures_payload,
    build_sample_manifest_payload,
    load_frozen_sample_matrix,
    load_sample_bundles,
    now_iso,
    read_json,
    rel_path,
    render_appearance_markdown,
    render_failures_markdown,
    write_json,
    write_text,
)


TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "simulated-shadow-h1-mainline-sampling"
REPORTS_DIR = ROOT / "artifacts" / "telegram_simulated_mainline_v1" / "reports"
SIMULATED_TELEGRAM_DIR = ROOT / "artifacts" / "telegram_simulated_mainline_v1" / "simulated_telegram"
SIMULATED_MIRROR_DIR = ROOT / "artifacts" / "telegram_simulated_mainline_v1" / "mirror"
RUN_META_JSON = REPORTS_DIR / "H1_SIMULATED_RUN_CURRENT.json"
RUN_META_MD = REPORTS_DIR / "H1_SIMULATED_RUN_CURRENT.md"
SAMPLE_MANIFEST_JSON = REPORTS_DIR / "H1_SIMULATED_SAMPLE_MANIFEST_CURRENT.json"
SAMPLE_MANIFEST_MD = REPORTS_DIR / "H1_SIMULATED_SAMPLE_MANIFEST_CURRENT.md"
APPEARANCE_REPORT_JSON = REPORTS_DIR / "H1_SIMULATED_SHADOW_APPEARANCE_REPORT_CURRENT.json"
APPEARANCE_REPORT_MD = REPORTS_DIR / "H1_SIMULATED_SHADOW_APPEARANCE_REPORT_CURRENT.md"
FAILURES_TABLE_JSON = REPORTS_DIR / "H1_SIMULATED_FAILURES_TABLE_CURRENT.json"
FAILURES_TABLE_MD = REPORTS_DIR / "H1_SIMULATED_FAILURES_TABLE_CURRENT.md"
SAMPLE_LEVEL_REPORT_JSON = REPORTS_DIR / "H1_SIMULATED_SAMPLE_LEVEL_REPORT_CURRENT.json"
SAMPLE_LEVEL_REPORT_MD = REPORTS_DIR / "H1_SIMULATED_SAMPLE_LEVEL_REPORT_CURRENT.md"
FROZEN_SAMPLE_MATRIX_PATH = ROOT / "docs" / "codex" / "tasks" / "e4-shadow-h1-formal-mainline-sampling" / "FROZEN_SAMPLE_MATRIX.json"


def render_run_meta_markdown(payload: Dict[str, Any]) -> str:
    return f"""# H1 Simulated Run

- generated_at: `{payload['generated_at']}`
- task_slug: `{payload['task_slug']}`
- source_type: `{payload['source_type']}`
- evidence_level: `{payload['evidence_level']}`
- head_git_commit_short: `{payload['head_git_commit_short']}`
- observed_at: `{payload['observed_at']}`
- prompt_count: `{payload['prompt_count']}`
- session_id: `{payload['session_id']}`
- sample_root: `{payload['sample_root']}`

## Constraints

- claim_ceiling: `simulated_mainline_only`
- no_repo_level_state_upgrade: `True`
- no_runtime_efficacy_claim: `True`
"""


def build_simulated_manifest_payload(
    *,
    sample_matrix: Dict[str, Any],
    bundles,
    run_meta: Dict[str, Any],
) -> Dict[str, Any]:
    payload = build_sample_manifest_payload(
        sample_matrix=sample_matrix,
        bundles=bundles,
        live_process_version={
            "observed_at": None,
            "git_commit_short": run_meta.get("head_git_commit_short"),
        },
    )
    payload["schema_version"] = "h1_simulated.sample_manifest.v1"
    payload["binding_mode"] = "simulated_mainline"
    payload["process_commit_short"] = run_meta.get("head_git_commit_short")
    payload["process_observed_at"] = run_meta.get("observed_at")
    for row in payload.get("rows", []):
        reason = str(row.get("reason") or "")
        row["reason"] = (
            reason.replace("complete E4 bundle", "complete simulated mainline bundle")
            .replace("required E4 files", "required simulated mainline files")
        )
    return payload


def render_simulated_manifest_markdown(payload: Dict[str, Any]) -> str:
    row_lines = []
    for item in payload.get("rows", []):
        row_lines.append(
            "| `{manifest_id}` | `{bucket}` | `{status}` | `{matched}` | {reason} |".format(
                manifest_id=item["manifest_id"],
                bucket=item["bucket"],
                status=item["status"],
                matched=item.get("matched_sample_id") or "none",
                reason=item["reason"],
            )
        )
    summary = payload.get("summary") or {}
    return f"""# H1 Simulated Sample Manifest

- generated_at: `{payload['generated_at']}`
- process_observed_at: `{payload.get('process_observed_at') or 'unknown'}`
- process_commit_short: `{payload.get('process_commit_short') or 'unknown'}`

## Summary

- expected_rows: `{summary.get('expected_rows', 0)}`
- matched_complete: `{summary.get('matched_complete', 0)}`
- matched_incomplete: `{summary.get('matched_incomplete', 0)}`
- missing: `{summary.get('missing', 0)}`
- ambiguous: `{summary.get('ambiguous', 0)}`

## Rows

| manifest_id | bucket | status | matched_sample | reason |
|---|---|---|---|---|
{chr(10).join(row_lines) if row_lines else '| none | none | none | none | none |'}
"""


def render_simulated_appearance_markdown(payload: Dict[str, Any]) -> str:
    base = render_appearance_markdown(payload)
    return base.replace("# H1 E4 Shadow Appearance Report", "# H1 Simulated Shadow Appearance Report")


def render_simulated_failures_markdown(payload: Dict[str, Any]) -> str:
    base = render_failures_markdown(payload)
    return base.replace("# H1 E4 Failures Table", "# H1 Simulated Failures Table")


def build_simulated_final_report(
    *,
    run_meta: Dict[str, Any],
    manifest_payload: Dict[str, Any],
    appearance_payload: Dict[str, Any],
    failures_payload: Dict[str, Any],
) -> Dict[str, Any]:
    manifest_summary = dict(manifest_payload.get("summary") or {})
    appearance_summary = dict(appearance_payload.get("summary") or {})
    failures_summary = dict(failures_payload.get("summary") or {})
    qualifying_rows = [
        row for row in manifest_payload.get("rows", [])
        if row.get("status") == "matched_complete"
    ]
    return {
        "schema_version": "h1_simulated.sample_level_report.v1",
        "generated_at": now_iso(),
        "decision": (
            "simulated_sample_observation_ready"
            if not failures_summary.get("failure_count")
            else "simulated_sample_collection_incomplete"
        ),
        "claim_ceiling": "canonical shadow_h1 telemetry observed on the simulated Telegram mainline only",
        "run_meta_ref": rel_path(RUN_META_JSON),
        "summary": {
            "matched_complete": manifest_summary.get("matched_complete", 0),
            "matched_incomplete": manifest_summary.get("matched_incomplete", 0),
            "missing": manifest_summary.get("missing", 0),
            "ambiguous": manifest_summary.get("ambiguous", 0),
            "shadow_present": appearance_summary.get("shadow_present", 0),
            "guard_true_count": appearance_summary.get("guard_true_count", 0),
            "failure_count": failures_summary.get("failure_count", 0),
            "qualifying_sample_ids": [
                row.get("matched_sample_id") for row in qualifying_rows if row.get("matched_sample_id")
            ],
        },
        "not_proven": [
            "runtime efficacy",
            "real Telegram / E4 sampling",
            "live decision promotion",
            "repo-level enablement",
        ],
        "source_type": run_meta.get("source_type"),
        "evidence_level": run_meta.get("evidence_level"),
    }


def render_simulated_final_markdown(payload: Dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    return f"""# H1 Simulated Sample-Level Report

- generated_at: `{payload['generated_at']}`
- decision: `{payload['decision']}`
- claim_ceiling: `{payload['claim_ceiling']}`
- source_type: `{payload.get('source_type')}`
- evidence_level: `{payload.get('evidence_level')}`

## Summary

- matched_complete: `{summary.get('matched_complete', 0)}`
- matched_incomplete: `{summary.get('matched_incomplete', 0)}`
- missing: `{summary.get('missing', 0)}`
- ambiguous: `{summary.get('ambiguous', 0)}`
- shadow_present: `{summary.get('shadow_present', 0)}`
- guard_true_count: `{summary.get('guard_true_count', 0)}`
- failure_count: `{summary.get('failure_count', 0)}`

## Not Proven

- runtime efficacy
- real Telegram / E4 sampling
- live decision promotion
- repo-level enablement
"""


def load_run_meta() -> Dict[str, Any]:
    return read_json(RUN_META_JSON)


def build_simulated_reports() -> Dict[str, Any]:
    sample_matrix = load_frozen_sample_matrix(FROZEN_SAMPLE_MATRIX_PATH)
    run_meta = load_run_meta()
    bundles = load_sample_bundles(SIMULATED_TELEGRAM_DIR)
    manifest_payload = build_simulated_manifest_payload(
        sample_matrix=sample_matrix,
        bundles=bundles,
        run_meta=run_meta,
    )
    appearance_payload = build_appearance_payload(manifest_payload)
    appearance_payload["schema_version"] = "h1_simulated.shadow_appearance.v1"
    failures_payload = build_failures_payload(manifest_payload)
    failures_payload["schema_version"] = "h1_simulated.failures_table.v1"
    final_payload = build_simulated_final_report(
        run_meta=run_meta,
        manifest_payload=manifest_payload,
        appearance_payload=appearance_payload,
        failures_payload=failures_payload,
    )
    return {
        "run_meta": run_meta,
        "manifest": manifest_payload,
        "appearance": appearance_payload,
        "failures": failures_payload,
        "final": final_payload,
    }


def write_simulated_reports(payloads: Dict[str, Any]) -> None:
    write_json(RUN_META_JSON, payloads["run_meta"])
    write_text(RUN_META_MD, render_run_meta_markdown(payloads["run_meta"]))
    write_json(SAMPLE_MANIFEST_JSON, payloads["manifest"])
    write_text(SAMPLE_MANIFEST_MD, render_simulated_manifest_markdown(payloads["manifest"]))
    write_json(APPEARANCE_REPORT_JSON, payloads["appearance"])
    write_text(APPEARANCE_REPORT_MD, render_simulated_appearance_markdown(payloads["appearance"]))
    write_json(FAILURES_TABLE_JSON, payloads["failures"])
    write_text(FAILURES_TABLE_MD, render_simulated_failures_markdown(payloads["failures"]))
    write_json(SAMPLE_LEVEL_REPORT_JSON, payloads["final"])
    write_text(SAMPLE_LEVEL_REPORT_MD, render_simulated_final_markdown(payloads["final"]))


__all__ = [
    "TASK_DIR",
    "REPORTS_DIR",
    "SIMULATED_TELEGRAM_DIR",
    "SIMULATED_MIRROR_DIR",
    "RUN_META_JSON",
    "RUN_META_MD",
    "SAMPLE_MANIFEST_JSON",
    "SAMPLE_MANIFEST_MD",
    "APPEARANCE_REPORT_JSON",
    "APPEARANCE_REPORT_MD",
    "FAILURES_TABLE_JSON",
    "FAILURES_TABLE_MD",
    "SAMPLE_LEVEL_REPORT_JSON",
    "SAMPLE_LEVEL_REPORT_MD",
    "FROZEN_SAMPLE_MATRIX_PATH",
    "load_run_meta",
    "build_simulated_reports",
    "write_simulated_reports",
]
