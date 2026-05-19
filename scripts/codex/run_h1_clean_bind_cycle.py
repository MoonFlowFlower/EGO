#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from h1_e4_sampling_common import (
    CAUSALITY_EXCLUSION_JSON,
    PREFLIGHT_REPORT_JSON,
    REPORTS_DIR,
    ROOT,
    now_iso,
    read_json,
    rel_path,
    write_json,
    write_text,
)


TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "h1-preflight-same-surface-unblock"
FILESET_PATH = TASK_DIR / "CLEAN_BIND_FILESET.json"
CAUSALITY_CLEAR_NOTE_JSON = REPORTS_DIR / "H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.json"
CAUSALITY_CLEAR_NOTE_MD = REPORTS_DIR / "H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.md"
DEFAULT_WORKTREE_PARENT = ROOT.parent / "_codex_clean_binds"
DEFAULT_WINDOWS_PYTHON = r"C:\Python313\python.exe"
DEFAULT_ALLOWLIST = "telegram:dm:preflight"
OPTIONAL_IGNORED_FILES = [
    Path("EgoCore/.env"),
]
STALE_RUNTIME_FILES = [
    Path("EgoCore/logs/egocore_run.log"),
    Path("EgoCore/logs/egocore_err.log"),
    Path("EgoCore/logs/telegram_launcher_meta.json"),
    Path("EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json"),
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a clean-bind worktree and rerun H1 E4 preflight")
    parser.add_argument(
        "--worktree-parent",
        default=str(DEFAULT_WORKTREE_PARENT),
        help="Parent directory for the temporary clean execution worktree.",
    )
    parser.add_argument(
        "--allowlist",
        default=os.environ.get("EGO_H1_CANONICAL_SHADOW_ALLOWLIST", DEFAULT_ALLOWLIST),
        help="Allowlist value for shadow H1 telemetry. This remains telemetry-only.",
    )
    parser.add_argument(
        "--windows-python",
        default=os.environ.get("EGO_WINDOWS_PYTHON", DEFAULT_WINDOWS_PYTHON),
        help="Windows Python executable to use for the Telegram poller.",
    )
    parser.add_argument(
        "--bind-timeout-seconds",
        type=int,
        default=120,
        help="Seconds to wait for the clean worktree live process version report.",
    )
    return parser.parse_args()


def _run(
    command: List[str],
    *,
    cwd: Path | None = None,
    env: Dict[str, str] | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    return completed


def _read_json_file(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _wsl_to_windows(path: Path) -> str:
    return _run(["wslpath", "-w", str(path)], check=True).stdout.strip()


def _git(args: Iterable[str], *, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=cwd, check=check)


def _load_fileset() -> List[Path]:
    payload = read_json(FILESET_PATH)
    return [Path(item) for item in payload.get("files", [])]


def _copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _sync_fileset(*, source_root: Path, target_root: Path, fileset: List[Path]) -> None:
    for relative_path in fileset:
        src = source_root / relative_path
        if not src.exists():
            raise FileNotFoundError(f"clean-bind source file missing: {src}")
        _copy_file(src, target_root / relative_path)


def _sync_optional_ignored_files(*, source_root: Path, target_root: Path) -> List[str]:
    copied: List[str] = []
    for relative_path in OPTIONAL_IGNORED_FILES:
        src = source_root / relative_path
        if not src.exists():
            continue
        _copy_file(src, target_root / relative_path)
        copied.append(str(relative_path).replace("\\", "/"))
    return copied


def _purge_stale_runtime_files(*, worktree_root: Path) -> None:
    for relative_path in STALE_RUNTIME_FILES:
        path = worktree_root / relative_path
        if not path.exists():
            continue
        path.unlink()


def _timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _create_worktree(*, parent: Path) -> tuple[Path, str]:
    stamp = _timestamp_slug()
    branch_name = f"codex/h1-clean-bind-{stamp}"
    worktree_path = parent / f"ego_h1_clean_bind_{stamp}"
    parent.mkdir(parents=True, exist_ok=True)
    _git(["worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"], cwd=ROOT)
    return worktree_path, branch_name


def _commit_fileset(*, worktree_root: Path, fileset: List[Path]) -> str:
    add_paths = [str(path).replace("\\", "/") for path in fileset]
    _git(["add", "--", *add_paths], cwd=worktree_root)
    status = _git(["status", "--short", "--untracked-files=no"], cwd=worktree_root).stdout.strip()
    if status:
        _git(
            [
                "-c",
                "user.name=Codex",
                "-c",
                "user.email=codex@example.invalid",
                "commit",
                "--no-verify",
                "-m",
                "temp(h1): clean bind execution slice",
            ],
            cwd=worktree_root,
        )
    return _git(["rev-parse", "--short", "HEAD"], cwd=worktree_root).stdout.strip()


def _list_telegram_pids() -> List[str]:
    script = r"""
$ErrorActionPreference = "SilentlyContinue"
Get-CimInstance Win32_Process |
  Where-Object {
    $_.CommandLine -and
    $_.CommandLine -match '(^|\\)(python|py)(\.exe)?' -and
    (
      ($_.CommandLine -match '(^|\s)-m\s+app\.main(\s|$)' -and $_.CommandLine -match '(^|\s)--telegram(\s|$)') -or
      ($_.CommandLine -match 'app[\\/]main\.py' -and $_.CommandLine -match '(^|\s)--telegram(\s|$)')
    )
  } |
  Select-Object -ExpandProperty ProcessId
"""
    completed = _run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _stop_telegram_processes() -> List[str]:
    pids = _list_telegram_pids()
    for pid in pids:
        _run(["cmd.exe", "/c", f"taskkill /PID {pid} /T /F >NUL 2>&1"], check=False)
    deadline = time.time() + 20
    while time.time() < deadline:
        remaining = _list_telegram_pids()
        if not remaining:
            return pids
        time.sleep(1)
    return pids


def _start_worktree_telegram(
    *,
    worktree_root: Path,
    allowlist: str,
    windows_python: str,
) -> str:
    live_version_path = worktree_root / "EgoCore" / "artifacts" / "proto_self_v2" / "LIVE_TELEGRAM_PROCESS_VERSION.json"
    if live_version_path.exists():
        live_version_path.unlink()
    windows_repo_root = _wsl_to_windows(worktree_root)
    git_dir = _git(["rev-parse", "--git-dir"], cwd=worktree_root).stdout.strip()
    windows_git_dir = _wsl_to_windows(Path(git_dir))
    start_script = _wsl_to_windows(ROOT / "scripts" / "start_egocore_telegram_windows.ps1")
    ps_script = f"""
$ErrorActionPreference = "Stop"
$env:EGO_ENABLE_H1_CANONICAL_SHADOW = "true"
$env:EGO_H1_CANONICAL_SHADOW_ALLOWLIST = "{allowlist}"
$env:EGO_ALLOW_GIT_WORKTREE_ROOT = "1"
$env:EGO_REPO_ROOT = "{windows_repo_root}"
$env:EGO_WINDOWS_PYTHON = "{windows_python}"
$env:GIT_DIR = "{windows_git_dir}"
$env:GIT_WORK_TREE = "{windows_repo_root}"
& "{start_script}"
"""
    completed = _run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=True,
    )
    pid = completed.stdout.strip().splitlines()[-1].strip()
    if not pid:
        raise RuntimeError("clean-bind start script returned no PID")
    return pid


def _wait_for_live_bind(
    *,
    worktree_root: Path,
    expected_commit: str,
    timeout_seconds: int,
    started_after: float,
) -> Dict[str, Any]:
    live_path = worktree_root / "EgoCore" / "artifacts" / "proto_self_v2" / "LIVE_TELEGRAM_PROCESS_VERSION.json"
    stdout_log = worktree_root / "EgoCore" / "logs" / "egocore_run.log"
    stderr_log = worktree_root / "EgoCore" / "logs" / "egocore_err.log"
    launcher_meta = worktree_root / "EgoCore" / "logs" / "telegram_launcher_meta.json"
    deadline = time.time() + timeout_seconds
    last_payload: Dict[str, Any] = {}
    while time.time() < deadline:
        if live_path.exists():
            last_payload = _read_json_file(live_path)
            observed_ts = last_payload.get("observed_at")
            parsed_observed = None
            if isinstance(observed_ts, str):
                try:
                    parsed_observed = datetime.fromisoformat(observed_ts.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    parsed_observed = None
            if (
                last_payload.get("process_kind") == "telegram"
                and last_payload.get("git_commit_short") == expected_commit
                and last_payload.get("git_dirty") is False
                and str(last_payload.get("repo_root") or "").replace("\\", "/").lower()
                == str(_wsl_to_windows(worktree_root)).replace("\\", "/").lower()
                and (
                    parsed_observed is None
                    or parsed_observed >= (started_after - 5)
                )
            ):
                return {
                    "status": "ready",
                    "live_process_version_path": str(live_path).replace("\\", "/"),
                    "live_process_version": last_payload,
                    "stdout_log": str(stdout_log).replace("\\", "/"),
                    "stderr_log": str(stderr_log).replace("\\", "/"),
                    "launcher_meta": str(launcher_meta).replace("\\", "/"),
                }
        time.sleep(2)

    return {
        "status": "timeout",
        "live_process_version_path": str(live_path).replace("\\", "/"),
        "live_process_version": last_payload,
        "stdout_log": str(stdout_log).replace("\\", "/"),
        "stderr_log": str(stderr_log).replace("\\", "/"),
        "launcher_meta": str(launcher_meta).replace("\\", "/"),
        "stdout_tail": stdout_log.read_text(encoding="utf-8", errors="ignore")[-2000:] if stdout_log.exists() else "",
        "stderr_tail": stderr_log.read_text(encoding="utf-8", errors="ignore")[-2000:] if stderr_log.exists() else "",
        "launcher_meta_payload": _read_json_file(launcher_meta) if launcher_meta.exists() else {},
    }


def _pid_alive(pid: str) -> bool:
    completed = _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
        ],
        check=False,
    )
    return completed.returncode == 0


def _run_preflight_against_worktree(worktree_root: Path) -> Dict[str, Any]:
    preflight_script = ROOT / "scripts" / "codex" / "run_h1_e4_sampling_preflight.py"
    completed = _run(
        [sys.executable, str(preflight_script), "--repo-root", str(worktree_root)],
        cwd=ROOT,
        check=False,
    )
    if not PREFLIGHT_REPORT_JSON.exists():
        raise RuntimeError(
            "preflight did not generate H1_E4_PREFLIGHT_CURRENT.json\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    payload = read_json(PREFLIGHT_REPORT_JSON)
    payload["preflight_command"] = {
        "command": f"{sys.executable} {preflight_script} --repo-root {worktree_root}",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    return payload


def build_causality_clear_payload(
    *,
    previous_exclusion: Dict[str, Any],
    new_preflight: Dict[str, Any],
    worktree_root: Path,
    worktree_branch: str,
    worktree_head_short: str,
    mirrored_files: List[str],
    optional_files: List[str],
    stopped_pids: List[str],
    started_pid: str,
) -> Dict[str, Any]:
    previous_records = {
        record["surface"]: record["category"]
        for record in previous_exclusion.get("surface_classification", {}).get("records", [])
    }
    current_records = {
        record["surface"]: record["category"]
        for record in new_preflight.get("surface_classification", {}).get("records", [])
    }
    transitions = []
    for surface in ["native_loop", "runtime_observation"]:
        transitions.append(
            {
                "surface": surface,
                "before": previous_records.get(surface, "unknown"),
                "after": current_records.get(surface, "unknown"),
            }
        )

    return {
        "schema_version": "h1_e4.causality_clear_note.v1",
        "generated_at": now_iso(),
        "task_slug": "h1-preflight-same-surface-unblock",
        "previous_exclusion_ref": rel_path(CAUSALITY_EXCLUSION_JSON),
        "new_preflight_ref": rel_path(PREFLIGHT_REPORT_JSON),
        "worktree_root": str(worktree_root).replace("\\", "/"),
        "worktree_branch": worktree_branch,
        "worktree_head_git_commit_short": worktree_head_short,
        "mirrored_files": mirrored_files,
        "optional_ignored_files": optional_files,
        "stopped_telegram_pids": stopped_pids,
        "started_telegram_pid": started_pid,
        "started_pid_alive": _pid_alive(started_pid),
        "surface_transition": transitions,
        "clean_bind_ready": bool(new_preflight.get("clean_bind_ready")),
        "live_process_ok": bool(new_preflight.get("live_process_ok")),
        "decision": (
            "sampling_path_cleared"
            if new_preflight.get("decision") == "continue"
            else "sampling_path_not_cleared"
        ),
        "no_live_h1_decision_promotion": True,
        "no_sampling_resumed": True,
        "claim_ceiling": "preflight_clean_only",
    }


def render_causality_clear_markdown(payload: Dict[str, Any]) -> str:
    transition_rows = "\n".join(
        f"| `{item['surface']}` | `{item['before']}` | `{item['after']}` |"
        for item in payload.get("surface_transition", [])
    )
    mirrored_rows = "\n".join(f"- `{item}`" for item in payload.get("mirrored_files", [])) or "- none"
    optional_rows = "\n".join(f"- `{item}`" for item in payload.get("optional_ignored_files", [])) or "- none"
    return f"""# H1 E4 Causality Clear Note

- generated_at: `{payload['generated_at']}`
- decision: `{payload['decision']}`
- worktree_root: `{payload['worktree_root']}`
- worktree_branch: `{payload['worktree_branch']}`
- worktree_head_git_commit_short: `{payload['worktree_head_git_commit_short']}`
- started_telegram_pid: `{payload['started_telegram_pid']}`
- started_pid_alive: `{payload['started_pid_alive']}`
- clean_bind_ready: `{payload['clean_bind_ready']}`
- live_process_ok: `{payload['live_process_ok']}`
- no_live_h1_decision_promotion: `{payload['no_live_h1_decision_promotion']}`
- no_sampling_resumed: `{payload['no_sampling_resumed']}`

## Surface Transition

| surface | before | after |
|---|---|---|
{transition_rows}

## Mirrored Fileset

{mirrored_rows}

## Optional Ignored Files

{optional_rows}

## Conclusion

- This note only proves the formal sampling path is no longer contaminated at preflight level.
- It does not prove runtime efficacy.
- It does not resume E4 shadow sampling.
- It does not upgrade repo-level state.
"""


def main() -> int:
    args = _parse_args()
    fileset = _load_fileset()
    previous_exclusion = read_json(CAUSALITY_EXCLUSION_JSON)
    worktree_root, worktree_branch = _create_worktree(parent=Path(args.worktree_parent).resolve())
    mirrored_files = [str(path).replace("\\", "/") for path in fileset]
    optional_files: List[str] = []
    stopped_pids: List[str] = []
    started_pid = ""

    try:
        _sync_fileset(source_root=ROOT, target_root=worktree_root, fileset=fileset)
        optional_files = _sync_optional_ignored_files(source_root=ROOT, target_root=worktree_root)
        _purge_stale_runtime_files(worktree_root=worktree_root)
        worktree_head_short = _commit_fileset(worktree_root=worktree_root, fileset=fileset)
        stopped_pids = _stop_telegram_processes()
        started_at = time.time()
        started_pid = _start_worktree_telegram(
            worktree_root=worktree_root,
            allowlist=args.allowlist,
            windows_python=args.windows_python,
        )
        bind_status = _wait_for_live_bind(
            worktree_root=worktree_root,
            expected_commit=worktree_head_short,
            timeout_seconds=args.bind_timeout_seconds,
            started_after=started_at,
        )
        if bind_status["status"] != "ready":
            raise RuntimeError(
                "clean-bind live process version was not ready within timeout\n"
                f"{json.dumps(bind_status, ensure_ascii=False, indent=2)}"
            )

        new_preflight = _run_preflight_against_worktree(worktree_root)
        payload = build_causality_clear_payload(
            previous_exclusion=previous_exclusion,
            new_preflight=new_preflight,
            worktree_root=worktree_root,
            worktree_branch=worktree_branch,
            worktree_head_short=worktree_head_short,
            mirrored_files=mirrored_files,
            optional_files=optional_files,
            stopped_pids=stopped_pids,
            started_pid=started_pid,
        )
        write_json(CAUSALITY_CLEAR_NOTE_JSON, payload)
        write_text(CAUSALITY_CLEAR_NOTE_MD, render_causality_clear_markdown(payload))

        if new_preflight.get("decision") != "continue":
            raise RuntimeError(
                "clean-bind preflight did not clear the sampling path\n"
                f"{json.dumps(new_preflight, ensure_ascii=False, indent=2)}"
            )

        print(f"worktree_root={worktree_root}")
        print(f"worktree_branch={worktree_branch}")
        print(f"started_telegram_pid={started_pid}")
        print(f"preflight_decision={new_preflight.get('decision')}")
        print(f"causality_clear_json={rel_path(CAUSALITY_CLEAR_NOTE_JSON)}")
        print(f"causality_clear_md={rel_path(CAUSALITY_CLEAR_NOTE_MD)}")
        return 0
    except Exception:
        if started_pid:
            _run(["cmd.exe", "/c", f"taskkill /PID {started_pid} /T /F >NUL 2>&1"], check=False)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
