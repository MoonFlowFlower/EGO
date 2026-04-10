import json
import os
from pathlib import Path
import subprocess

import app.live_process_version as live_process_version
from app.live_process_version import build_live_process_version_record, write_live_process_version_report


def test_build_live_process_version_record_contains_required_fields():
    os.environ["EGO_ENABLE_H1_CANONICAL_SHADOW"] = "true"
    os.environ["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] = "telegram:dm:1"
    record = build_live_process_version_record(
        process_kind="telegram",
        argv=["python", "-m", "app.main", "--telegram"],
        cwd="/tmp/demo",
        repo_root=Path(__file__).resolve().parents[2],
    )

    assert record["schema_version"] == "egocore.live_process_version.v1"
    assert record["process_kind"] == "telegram"
    assert record["argv"] == ["python", "-m", "app.main", "--telegram"]
    assert record["cwd"] == "/tmp/demo"
    assert isinstance(record["pid"], int)
    assert record["git_commit_sha"]
    assert record["git_commit_short"]
    assert record["runtime_env_flags"]["EGO_ENABLE_H1_CANONICAL_SHADOW"] == "true"
    assert record["runtime_env_flags"]["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] == "telegram:dm:1"


def test_write_live_process_version_report_writes_json(tmp_path):
    path = tmp_path / "LIVE_TELEGRAM_PROCESS_VERSION.json"
    written = write_live_process_version_report(
        process_kind="telegram",
        argv=["python", "-m", "app.main", "--telegram"],
        cwd="/tmp/demo",
        repo_root=Path(__file__).resolve().parents[2],
        report_path=path,
    )

    assert written == path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["process_kind"] == "telegram"
    assert payload["schema_version"] == "egocore.live_process_version.v1"
    assert "runtime_env_flags" in payload


def test_unexpected_dirty_paths_ignores_runtime_generated_files():
    status = "\n".join(
        [
            " M EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json",
            " M EgoCore/logs/egocore_run.log",
            " M EgoCore/logs/egocore_err.log",
            " M EgoCore/tests/test_native_loop.py",
        ]
    )

    assert live_process_version._unexpected_dirty_paths(status) == [
        "EgoCore/tests/test_native_loop.py"
    ]


def test_run_git_falls_back_to_wsl_for_windows_worktree(monkeypatch, tmp_path):
    repo_root = Path("D:/Project/AIProject/MyProject/Ego/worktree")

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "git":
            raise subprocess.CalledProcessError(1, command)
        if command[:3] == ["wsl.exe", "git", "-C"]:
            class Result:
                stdout = "abc123\n"
                returncode = 0
            return Result()
        raise AssertionError(command)

    monkeypatch.setattr(live_process_version.os, "name", "nt")
    monkeypatch.setattr(live_process_version.subprocess, "run", fake_run)
    monkeypatch.setattr(live_process_version, "_looks_like_wsl_worktree", lambda _: True)

    value = live_process_version._run_git(repo_root, ["rev-parse", "--short", "HEAD"])

    assert value == "abc123"
    assert calls[0][:2] == ["git", "-C"]
    assert calls[1][:3] == ["wsl.exe", "git", "-C"]
    assert calls[1][3] == "/mnt/d/Project/AIProject/MyProject/Ego/worktree"
