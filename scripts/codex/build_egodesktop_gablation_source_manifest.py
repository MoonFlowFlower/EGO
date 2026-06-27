#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def artifact_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(
    *,
    source_id: str,
    source_kind: str,
    source_license_tier: str,
    source_url_or_local_path: str,
    license_name: str,
    license_url: str,
    attribution_required: bool,
    sharealike_required: bool,
    noncommercial_only: bool,
    gated_terms_required: bool,
    operator_terms_review_required: bool,
    operator_terms_review_status: str,
    admission_status: str,
    download_status: str,
    cache_policy: str,
    raw_text_policy: str,
    privacy_mode: str,
    pii_review_required: bool,
    allowed_claim_ceiling: str,
    blocked_downstream_claims: list[str],
    future_capture_eligible: bool,
    future_capture_blockers: list[str],
    blocked_reason: str,
    retrieved_at: str,
    license_text_hash_or_card_hash: str = "",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_kind": source_kind,
        "source_license_tier": source_license_tier,
        "source_url_or_local_path": source_url_or_local_path,
        "retrieved_at": retrieved_at,
        "license_name": license_name,
        "license_url": license_url,
        "license_text_hash_or_card_hash": license_text_hash_or_card_hash,
        "attribution_required": attribution_required,
        "sharealike_required": sharealike_required,
        "noncommercial_only": noncommercial_only,
        "gated_terms_required": gated_terms_required,
        "operator_terms_review_required": operator_terms_review_required,
        "operator_terms_review_status": operator_terms_review_status,
        "admission_status": admission_status,
        "download_status": download_status,
        "cache_policy": cache_policy,
        "raw_text_policy": raw_text_policy,
        "privacy_mode": privacy_mode,
        "pii_review_required": pii_review_required,
        "allowed_claim_ceiling": allowed_claim_ceiling,
        "blocked_downstream_claims": blocked_downstream_claims,
        "future_capture_eligible": future_capture_eligible,
        "future_capture_blockers": future_capture_blockers,
        "b011_carry_forward_required": True,
        "independence_cluster_keys": [
            "dataset_or_local_artifact",
            "session_or_speaker_id",
            "topic",
            "template_or_near_duplicate_surface",
            "affect_band",
        ],
        "split_meta_leakage_scan_required": True,
        "source_hash": sha256_text(source_url_or_local_path),
        "content_hash_strategy": "hash_only_or_redacted_excerpt_before_capture",
        "blocked_reason": blocked_reason,
    }


def build_source_manifest(*, created_at: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    created = created_at or _utc_now()
    blocked_claims = [
        "product_claim",
        "companion_readiness",
        "commercial_use",
        "stable_user_benefit",
        "agency",
        "emotion",
        "subjectivity",
        "consciousness",
        "alive_status",
        "bar2_specialness",
    ]
    rows = [
        _row(
            source_id="local_egodesktop_session_context_v0",
            source_kind="local_egodesktop_artifact",
            source_license_tier="local_operator_private",
            source_url_or_local_path="artifacts/egodesktop_session_local_conversation_context_v0/session_context_report.json",
            license_name="local_private_operator_artifact",
            license_url="local",
            attribution_required=False,
            sharealike_required=False,
            noncommercial_only=True,
            gated_terms_required=False,
            operator_terms_review_required=True,
            operator_terms_review_status="required_before_raw_text_use",
            admission_status="metadata_allowed",
            download_status="not_downloadable",
            cache_policy="no_raw_cache_in_016",
            raw_text_policy="hash_only_or_redacted_excerpt_required_before_capture",
            privacy_mode="blocked_until_privacy_manifest",
            pii_review_required=True,
            allowed_claim_ceiling="local_private_metadata_only",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["blocked_until_privacy_manifest"],
            blocked_reason="local private text requires privacy manifest before any capture use",
            retrieved_at=created,
        ),
        _row(
            source_id="egodesktop_gablation_009_predeclared_single_capture",
            source_kind="local_egodesktop_artifact",
            source_license_tier="local_operator_private",
            source_url_or_local_path=(
                "artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/"
                "capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl"
            ),
            license_name="local_private_operator_artifact",
            license_url="local",
            attribution_required=False,
            sharealike_required=False,
            noncommercial_only=True,
            gated_terms_required=False,
            operator_terms_review_required=True,
            operator_terms_review_status="required_before_raw_text_use",
            admission_status="metadata_allowed",
            download_status="not_downloadable",
            cache_policy="no_raw_cache_in_016",
            raw_text_policy="hash_only_or_redacted_excerpt_required_before_capture",
            privacy_mode="blocked_prior_calibration_only",
            pii_review_required=True,
            allowed_claim_ceiling="prior_calibration_provenance_only",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["prior_calibration_only_not_heldout_creature_on_source"],
            blocked_reason="accepted prior calibration provenance only",
            retrieved_at=created,
        ),
        _row(
            source_id="egodesktop_gablation_009_turn2_rejected_posthoc",
            source_kind="local_egodesktop_artifact",
            source_license_tier="blocked_negative_evidence",
            source_url_or_local_path=(
                "artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/"
                "capture/calibration_ui_turn2/"
            ),
            license_name="blocked_negative_evidence",
            license_url="local",
            attribution_required=False,
            sharealike_required=False,
            noncommercial_only=True,
            gated_terms_required=False,
            operator_terms_review_required=False,
            operator_terms_review_status="not_applicable_negative_evidence",
            admission_status="negative_evidence_only",
            download_status="not_downloadable",
            cache_policy="no_raw_cache_in_016",
            raw_text_policy="not_admitted",
            privacy_mode="not_admitted",
            pii_review_required=False,
            allowed_claim_ceiling="negative_evidence_only",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["rejected_posthoc_positional_selection"],
            blocked_reason="must never enter source manifest input rows, calibration basis, capture basis, score, or comparison",
            retrieved_at=created,
        ),
        _row(
            source_id="dailydialog_hf",
            source_kind="public_dataset",
            source_license_tier="public_nc_sa",
            source_url_or_local_path="https://huggingface.co/datasets/roskoN/dailydialog",
            license_name="cc-by-nc-sa-4.0",
            license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
            license_text_hash_or_card_hash=sha256_text(
                "https://huggingface.co/datasets/roskoN/dailydialog/raw/main/README.md|cc-by-nc-sa-4.0"
            ),
            attribution_required=True,
            sharealike_required=True,
            noncommercial_only=True,
            gated_terms_required=False,
            operator_terms_review_required=False,
            operator_terms_review_status="not_required_metadata_only",
            admission_status="candidate_metadata_only",
            download_status="future_local_download_conditional",
            cache_policy="future_local_cache_only",
            raw_text_policy="raw_local_only_or_hash_only",
            privacy_mode="redacted_excerpt_or_hash_only_before_capture",
            pii_review_required=True,
            allowed_claim_ceiling="local_noncommercial_evidence_only",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["blocked_until_manifest_and_leakage_gates"],
            blocked_reason="future capture blocked until source manifest, leakage, independence, affect, and anti-degeneracy gates pass",
            retrieved_at=created,
        ),
        _row(
            source_id="empathetic_dialogues_hf",
            source_kind="public_dataset",
            source_license_tier="public_noncommercial",
            source_url_or_local_path="https://huggingface.co/datasets/facebook/empathetic_dialogues",
            license_name="cc-by-nc-4.0",
            license_url="https://creativecommons.org/licenses/by-nc/4.0/",
            license_text_hash_or_card_hash=sha256_text(
                "https://huggingface.co/datasets/facebook/empathetic_dialogues|cc-by-nc-4.0"
            ),
            attribution_required=True,
            sharealike_required=False,
            noncommercial_only=True,
            gated_terms_required=False,
            operator_terms_review_required=False,
            operator_terms_review_status="not_required_metadata_only",
            admission_status="candidate_metadata_only",
            download_status="future_local_download_conditional",
            cache_policy="future_local_cache_only",
            raw_text_policy="raw_local_only_or_hash_only",
            privacy_mode="redacted_excerpt_or_hash_only_before_capture",
            pii_review_required=True,
            allowed_claim_ceiling="local_noncommercial_evidence_only",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["blocked_until_manifest_and_leakage_gates"],
            blocked_reason="future capture blocked until source manifest, leakage, independence, affect, and anti-degeneracy gates pass",
            retrieved_at=created,
        ),
        _row(
            source_id="lmsys_chat_1m_hf",
            source_kind="public_dataset",
            source_license_tier="gated_or_terms_required",
            source_url_or_local_path="https://huggingface.co/datasets/lmsys/lmsys-chat-1m",
            license_name="unknown_gated_or_terms_required",
            license_url="https://huggingface.co/datasets/lmsys/lmsys-chat-1m",
            attribution_required=False,
            sharealike_required=False,
            noncommercial_only=False,
            gated_terms_required=True,
            operator_terms_review_required=True,
            operator_terms_review_status="required_before_any_use",
            admission_status="blocked",
            download_status="blocked",
            cache_policy="blocked",
            raw_text_policy="not_admitted",
            privacy_mode="not_admitted",
            pii_review_required=True,
            allowed_claim_ceiling="none",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["gated_or_terms_required"],
            blocked_reason="raw card access returned unauthorized during 014 metadata check",
            retrieved_at=created,
        ),
        _row(
            source_id="personachat_parlai",
            source_kind="public_dataset",
            source_license_tier="unknown_or_unclear",
            source_url_or_local_path="https://github.com/facebookresearch/ParlAI/tree/main/projects/personachat",
            license_name="unknown_or_unclear",
            license_url="https://github.com/facebookresearch/ParlAI/tree/main/projects/personachat",
            attribution_required=False,
            sharealike_required=False,
            noncommercial_only=False,
            gated_terms_required=False,
            operator_terms_review_required=True,
            operator_terms_review_status="required_before_any_use",
            admission_status="blocked",
            download_status="blocked",
            cache_policy="blocked",
            raw_text_policy="not_admitted",
            privacy_mode="not_admitted",
            pii_review_required=True,
            allowed_claim_ceiling="none",
            blocked_downstream_claims=blocked_claims,
            future_capture_eligible=False,
            future_capture_blockers=["unknown_or_unclear_license"],
            blocked_reason="data license and download path not established",
            retrieved_at=created,
        ),
    ]

    manifest = {
        "schema": "egodesktop.joi_real_loop.source_manifest.v0",
        "manifest_id": "egodesktop_joi_real_loop_g_ablation_source_manifest_v0",
        "created_at": created,
        "producer_function": "build_source_manifest",
        "source_policy_version": "egodesktop_joi_real_loop_source_policy_v0",
        "claim_ceiling": "source_manifest_artifact_only",
        "no_capture_authority": True,
        "no_scoring_authority": True,
        "no_product_claim_authority": True,
        "no_runtime_authority": True,
        "no_program_state_authority": True,
        "no_evidence_ledger_authority": True,
        "no_remote_authority": True,
        "source_rows": rows,
    }

    planned_actions = [
        {
            "source_id": row["source_id"],
            "action": "future_local_download_conditional",
            "source_url": row["source_url_or_local_path"],
            "required_before_download": [
                "separate_downloader_task",
                "license_card_hash_readback",
                "raw_cache_local_only",
                "no_capture_or_scoring",
            ],
        }
        for row in rows
        if row["download_status"] == "future_local_download_conditional"
    ]
    download_plan = {
        "schema": "egodesktop.joi_real_loop.source_download_plan.v0",
        "plan_id": "egodesktop_joi_real_loop_g_ablation_source_download_plan_v0",
        "created_at": created,
        "producer_function": "build_source_manifest",
        "download_authority": "none_in_016",
        "raw_cache_created": False,
        "claim_ceiling": "source_manifest_artifact_only",
        "planned_actions": planned_actions,
        "blocked_source_ids": [
            row["source_id"]
            for row in rows
            if row["download_status"] in {"blocked", "not_downloadable"}
        ],
    }
    manifest["download_plan_hash"] = sha256_text(artifact_json_text(download_plan))
    return manifest, download_plan


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(artifact_json_text(payload), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_artifacts(output_dir: Path, manifest: dict[str, Any], download_plan: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "SOURCE_MANIFEST.json"
    plan_path = output_dir / "SOURCE_DOWNLOAD_PLAN.json"
    _write_json(manifest_path, manifest)
    _write_json(plan_path, download_plan)

    manifest_hash = sha256_text(manifest_path.read_text(encoding="utf-8"))
    plan_hash = sha256_text(plan_path.read_text(encoding="utf-8"))
    (output_dir / "SOURCE_MANIFEST.sha256").write_text(manifest_hash + "\n", encoding="utf-8")
    (output_dir / "SOURCE_DOWNLOAD_PLAN.sha256").write_text(plan_hash + "\n", encoding="utf-8")

    report = {
        "schema": "egodesktop.joi_real_loop.source_manifest_build_report.v0",
        "producer_function": "build_source_manifest.write_artifacts",
        "source_manifest": _display_path(manifest_path),
        "source_manifest_sha256": manifest_hash,
        "source_download_plan": _display_path(plan_path),
        "source_download_plan_sha256": plan_hash,
        "raw_cache_created": False,
        "download_executed": False,
        "claim_ceiling": "source_manifest_artifact_only",
    }
    _write_json(output_dir / "BUILD_REPORT.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EgoDesktop G-ABLATION source manifest artifacts.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args(argv)

    manifest, download_plan = build_source_manifest(created_at=args.created_at)
    report = write_artifacts(args.out, manifest, download_plan)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
