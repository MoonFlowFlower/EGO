#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))

from app.dashboard.live_api_client import DashboardLiveApiClient
from app.dashboard.stage1_live_run import (
    build_dashboard_stage1_live_run,
    render_dashboard_stage1_live_run_markdown,
)
from app.dashboard.live_session_export import render_live_session_export_markdown


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
RUN_CURRENT_JSON = ARTIFACT_ROOT / "DASHBOARD_STAGE1_LIVE_RUN_CURRENT.json"
RUN_CURRENT_MD = ARTIFACT_ROOT / "DASHBOARD_STAGE1_LIVE_RUN_CURRENT.md"
EXPORT_CURRENT_JSON = ARTIFACT_ROOT / "DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json"
EXPORT_CURRENT_MD = ARTIFACT_ROOT / "DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.md"
RUN_HISTORY_DIR = ARTIFACT_ROOT / "historical" / "reference" / "stage1_live_runs"
EXPORT_HISTORY_DIR = ARTIFACT_ROOT / "historical" / "reference" / "live_session_exports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one autonomous dashboard-only Stage 1 live-window sample")
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--session-name", default=None)
    parser.add_argument("--wait-timeout-ms", type=int, default=15000)
    parser.add_argument("--prompt-source-strategy", default="hybrid")
    return parser.parse_args()


def _utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _copy_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _record_run_artifacts(report: dict[str, Any], *, timestamp_slug: str) -> tuple[Path, Path]:
    history_json = RUN_HISTORY_DIR / f"DASHBOARD_STAGE1_LIVE_RUN_{timestamp_slug}.json"
    history_md = RUN_HISTORY_DIR / f"DASHBOARD_STAGE1_LIVE_RUN_{timestamp_slug}.md"
    _write_json(history_json, report)
    _write_text(history_md, render_dashboard_stage1_live_run_markdown(report))
    _write_json(RUN_CURRENT_JSON, report)
    _write_text(RUN_CURRENT_MD, render_dashboard_stage1_live_run_markdown(report))
    return history_json, history_md


def _record_export_artifacts(export_report: dict[str, Any], *, timestamp_slug: str) -> tuple[Path, Path]:
    _copy_if_exists(
        EXPORT_CURRENT_JSON,
        EXPORT_HISTORY_DIR / f"DASHBOARD_LIVE_SESSION_EXPORT_PREVIOUS_{timestamp_slug}.json",
    )
    _copy_if_exists(
        EXPORT_CURRENT_MD,
        EXPORT_HISTORY_DIR / f"DASHBOARD_LIVE_SESSION_EXPORT_PREVIOUS_{timestamp_slug}.md",
    )
    history_json = EXPORT_HISTORY_DIR / f"DASHBOARD_LIVE_SESSION_EXPORT_{timestamp_slug}.json"
    history_md = EXPORT_HISTORY_DIR / f"DASHBOARD_LIVE_SESSION_EXPORT_{timestamp_slug}.md"
    _write_json(history_json, export_report)
    _write_text(history_md, render_live_session_export_markdown(export_report))
    _write_json(EXPORT_CURRENT_JSON, export_report)
    _write_text(EXPORT_CURRENT_MD, render_live_session_export_markdown(export_report))
    return history_json, history_md


def _refresh_stage1_views() -> None:
    subprocess.run(
        [sys.executable, "scripts/codex/build_dashboard_stage1_evidence_views.py"],
        cwd=ROOT,
        check=True,
    )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _is_clean_live_window(report: dict[str, Any]) -> bool:
    summary = dict(report.get("summary") or {})
    return (
        report.get("execution_verdict") == "single_entry_live_window_captured"
        and int(summary.get("host_only_count") or 0) == 0
        and int(summary.get("degraded_count") or 0) == 0
        and int(summary.get("ordinary_chat_turn_count") or 0) >= 4
        and int(summary.get("subject_gate_ok_count") or 0) == int(summary.get("assistant_turn_count") or 0)
    )


def _historical_run_reports() -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in sorted(RUN_HISTORY_DIR.glob("DASHBOARD_STAGE1_LIVE_RUN_*.json")):
        payload = _load_json(path)
        if payload is not None:
            reports.append(payload)
    return reports


def _autonomous_policy_state(current_report: dict[str, Any]) -> dict[str, Any]:
    reports = _historical_run_reports()
    clean_streak = 0
    same_blocker_streak = 0
    current_blocker = current_report.get("blocker_reason")

    for report in reversed([*reports, current_report]):
        if _is_clean_live_window(report):
            clean_streak += 1
        else:
            break

    if current_blocker:
        same_blocker_streak = 1
        for report in reversed(reports):
            if report.get("blocker_reason") == current_blocker:
                same_blocker_streak += 1
            else:
                break

    return {
        "recent_consecutive_clean_runs": clean_streak,
        "recent_same_blocker_count": same_blocker_streak,
        "dashboard_only_stability_strengthened": clean_streak >= 2,
        "stop_requested_by_same_blocker_rule": bool(current_blocker and same_blocker_streak >= 2),
        "rule": "Two consecutive clean dashboard-only runs strengthen single-entry evidence; two consecutive same blockers stop autonomous looping.",
    }


def main() -> int:
    args = parse_args()
    timestamp_slug = _utc_timestamp_slug()
    client = DashboardLiveApiClient(
        base_url=args.base_url,
        timeout=max(120.0, float(args.wait_timeout_ms) / 1000.0 + 15.0),
    )
    run_report, export_report = build_dashboard_stage1_live_run(
        client=client,
        session_name=args.session_name,
        wait_timeout_ms=args.wait_timeout_ms,
        prompt_source_strategy=args.prompt_source_strategy,
    )
    if export_report is not None:
        run_report["export_artifact_path"] = _display_path(EXPORT_CURRENT_JSON)
    run_report["autonomous_policy_state"] = _autonomous_policy_state(run_report)

    _record_run_artifacts(run_report, timestamp_slug=timestamp_slug)

    if export_report is not None:
        _record_export_artifacts(export_report, timestamp_slug=timestamp_slug)
        _refresh_stage1_views()

    print(
        json.dumps(
            {
                "execution_verdict": run_report.get("execution_verdict"),
                "blocker_reason": run_report.get("blocker_reason"),
                "session_id": run_report.get("session_id"),
                "export_artifact_path": run_report.get("export_artifact_path"),
                "prompt_source_counts": run_report.get("prompt_source_counts"),
                "prompt_pack_degraded": run_report.get("prompt_pack_degraded"),
                "summary": run_report.get("summary"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if export_report is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
