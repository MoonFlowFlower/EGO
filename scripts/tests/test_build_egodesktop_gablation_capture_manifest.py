from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "build_egodesktop_gablation_capture_manifest.py"
spec = importlib.util.spec_from_file_location("build_egodesktop_gablation_capture_manifest", MODULE_PATH)
builder = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def test_capture_manifest_selects_row_hashes_without_raw_text(tmp_path: Path) -> None:
    report_path = _write_raw_cache_fixture(tmp_path)

    manifest, build_report = builder.build_capture_manifest(
        raw_cache_report_path=report_path,
        rows_per_source=2,
        created_at="2026-06-27T00:00:00+00:00",
    )
    written = builder.write_artifacts(tmp_path / "out", manifest, build_report)

    assert manifest["claim_ceiling"] == "capture_manifest_hash_selection_only"
    assert manifest["capture_authority"] is False
    assert manifest["runtime_authority"] is False
    assert manifest["raw_text_in_manifest"] is False
    assert len(manifest["selected_rows"]) == 4
    assert {row["source_id"] for row in manifest["selected_rows"]} == {
        "dailydialog_hf",
        "empathetic_dialogues_hf",
    }
    assert all(row["desktop_trigger_required"] == "window.egoDesktop.sendChatTurn" for row in manifest["selected_rows"])
    assert all("row_content_sha256" in row for row in manifest["selected_rows"])
    assert "alpha raw text" not in json.dumps(manifest, ensure_ascii=False)
    assert "I felt proud" not in json.dumps(manifest, ensure_ascii=False)
    assert written["capture_manifest_sha256"] == _sha_text((tmp_path / "out" / "CAPTURE_MANIFEST.json").read_text())


def test_capture_manifest_rejects_cache_hash_mismatch(tmp_path: Path) -> None:
    report_path = _write_raw_cache_fixture(tmp_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["results"][0]["cache_sha256"] = "0" * 64
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    try:
        builder.build_capture_manifest(raw_cache_report_path=report_path, rows_per_source=1)
    except ValueError as exc:
        assert "cache hash mismatch" in str(exc)
    else:
        raise AssertionError("cache hash mismatch was not rejected")


def _write_raw_cache_fixture(tmp_path: Path) -> Path:
    daily_cache = tmp_path / "source_cache" / "dailydialog_hf" / "train_sample.jsonl"
    empath_cache = tmp_path / "source_cache" / "empathetic_dialogues_hf" / "train_sample.jsonl"
    daily_cache.parent.mkdir(parents=True)
    empath_cache.parent.mkdir(parents=True)
    daily_cache.write_text(
        "".join(
            [
                json.dumps({"row_idx": 0, "row": {"utterances": ["alpha raw text"]}}, sort_keys=True) + "\n",
                json.dumps({"row_idx": 1, "row": {"utterances": ["beta raw text"]}}, sort_keys=True) + "\n",
                json.dumps({"row_idx": 2, "row": {"utterances": ["gamma raw text"]}}, sort_keys=True) + "\n",
            ]
        ),
        encoding="utf-8",
    )
    empath_cache.write_text(
        "".join(
            [
                json.dumps({"row_idx": 0, "row": {"utterance": "I felt proud"}}, sort_keys=True) + "\n",
                json.dumps({"row_idx": 1, "row": {"utterance": "That sounds good"}}, sort_keys=True) + "\n",
            ]
        ),
        encoding="utf-8",
    )
    report = {
        "schema": "egodesktop.joi_real_loop.source_cache_raw_sample.v0",
        "raw_cache_created": True,
        "results": [
            {
                "source_id": "dailydialog_hf",
                "method": "hf_rows_api",
                "source_url": "https://huggingface.co/datasets/roskoN/dailydialog",
                "split": "train",
                "row_count": 3,
                "cache_path": str(daily_cache),
                "cache_sha256": _sha_text(daily_cache.read_text(encoding="utf-8")),
                "cache_written": True,
                "license_name": "cc-by-nc-sa-4.0",
                "source_license_tier": "public_nc_sa",
            },
            {
                "source_id": "empathetic_dialogues_hf",
                "method": "direct_archive_csv",
                "source_url": "https://huggingface.co/datasets/facebook/empathetic_dialogues",
                "split": "train",
                "row_count": 2,
                "cache_path": str(empath_cache),
                "cache_sha256": _sha_text(empath_cache.read_text(encoding="utf-8")),
                "cache_written": True,
                "license_name": "cc-by-nc-4.0",
                "source_license_tier": "public_noncommercial",
            },
        ],
    }
    report_path = tmp_path / "RAW_CACHE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
