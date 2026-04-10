#!/usr/bin/env python3
from __future__ import annotations

import os
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from h1_e4_sampling_common import (
    CAUSALITY_EXCLUSION_JSON,
    CAUSALITY_EXCLUSION_MD,
    PREFLIGHT_REPORT_JSON,
    PREFLIGHT_REPORT_MD,
    ROOT,
    build_preflight_payload,
    git_dirty_paths,
    git_head_short,
    load_frozen_sample_matrix,
    load_live_process_version,
    rel_path,
    render_preflight_markdown,
    write_json,
    write_text,
)


def _run_command(
    *,
    name: str,
    command: List[str],
    cwd: Path,
    env_overrides: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "command": " ".join(command),
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "note": (completed.stderr or completed.stdout or "").strip().splitlines()[-1] if (completed.stderr or completed.stdout) else "",
    }


def run_targeted_checks(*, repo_root: Path) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    checks.append(
        _run_command(
            name="h1_shadow_kernel",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "OpenEmotion/openemotion/proto_self/tests/test_h1_shadow_canonical.py",
                "-q",
            ],
            cwd=repo_root,
            env_overrides={"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"},
        )
    )
    checks.append(
        _run_command(
            name="proto_self_runtime_bridge",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "EgoCore/tests/test_runtime_v2_proto_self_runtime.py",
                "-q",
            ],
            cwd=repo_root,
            env_overrides={"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"},
        )
    )
    checks.append(
        _run_command(
            name="telegram_evidence_collector",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "EgoCore/tests/test_telegram_evidence_collector.py",
                "EgoCore/tests/test_telegram_proto_self_v2_evidence.py",
                "-q",
            ],
            cwd=repo_root,
            env_overrides={"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"},
        )
    )
    checks.append(
        _run_command(
            name="runtime_mainline_observation",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "EgoCore/tests/test_runtime_mainline_observation.py",
                "-q",
            ],
            cwd=repo_root,
            env_overrides={"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"},
        )
    )
    checks.append(
        _run_command(
            name="native_path_surface",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "EgoCore/tests/test_native_loop.py",
                "EgoCore/tests/test_telegram_bot_native_switch.py",
                "-q",
            ],
            cwd=repo_root,
            env_overrides={"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"},
        )
    )
    checks.append(
        _run_command(
            name="repo_fast_gate",
            command=[sys.executable, "scripts/codex/verify_repo.py", "--mode", "fast"],
            cwd=repo_root,
        )
    )
    return checks


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run H1 E4 sampling preflight")
    parser.add_argument(
        "--repo-root",
        default=str(ROOT),
        help="Target repo root to evaluate. Defaults to the current repo root.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    live_process_version_path = repo_root / "EgoCore" / "artifacts" / "proto_self_v2" / "LIVE_TELEGRAM_PROCESS_VERSION.json"
    sample_matrix = load_frozen_sample_matrix()
    payload = build_preflight_payload(
        sample_matrix=sample_matrix,
        head_short=git_head_short(repo_root=repo_root),
        dirty_paths=git_dirty_paths(tracked_only=True, repo_root=repo_root),
        live_process_version=load_live_process_version(live_process_version_path),
        targeted_checks=run_targeted_checks(repo_root=repo_root),
        repo_root_ref=str(repo_root).replace("\\", "/"),
        live_process_version_ref=str(live_process_version_path).replace("\\", "/"),
    )

    if payload["report_kind"] == "causality_exclusion":
        json_path = CAUSALITY_EXCLUSION_JSON
        md_path = CAUSALITY_EXCLUSION_MD
    else:
        json_path = PREFLIGHT_REPORT_JSON
        md_path = PREFLIGHT_REPORT_MD

    write_json(json_path, payload)
    write_text(md_path, render_preflight_markdown(payload))

    print(f"decision={payload['decision']}")
    print(f"report_kind={payload['report_kind']}")
    print(f"report_json={rel_path(json_path)}")
    print(f"report_md={rel_path(md_path)}")
    return 0 if payload["decision"] == "continue" else 1


if __name__ == "__main__":
    raise SystemExit(main())
