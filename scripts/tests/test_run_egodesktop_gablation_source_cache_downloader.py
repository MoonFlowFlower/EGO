from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "run_egodesktop_gablation_source_cache_downloader.py"
spec = importlib.util.spec_from_file_location("run_egodesktop_gablation_source_cache_downloader", MODULE_PATH)
downloader = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = downloader
spec.loader.exec_module(downloader)


def test_build_metadata_smoke_plan_only_includes_allowed_public_sources() -> None:
    manifest = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
    )
    plan = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_DOWNLOAD_PLAN.json"
    )

    actions = downloader.build_metadata_smoke_actions(manifest, plan)
    assert {action["source_id"] for action in actions} == {"dailydialog_hf", "empathetic_dialogues_hf"}
    assert all(action["url"].startswith("https://huggingface.co/datasets/") for action in actions)


def test_downloader_refuses_blocked_sources_even_if_plan_mentions_them() -> None:
    manifest = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
    )
    plan = {
        "planned_actions": [
            {
                "source_id": "lmsys_chat_1m_hf",
                "action": "future_local_download_conditional",
                "source_url": "https://huggingface.co/datasets/lmsys/lmsys-chat-1m",
            }
        ]
    }

    try:
        downloader.build_metadata_smoke_actions(manifest, plan)
    except ValueError as exc:
        assert "not admissible" in str(exc)
    else:
        raise AssertionError("blocked source was admitted")


def test_downloader_refuses_local_private_sources_even_if_plan_mentions_them() -> None:
    manifest = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
    )
    plan = {
        "planned_actions": [
            {
                "source_id": "local_egodesktop_session_context_v0",
                "action": "future_local_download_conditional",
                "source_url": "artifacts/egodesktop_session_local_conversation_context_v0/session_context_report.json",
            }
        ]
    }

    try:
        downloader.build_metadata_smoke_actions(manifest, plan)
    except ValueError as exc:
        assert "not admissible" in str(exc)
    else:
        raise AssertionError("local private source was admitted")


def test_downloader_refuses_negative_evidence_sources_even_if_plan_mentions_them() -> None:
    manifest = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
    )
    plan = {
        "planned_actions": [
            {
                "source_id": "egodesktop_gablation_009_turn2_rejected_posthoc",
                "action": "future_local_download_conditional",
                "source_url": "artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/",
            }
        ]
    }

    try:
        downloader.build_metadata_smoke_actions(manifest, plan)
    except ValueError as exc:
        assert "not admissible" in str(exc)
    else:
        raise AssertionError("negative evidence source was admitted")


def test_metadata_smoke_report_hashes_content_without_storing_raw_text(tmp_path: Path) -> None:
    actions = [
        {
            "source_id": "dailydialog_hf",
            "url": "https://huggingface.co/datasets/daily_dialog",
            "license_name": "cc-by-nc-sa-4.0",
            "source_license_tier": "public_nc_sa",
        }
    ]

    def fake_fetch(url: str) -> downloader.FetchResult:
        return downloader.FetchResult(
            url=url,
            status_code=200,
            content=b"license: cc-by-nc-sa-4.0\nraw text should not be stored",
            content_type="text/plain",
        )

    report = downloader.run_metadata_smoke(actions, fetcher=fake_fetch, created_at="2026-06-27T00:00:00+00:00")
    written = downloader.write_report(tmp_path, report)

    assert report["raw_text_stored"] is False
    assert report["download_authority"] == "metadata_only_no_raw_cache"
    assert report["results"][0]["status_code"] == 200
    assert report["results"][0]["reachable"] is True
    assert report["results"][0]["content_sha256"] == downloader.sha256_bytes(
        b"license: cc-by-nc-sa-4.0\nraw text should not be stored"
    )
    assert "raw text should not be stored" not in str(report)
    assert (tmp_path / "CACHE_SMOKE_REPORT.json").exists()
    assert (tmp_path / "CACHE_SMOKE_REPORT.sha256").exists()
    assert written["raw_text_stored"] is False


def test_metadata_smoke_records_unreachable_source_without_raw_text() -> None:
    actions = [
        {
            "source_id": "dailydialog_hf",
            "url": "https://huggingface.co/datasets/daily_dialog",
            "license_name": "cc-by-nc-sa-4.0",
            "source_license_tier": "public_nc_sa",
        }
    ]

    def fake_fetch(url: str) -> downloader.FetchResult:
        return downloader.FetchResult(
            url=url,
            status_code=404,
            content=b"not found raw body",
            content_type="text/plain",
        )

    report = downloader.run_metadata_smoke(actions, fetcher=fake_fetch, created_at="2026-06-27T00:00:00+00:00")

    assert report["results"][0]["reachable"] is False
    assert report["results"][0]["status_code"] == 404
    assert report["results"][0]["content_sha256"] == downloader.sha256_bytes(b"not found raw body")
    assert "not found raw body" not in str(report)
