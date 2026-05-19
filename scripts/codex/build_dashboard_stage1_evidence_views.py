#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
import sys

if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))

from app.dashboard.stage1_evidence import (
    build_dashboard_artifact_manifest,
    build_stage1_entrypoint_comparative_audit,
    render_dashboard_artifact_manifest_markdown,
    render_stage1_entrypoint_comparative_audit_markdown,
)


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
PREFLIGHT_PATH = ARTIFACT_ROOT / "UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.json"
DASHBOARD_LIVE_EXPORT_PATH = ARTIFACT_ROOT / "DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json"
LIVE_HISTORY_DIR = ARTIFACT_ROOT / "historical" / "reference" / "live_session_exports"
TELEGRAM_LIVE_EXPORT_PATH = ARTIFACT_ROOT / "TELEGRAM_LIVE_SESSION_EXPORT_CURRENT.json"
SUBJECT_MAINLINE_AUDIT_PATH = ARTIFACT_ROOT / "SUBJECT_MAINLINE_AUDIT_CURRENT.json"
MANIFEST_JSON_PATH = ARTIFACT_ROOT / "ARTIFACT_MANIFEST_CURRENT.json"
MANIFEST_MD_PATH = ARTIFACT_ROOT / "ARTIFACT_MANIFEST_CURRENT.md"
COMPARATIVE_JSON_PATH = ARTIFACT_ROOT / "STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.json"
COMPARATIVE_MD_PATH = ARTIFACT_ROOT / "STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.md"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _live_window_identity(report: dict[str, Any], *, artifact_path: str) -> tuple[str, str, str]:
    entrypoint = str(dict(report.get("entrypoint_contract") or {}).get("entrypoint") or "unknown")
    fetch = dict(report.get("fetch") or {})
    session = dict(report.get("session") or {})
    session_id = str(fetch.get("session_id") or session.get("session_id") or artifact_path)
    revision = str(fetch.get("session_revision") or session.get("session_revision") or report.get("generated_at") or artifact_path)
    return entrypoint, session_id, revision


def _append_live_window_report(
    rows: list[dict[str, Any]],
    seen: dict[tuple[str, str, str], int],
    *,
    path: Path,
) -> None:
    payload = _load_json(path)
    if payload is None:
        return
    artifact_path = _display_path(path)
    identity = _live_window_identity(payload, artifact_path=artifact_path)
    item = {
        "artifact_path": artifact_path,
        "report": payload,
    }
    existing_index = seen.get(identity)
    if existing_index is not None:
        rows.pop(existing_index)
        for key, index in list(seen.items()):
            if index > existing_index:
                seen[key] = index - 1
    rows.append(item)
    seen[identity] = len(rows) - 1


def _dashboard_history_export_paths() -> list[Path]:
    if not LIVE_HISTORY_DIR.exists():
        return []
    return sorted(
        path
        for path in LIVE_HISTORY_DIR.glob("DASHBOARD_LIVE_SESSION_EXPORT_*.json")
        if "PREVIOUS_" not in path.name
    )


def _collect_live_window_reports() -> list[dict[str, Any]]:
    live_window_reports: list[dict[str, Any]] = []
    seen: dict[tuple[str, str, str], int] = {}
    for path in _dashboard_history_export_paths():
        _append_live_window_report(live_window_reports, seen, path=path)
    for path in (DASHBOARD_LIVE_EXPORT_PATH, TELEGRAM_LIVE_EXPORT_PATH):
        _append_live_window_report(live_window_reports, seen, path=path)
    return live_window_reports


def main() -> int:
    manifest = build_dashboard_artifact_manifest(ARTIFACT_ROOT)
    _write_json(MANIFEST_JSON_PATH, manifest)
    MANIFEST_MD_PATH.write_text(render_dashboard_artifact_manifest_markdown(manifest), encoding="utf-8")

    live_window_reports = _collect_live_window_reports()

    comparative = build_stage1_entrypoint_comparative_audit(
        preflight_report=_load_json(PREFLIGHT_PATH),
        preflight_artifact=str(PREFLIGHT_PATH.relative_to(ROOT)).replace("\\", "/") if PREFLIGHT_PATH.exists() else None,
        live_window_reports=live_window_reports,
        subject_mainline_audit=_load_json(SUBJECT_MAINLINE_AUDIT_PATH),
        subject_mainline_artifact=(
            str(SUBJECT_MAINLINE_AUDIT_PATH.relative_to(ROOT)).replace("\\", "/")
            if SUBJECT_MAINLINE_AUDIT_PATH.exists()
            else None
        ),
    )
    _write_json(COMPARATIVE_JSON_PATH, comparative)
    COMPARATIVE_MD_PATH.write_text(render_stage1_entrypoint_comparative_audit_markdown(comparative), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "pass",
                "manifest_legacy_file_count": manifest.get("legacy_file_count"),
                "comparative_verdict": ((comparative.get("evidence_ladder") or {}).get("comparative_audit") or {}).get("verdict"),
                "live_entrypoints": ((comparative.get("evidence_ladder") or {}).get("single_entry_live_windows") or {}).get("entrypoints_observed"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
