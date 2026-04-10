from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import re
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from app.repo_paths import get_repo_root


ALLOWED_RUNTIME_DIRTY_PATHS = {
    "EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json",
    "EgoCore/logs/egocore_err.log",
    "EgoCore/logs/egocore_run.log",
    "EgoCore/logs/telegram_launcher_meta.json",
}

ALLOWED_RUNTIME_DIRTY_PATTERNS = [
    "OpenEmotion/artifacts/mvp19/**/formal_selfhood_integration/openemotion/selfhood_integration_revisions.jsonl",
    "OpenEmotion/artifacts/mvp19/**/formal_selfhood_integration/openemotion/selfhood_integration_state.json",
    "OpenEmotion/artifacts/mvp21/**/formal_initiative_realization/openemotion/initiative_realization_revisions.jsonl",
    "OpenEmotion/artifacts/mvp21/**/formal_initiative_realization/openemotion/initiative_realization_state.json",
]


def _repo_root() -> Path:
    return get_repo_root()


def _default_report_path(process_kind: str) -> Path:
    root = _repo_root()
    return root / "EgoCore" / "artifacts" / "proto_self_v2" / f"LIVE_{process_kind.upper()}_PROCESS_VERSION.json"


def _run_git(repo_root: Path, args: Iterable[str]) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except Exception:
        fallback = _run_git_via_wsl(repo_root, args)
        return fallback
    if result.returncode != 0:
        return _run_git_via_wsl(repo_root, args)
    value = result.stdout.strip()
    return value or None


def _windows_to_wsl_path(path: str) -> Optional[str]:
    normalized = path.replace("\\", "/")
    match = re.match(r"^([A-Za-z]):/(.*)$", normalized)
    if not match:
        return None
    drive = match.group(1).lower()
    remainder = match.group(2)
    return f"/mnt/{drive}/{remainder}"


def _looks_like_wsl_worktree(repo_root: Path) -> bool:
    try:
        git_file = repo_root / ".git"
        if not git_file.exists() or git_file.is_dir():
            return False
        payload = git_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return "/mnt/" in payload


def _run_git_via_wsl(repo_root: Path, args: Iterable[str]) -> Optional[str]:
    if os.name != "nt":
        return None
    if not _looks_like_wsl_worktree(repo_root):
        return None
    wsl_repo_root = _windows_to_wsl_path(str(repo_root))
    if not wsl_repo_root:
        return None
    try:
        result = subprocess.run(
            ["wsl.exe", "git", "-C", wsl_repo_root, *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except Exception:
        return None
    value = result.stdout.strip()
    return value or None


def _parse_status_paths(status_porcelain: Optional[str]) -> list[str]:
    if not status_porcelain:
        return []
    rows: list[str] = []
    for line in status_porcelain.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        path = line[2:].lstrip() if len(line) > 2 else line
        rows.append(path)
    return rows


def _is_allowed_runtime_dirty_path(path: str) -> bool:
    if path in ALLOWED_RUNTIME_DIRTY_PATHS:
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in ALLOWED_RUNTIME_DIRTY_PATTERNS)


def _unexpected_dirty_paths(status_porcelain: Optional[str]) -> list[str]:
    paths = _parse_status_paths(status_porcelain)
    return [path for path in paths if not _is_allowed_runtime_dirty_path(path)]


def build_live_process_version_record(
    *,
    process_kind: str,
    argv: Optional[Iterable[str]] = None,
    cwd: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    resolved_repo_root = Path(repo_root) if repo_root is not None else _repo_root()
    status_porcelain = _run_git(resolved_repo_root, ["status", "--short"])
    unexpected_dirty_paths = _unexpected_dirty_paths(status_porcelain)
    env_flags = {
        "EGO_ENABLE_H1_CANONICAL_SHADOW": os.environ.get("EGO_ENABLE_H1_CANONICAL_SHADOW"),
        "EGO_H1_CANONICAL_SHADOW_ALLOWLIST": os.environ.get("EGO_H1_CANONICAL_SHADOW_ALLOWLIST"),
    }
    return {
        "schema_version": "egocore.live_process_version.v1",
        "observed_at": datetime.now().isoformat(),
        "process_kind": process_kind,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "python_executable": sys.executable,
        "argv": list(argv if argv is not None else sys.argv),
        "cwd": cwd or os.getcwd(),
        "repo_root": str(resolved_repo_root),
        "git_commit_sha": _run_git(resolved_repo_root, ["rev-parse", "HEAD"]),
        "git_commit_short": _run_git(resolved_repo_root, ["rev-parse", "--short", "HEAD"]),
        "git_branch": _run_git(resolved_repo_root, ["branch", "--show-current"]),
        "git_dirty": bool(unexpected_dirty_paths),
        "git_dirty_paths": unexpected_dirty_paths,
        "runtime_env_flags": env_flags,
    }


def write_live_process_version_report(
    *,
    process_kind: str,
    argv: Optional[Iterable[str]] = None,
    cwd: Optional[str] = None,
    repo_root: Optional[Path] = None,
    report_path: Optional[Path] = None,
) -> Path:
    record = build_live_process_version_record(
        process_kind=process_kind,
        argv=argv,
        cwd=cwd,
        repo_root=repo_root,
    )
    path = Path(report_path) if report_path is not None else _default_report_path(process_kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
