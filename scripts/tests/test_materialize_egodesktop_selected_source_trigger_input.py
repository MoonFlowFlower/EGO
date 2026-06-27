from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "materialize_egodesktop_selected_source_trigger_input.py"
spec = importlib.util.spec_from_file_location("materialize_egodesktop_selected_source_trigger_input", MODULE_PATH)
materializer = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = materializer
spec.loader.exec_module(materializer)


def test_materializer_hashes_selected_utterances_without_raw_text(tmp_path: Path) -> None:
    manifest_path, _cache_path = _write_fixture(tmp_path)

    report, user_text = materializer.materialize_trigger_input(capture_manifest_path=manifest_path)
    write_result = materializer.write_report(tmp_path / "out", report)

    assert user_text == "alpha raw text"
    assert report["raw_text_in_report"] is False
    assert report["user_text_hash"] == _trace_hash_value(user_text)
    assert report["user_text_plain_sha256"] == _sha_text(user_text)
    assert report["user_text_hash_basis"] == "EgoDesktop/src/joiRealLoopGAblationHarness.hashValue(string)"
    assert report["user_text_derivation_rule"] == "first_row_utterance_as_single_chat_turn"
    assert report["user_text_source_scope"] == "single_desktop_chat_turn"
    assert "alpha raw text" not in json.dumps(report, ensure_ascii=False)
    assert "beta raw text" not in json.dumps(report, ensure_ascii=False)
    assert write_result["trigger_input_report_sha256"] == _sha_text(
        (tmp_path / "out" / "TRIGGER_INPUT_REPORT.json").read_text(encoding="utf-8")
    )


def test_materializer_hashes_selected_wizard_post_without_raw_text(tmp_path: Path) -> None:
    manifest_path, _cache_path = _write_fixture(
        tmp_path,
        source_id="wizard_of_wikipedia_hf",
        rows=[
            {
                "row_idx": 0,
                "source_id": "wizard_of_wikipedia_hf",
                "split": "train",
                "row": {
                    "post": ["wizard prompt raw text", "wizard followup raw text"],
                    "response": ["assistant-style response raw text"],
                    "knowledge": [["knowledge raw text"]],
                    "topics": ["topic raw text"],
                },
            }
        ],
    )

    report, user_text = materializer.materialize_trigger_input(
        capture_manifest_path=manifest_path,
        selection_id="wizard_of_wikipedia_hf:train:0",
    )

    assert user_text == "wizard prompt raw text"
    assert report["raw_text_in_report"] is False
    assert report["user_text_hash"] == _trace_hash_value(user_text)
    assert report["user_text_derivation_rule"] == "first_row_post_as_single_chat_turn"
    serialized = json.dumps(report, ensure_ascii=False)
    assert "wizard prompt raw text" not in serialized
    assert "assistant-style response raw text" not in serialized
    assert "knowledge raw text" not in serialized


def test_materializer_rejects_source_cache_hash_mismatch(tmp_path: Path) -> None:
    manifest_path, _cache_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["selected_rows"][0]["source_cache_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    try:
        materializer.materialize_trigger_input(capture_manifest_path=manifest_path)
    except ValueError as exc:
        assert "source cache hash mismatch" in str(exc)
    else:
        raise AssertionError("source cache hash mismatch was not rejected")


def test_materializer_rejects_source_row_hash_mismatch(tmp_path: Path) -> None:
    manifest_path, _cache_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["selected_rows"][0]["row_content_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    try:
        materializer.materialize_trigger_input(capture_manifest_path=manifest_path)
    except ValueError as exc:
        assert "row content hash mismatch" in str(exc)
    else:
        raise AssertionError("row content hash mismatch was not rejected")


def _write_fixture(
    tmp_path: Path,
    *,
    source_id: str = "dailydialog_hf",
    rows: list[dict] | None = None,
) -> tuple[Path, Path]:
    cache_path = tmp_path / "source_cache" / source_id / "train_sample.jsonl"
    cache_path.parent.mkdir(parents=True)
    rows = rows or [
        {"row_idx": 0, "row": {"utterances": ["alpha raw text", "beta raw text"]}},
        {"row_idx": 1, "row": {"utterances": ["gamma raw text"]}},
    ]
    lines = [json.dumps(row, sort_keys=True) for row in rows]
    cache_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema": "egodesktop.joi_real_loop.capture_manifest.v0",
        "selected_rows": [
            {
                "selection_id": f"{source_id}:train:0",
                "source_id": source_id,
                "split": "train",
                "row_idx": 0,
                "source_cache_path": str(cache_path),
                "source_cache_sha256": _sha_text(cache_path.read_text(encoding="utf-8")),
                "row_content_sha256": _sha_text(lines[0]),
            }
        ],
    }
    manifest_path = tmp_path / "CAPTURE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path, cache_path


def _trace_hash_value(value: str) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
