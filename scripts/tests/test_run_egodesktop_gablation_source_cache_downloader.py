from __future__ import annotations

import io
import importlib.util
import sys
import tarfile
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
    assert {action["source_id"] for action in actions} == {
        "dailydialog_hf",
        "empathetic_dialogues_hf",
        "wizard_of_wikipedia_hf",
    }
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


def test_build_raw_cache_actions_includes_only_public_candidate_sources() -> None:
    manifest = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_MANIFEST.json"
    )
    plan = downloader.load_json(
        ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_source_manifest_v0" / "SOURCE_DOWNLOAD_PLAN.json"
    )

    actions = downloader.build_raw_cache_actions(manifest, plan, split="train", max_rows=2)

    assert {action["source_id"] for action in actions} == {
        "dailydialog_hf",
        "empathetic_dialogues_hf",
        "wizard_of_wikipedia_hf",
    }
    assert {action["method"] for action in actions} == {"hf_rows_api", "direct_archive_csv"}
    assert all(action["max_rows"] == 2 for action in actions)
    assert all(action["split"] == "train" for action in actions)


def test_raw_cache_sample_writes_ignored_cache_and_hash_report_without_committing_text(tmp_path: Path) -> None:
    actions = [
        {
            "source_id": "dailydialog_hf",
            "method": "hf_rows_api",
            "url": "https://datasets-server.huggingface.co/rows?dataset=roskoN/dailydialog&config=full&split=train&offset=0&length=2",
            "source_url": "https://huggingface.co/datasets/roskoN/dailydialog",
            "split": "train",
            "max_rows": 2,
            "license_name": "cc-by-nc-sa-4.0",
            "source_license_tier": "public_nc_sa",
        },
        {
            "source_id": "empathetic_dialogues_hf",
            "method": "direct_archive_csv",
            "url": "https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz",
            "archive_member": "empatheticdialogues/train.csv",
            "source_url": "https://huggingface.co/datasets/facebook/empathetic_dialogues",
            "split": "train",
            "max_rows": 2,
            "license_name": "cc-by-nc-4.0",
            "source_license_tier": "public_nc",
        },
        {
            "source_id": "wizard_of_wikipedia_hf",
            "method": "hf_rows_api",
            "url": "https://datasets-server.huggingface.co/rows?dataset=chujiezheng%2Fwizard_of_wikipedia&config=default&split=train&offset=0&length=2",
            "source_url": "https://huggingface.co/datasets/chujiezheng/wizard_of_wikipedia",
            "split": "train",
            "max_rows": 2,
            "license_name": "cc-by-nc-4.0",
            "source_license_tier": "public_noncommercial",
        },
    ]

    archive_bytes = _fake_empathetic_archive()

    def fake_fetch(url: str) -> downloader.FetchResult:
        if "dataset=roskoN%2Fdailydialog" in url or "dataset=roskoN/dailydialog" in url:
            return downloader.FetchResult(
                url=url,
                status_code=200,
                content=(
                    b'{"rows":[{"row_idx":0,"row":{"utterances":["alpha raw text"]}},'
                    b'{"row_idx":1,"row":{"utterances":["beta raw text"]}}],'
                    b'"num_rows_total":11118}'
                ),
                content_type="application/json",
            )
        if "dataset=chujiezheng%2Fwizard_of_wikipedia" in url:
            return downloader.FetchResult(
                url=url,
                status_code=200,
                content=(
                    b'{"rows":[{"row_idx":0,"row":{"post":["wizard raw prompt"],'
                    b'"response":["wizard raw response"],"topics":["science"]}},'
                    b'{"row_idx":1,"row":{"post":["wizard second prompt"],'
                    b'"response":["wizard second response"],"topics":["history"]}}],'
                    b'"num_rows_total":18430}'
                ),
                content_type="application/json",
            )
        return downloader.FetchResult(
            url=url,
            status_code=200,
            content=archive_bytes,
            content_type="application/gzip",
        )

    report = downloader.run_raw_cache_sample(
        actions,
        output_dir=tmp_path,
        fetcher=fake_fetch,
        created_at="2026-06-27T00:00:00+00:00",
    )
    written = downloader.write_raw_cache_report(tmp_path, report)

    assert report["download_authority"] == "bounded_public_raw_cache_local_only"
    assert report["raw_cache_created"] is True
    assert report["raw_text_stored"] is True
    assert report["capture_authority"] is False
    assert report["scoring_authority"] is False
    assert report["runtime_authority"] is False
    assert {result["row_count"] for result in report["results"]} == {2}
    assert "alpha raw text" not in str(report)
    assert "I felt proud" not in str(report)

    daily_cache = tmp_path / "source_cache" / "dailydialog_hf" / "train_sample.jsonl"
    empath_cache = tmp_path / "source_cache" / "empathetic_dialogues_hf" / "train_sample.jsonl"
    wizard_cache = tmp_path / "source_cache" / "wizard_of_wikipedia_hf" / "train_sample.jsonl"
    assert "alpha raw text" in daily_cache.read_text(encoding="utf-8")
    assert "I felt proud" in empath_cache.read_text(encoding="utf-8")
    assert "wizard raw prompt" in wizard_cache.read_text(encoding="utf-8")
    assert "wizard raw prompt" not in str(report)
    assert (tmp_path / "RAW_CACHE_REPORT.json").exists()
    assert (tmp_path / "RAW_CACHE_REPORT.sha256").exists()
    assert written["raw_cache_report"].endswith("RAW_CACHE_REPORT.json")
    assert written["raw_cache_created"] is True


def _fake_empathetic_archive() -> bytes:
    csv_text = (
        "conv_id,utterance_idx,context,prompt,speaker_idx,utterance,selfeval,tags\n"
        "hit:1,1,proud,Prompt one,0,I felt proud,1|1,\n"
        "hit:1,2,proud,Prompt one,1,That sounds good,1|1,\n"
    )
    stream = io.BytesIO()
    encoded = csv_text.encode("utf-8")
    with tarfile.open(fileobj=stream, mode="w:gz") as tar:
        info = tarfile.TarInfo("empatheticdialogues/train.csv")
        info.size = len(encoded)
        tar.addfile(info, io.BytesIO(encoded))
    return stream.getvalue()
