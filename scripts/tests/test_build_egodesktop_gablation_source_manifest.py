from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "build_egodesktop_gablation_source_manifest.py"
spec = importlib.util.spec_from_file_location("build_egodesktop_gablation_source_manifest", MODULE_PATH)
build_source_manifest = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = build_source_manifest
spec.loader.exec_module(build_source_manifest)


def test_build_source_manifest_denies_runtime_and_evidence_authority() -> None:
    manifest, download_plan = build_source_manifest.build_source_manifest(
        created_at="2026-06-27T00:00:00+00:00"
    )

    assert manifest["schema"] == "egodesktop.joi_real_loop.source_manifest.v0"
    assert manifest["producer_function"] == "build_source_manifest"
    assert manifest["claim_ceiling"] == "source_manifest_artifact_only"
    for field in (
        "no_capture_authority",
        "no_scoring_authority",
        "no_product_claim_authority",
        "no_runtime_authority",
        "no_program_state_authority",
        "no_evidence_ledger_authority",
        "no_remote_authority",
    ):
        assert manifest[field] is True

    assert download_plan["schema"] == "egodesktop.joi_real_loop.source_download_plan.v0"
    assert download_plan["download_authority"] == "none_in_016"
    assert download_plan["raw_cache_created"] is False


def test_candidate_sources_preserve_admission_and_blocked_downloads() -> None:
    manifest, download_plan = build_source_manifest.build_source_manifest(
        created_at="2026-06-27T00:00:00+00:00"
    )
    rows = {row["source_id"]: row for row in manifest["source_rows"]}

    assert rows["dailydialog_hf"]["download_status"] == "future_local_download_conditional"
    assert rows["dailydialog_hf"]["source_license_tier"] == "public_nc_sa"
    assert rows["dailydialog_hf"]["noncommercial_only"] is True
    assert rows["dailydialog_hf"]["sharealike_required"] is True

    assert rows["empathetic_dialogues_hf"]["download_status"] == "future_local_download_conditional"
    assert rows["empathetic_dialogues_hf"]["source_license_tier"] == "public_noncommercial"
    assert rows["empathetic_dialogues_hf"]["noncommercial_only"] is True

    assert rows["lmsys_chat_1m_hf"]["admission_status"] == "blocked"
    assert rows["lmsys_chat_1m_hf"]["blocked_reason"] == (
        "raw card access returned unauthorized during 014 metadata check"
    )
    assert rows["personachat_parlai"]["admission_status"] == "blocked"
    assert rows["personachat_parlai"]["blocked_reason"] == "data license and download path not established"
    assert rows["egodesktop_gablation_009_turn2_rejected_posthoc"]["admission_status"] == "negative_evidence_only"
    assert rows["egodesktop_gablation_009_turn2_rejected_posthoc"]["future_capture_eligible"] is False
    assert rows["egodesktop_gablation_009_turn2_rejected_posthoc"]["blocked_reason"] == (
        "must never enter source manifest input rows, calibration basis, capture basis, score, or comparison"
    )

    planned_ids = {item["source_id"] for item in download_plan["planned_actions"]}
    assert planned_ids == {"dailydialog_hf", "empathetic_dialogues_hf"}
    assert all(item["action"] == "future_local_download_conditional" for item in download_plan["planned_actions"])


def test_write_artifacts_creates_hash_sidecars_without_source_cache(tmp_path: Path) -> None:
    manifest, download_plan = build_source_manifest.build_source_manifest(
        created_at="2026-06-27T00:00:00+00:00"
    )
    report = build_source_manifest.write_artifacts(tmp_path, manifest, download_plan)

    expected = {
        "SOURCE_MANIFEST.json",
        "SOURCE_MANIFEST.sha256",
        "SOURCE_DOWNLOAD_PLAN.json",
        "SOURCE_DOWNLOAD_PLAN.sha256",
        "BUILD_REPORT.json",
    }
    assert expected.issubset({path.name for path in tmp_path.iterdir()})
    assert not (tmp_path / "source_cache").exists()

    manifest_text = (tmp_path / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
    manifest_hash = (tmp_path / "SOURCE_MANIFEST.sha256").read_text(encoding="utf-8").strip()
    assert manifest_hash == build_source_manifest.sha256_text(manifest_text)
    assert report["raw_cache_created"] is False
    assert report["download_executed"] is False
    assert report["source_manifest_sha256"] == manifest_hash

    loaded = json.loads(manifest_text)
    assert loaded["download_plan_hash"] == report["source_download_plan_sha256"]
