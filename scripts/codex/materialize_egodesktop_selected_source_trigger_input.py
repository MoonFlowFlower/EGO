#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CAPTURE_MANIFEST = (
    ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_capture_manifest_v0" / "CAPTURE_MANIFEST.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "egodesktop_joi_real_loop_g_ablation_selected_source_chat_smoke_v0"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def artifact_json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def trace_hash_value(value: Any) -> str:
    return hashlib.sha256(_js_json_stringify(_stable_value(value)).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _js_json_stringify(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _stable_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_stable_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _stable_value(value[key]) for key in sorted(value)}
    return value


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def _read_jsonl_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _selected_manifest_row(manifest: dict[str, Any], selection_id: str | None) -> dict[str, Any]:
    rows = list(manifest.get("selected_rows") or [])
    if not rows:
        raise ValueError("capture manifest has no selected_rows")
    if selection_id is None:
        return rows[0]
    for row in rows:
        if str(row.get("selection_id")) == selection_id:
            return row
    raise ValueError(f"selection_id not found in capture manifest: {selection_id}")


def _derive_user_text(source_row: dict[str, Any]) -> tuple[str, str]:
    row = source_row.get("row")
    if not isinstance(row, dict):
        raise ValueError("source cache row has no row object")
    utterances = row.get("utterances")
    if isinstance(utterances, list) and all(isinstance(item, str) for item in utterances):
        for item in utterances:
            if item:
                return item, "first_row_utterance_as_single_chat_turn"
        raise ValueError("source cache row utterances are empty")
    utterance = row.get("utterance")
    if isinstance(utterance, str):
        return utterance, "single_row_utterance"
    text = row.get("text")
    if isinstance(text, str):
        return text, "single_row_text"
    posts = row.get("post")
    if isinstance(posts, list) and all(isinstance(item, str) for item in posts):
        for item in posts:
            if item:
                return item, "first_row_post_as_single_chat_turn"
        raise ValueError("source cache row post list is empty")
    raise ValueError("source cache row has no supported text field")


def materialize_trigger_input(
    *,
    capture_manifest_path: Path = DEFAULT_CAPTURE_MANIFEST,
    selection_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    manifest = load_json(capture_manifest_path)
    manifest_text = capture_manifest_path.read_text(encoding="utf-8")
    manifest_hash = sha256_text(manifest_text)
    selected = _selected_manifest_row(manifest, selection_id)

    cache_path = _resolve(str(selected["source_cache_path"]))
    cache_text = cache_path.read_text(encoding="utf-8")
    cache_hash = sha256_text(cache_text)
    expected_cache_hash = str(selected["source_cache_sha256"])
    if cache_hash != expected_cache_hash:
        raise ValueError(f"source cache hash mismatch: expected {expected_cache_hash}, got {cache_hash}")

    row_idx = int(selected["row_idx"])
    lines = _read_jsonl_lines(cache_path)
    if row_idx < 0 or row_idx >= len(lines):
        raise ValueError(f"row_idx out of range: {row_idx}")
    row_line = lines[row_idx]
    row_hash = sha256_text(row_line)
    expected_row_hash = str(selected["row_content_sha256"])
    if row_hash != expected_row_hash:
        raise ValueError(f"row content hash mismatch: expected {expected_row_hash}, got {row_hash}")

    source_row = json.loads(row_line)
    user_text, derivation_rule = _derive_user_text(source_row)
    report = {
        "schema": "egodesktop.joi_real_loop.selected_source_trigger_input.v0",
        "producer_function": "materialize_selected_source_trigger_input",
        "claim_ceiling": "selected_source_desktop_trigger_smoke_only",
        "capture_manifest": _relative(capture_manifest_path),
        "capture_manifest_sha256": manifest_hash,
        "selection_id": str(selected["selection_id"]),
        "source_id": str(selected["source_id"]),
        "split": str(selected["split"]),
        "row_idx": row_idx,
        "source_cache_path": _relative(cache_path),
        "source_cache_sha256": cache_hash,
        "row_content_sha256": row_hash,
        "user_text_derivation_rule": derivation_rule,
        "user_text_source_scope": "single_desktop_chat_turn",
        "user_text_hash": trace_hash_value(user_text),
        "user_text_hash_basis": "EgoDesktop/src/joiRealLoopGAblationHarness.hashValue(string)",
        "user_text_plain_sha256": sha256_text(user_text),
        "user_text_length": len(user_text),
        "user_text_line_count": user_text.count("\n") + 1 if user_text else 0,
        "raw_text_in_report": False,
        "desktop_trigger_required": "window.egoDesktop.sendChatTurn",
        "writer_required": "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
        "capture_authority": False,
        "scoring_authority": False,
        "runtime_authority": "explicit_smoke_only",
        "program_state_authority": False,
        "evidence_ledger_authority": False,
        "remote_authority": False,
    }
    return report, user_text


def write_report(output_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "TRIGGER_INPUT_REPORT.json"
    report_path.write_text(artifact_json_text(report), encoding="utf-8")
    report_hash = sha256_text(report_path.read_text(encoding="utf-8"))
    (output_dir / "TRIGGER_INPUT_REPORT.sha256").write_text(report_hash + "\n", encoding="utf-8")
    return {
        "trigger_input_report": _relative(report_path),
        "trigger_input_report_sha256": report_hash,
        "raw_text_in_report": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize hash-only selected-source chat trigger input.")
    parser.add_argument("--capture-manifest", type=Path, default=DEFAULT_CAPTURE_MANIFEST)
    parser.add_argument("--selection-id", default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    report, _user_text = materialize_trigger_input(
        capture_manifest_path=args.capture_manifest,
        selection_id=args.selection_id,
    )
    write_result = write_report(args.out, report)
    print(artifact_json_text(write_result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
