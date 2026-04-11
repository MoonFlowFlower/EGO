#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))

from app.config import load_config
from app.dashboard.chat_service import DashboardChatService
from app.dashboard.preflight import (
    DeterministicDashboardPreflightRunner,
    build_dashboard_preflight_report,
    execute_dashboard_preflight,
    render_dashboard_preflight_markdown,
)
from app.openemotion_adapter import ProtoSelfAdapter, ProtoSelfStateStore, ProtoSelfTraceBridge
from app.openemotion_hooks.subject_gate import MandatorySubjectGate
from app.runtime_v2.proto_self_runtime import RuntimeV2ProtoSelfRuntime


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
DEFAULT_OUTPUT_JSON = ARTIFACT_ROOT / "LIVE_INGRESS_DASHBOARD_PREFLIGHT_CURRENT.json"
DEFAULT_OUTPUT_MD = ARTIFACT_ROOT / "LIVE_INGRESS_DASHBOARD_PREFLIGHT_CURRENT.md"


class IsolatedDashboardPreflightHooks:
    def __init__(self, *, runtime_root: Path) -> None:
        mirror_dir = runtime_root / "proto_self_mirror"
        state_store = ProtoSelfStateStore(
            root_dir=runtime_root / "proto_self_store",
            legacy_mirror_dir=mirror_dir,
        )
        trace_bridge = ProtoSelfTraceBridge(trace_dir=runtime_root / "logs")
        adapter = ProtoSelfAdapter(
            mirror_dir=mirror_dir,
            state_store=state_store,
            trace_bridge=trace_bridge,
        )
        self.runtime = RuntimeV2ProtoSelfRuntime(
            adapter=adapter,
            trace_bridge=trace_bridge,
            evidence_collector_factory=None,
        )

    @property
    def enabled(self) -> bool:
        return True

    def process_ingress(self, **kwargs: Any) -> None:
        self.runtime.process_ingress(**kwargs)

    def process_finalized_result(self, **kwargs: Any) -> None:
        self.runtime.process_finalized_result(**kwargs)

    def capture_response_plan(self, **kwargs: Any) -> None:
        self.runtime.capture_response_plan(**kwargs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run dashboard chat preflight for live-ingress corrective tranche")
    parser.add_argument("--session-name", default="preflight-live-ingress")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def _git_short_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_repo_config() -> None:
    load_config(
        config_dir=str(ROOT / "EgoCore" / "config"),
        env_file=str(ROOT / "EgoCore" / ".env"),
        validate=False,
    )


def build_service() -> DashboardChatService:
    _load_repo_config()
    tempdir = tempfile.TemporaryDirectory(prefix="dashboard-preflight-")
    runtime_root = Path(tempdir.name)
    hooks = IsolatedDashboardPreflightHooks(runtime_root=runtime_root)
    service = DashboardChatService(
        runner=DeterministicDashboardPreflightRunner(),
        subject_gate=MandatorySubjectGate(hooks=hooks),
        llm_client_resolver=lambda: None,
    )
    setattr(service, "_dashboard_preflight_tempdir", tempdir)
    return service


def main() -> int:
    args = parse_args()
    service = build_service()
    preflight_result = execute_dashboard_preflight(service, session_name=args.session_name)
    report = build_dashboard_preflight_report(
        preflight_result,
        git_commit_short=_git_short_head(),
    )
    _write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_dashboard_preflight_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "source": report.get("source"),
                "claim_ceiling": report.get("claim_ceiling"),
                "acceptance_met": (report.get("aggregate") or {}).get("acceptance_met"),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
