#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))

from app.dashboard.live_api_client import DashboardLiveApiClient
from app.dashboard.live_session_export import build_live_session_export, render_live_session_export_markdown


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
DEFAULT_JSON = ARTIFACT_ROOT / "DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json"
DEFAULT_MD = ARTIFACT_ROOT / "DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one live dashboard chat session as an auditable artifact")
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    parser.add_argument("--session-id", default=None, help="Dashboard chat session id; defaults to the most recently updated session.")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--observation-source", default=None)
    return parser.parse_args()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_session_id(client: DashboardLiveApiClient, requested_session_id: str | None) -> str:
    if requested_session_id:
        return requested_session_id
    sessions_payload = client.list_sessions().payload
    sessions = list(sessions_payload.get("sessions") or [])
    if not sessions:
        raise RuntimeError("No dashboard chat sessions available.")
    sessions.sort(key=lambda item: (item.get("updated_at") or "", item.get("session_id") or ""), reverse=True)
    return str(sessions[0].get("session_id"))


def main() -> int:
    args = parse_args()
    client = DashboardLiveApiClient(base_url=args.base_url)
    session_id = _resolve_session_id(client, args.session_id)
    payload = client.get_session(session_id).payload
    report = build_live_session_export(
        payload,
        base_url=client.base_url,
        observation_source=args.observation_source,
    )
    _write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_live_session_export_markdown(report), encoding="utf-8")
    print(json.dumps(report.get("summary") or {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
