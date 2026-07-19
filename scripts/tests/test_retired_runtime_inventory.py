from __future__ import annotations

from pathlib import Path
import subprocess

from scripts.codex.retired_runtime_inventory import (
    build_retirement_manifest,
    inventory_untracked_retired_files,
    move_preserved_untracked_roots,
    scan_current_legacy_callers,
    select_retired_paths,
    verify_manifest_recoverable,
    verify_preserved_untracked_inventory,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout.strip()


def test_manifest_expands_exact_paths_and_tag_recovers_bytes(tmp_path: Path) -> None:
    (tmp_path / "EgoOperator").mkdir()
    (tmp_path / "EgoDesktop").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "EgoOperator" / "agent_base.py").write_text("VALUE = 1\n")
    (tmp_path / "EgoDesktop" / "main.js").write_text("module.exports = 1;\n")
    (tmp_path / "scripts" / "run_ego_experience_trial.py").write_text(
        "from EgoOperator.agent_base import VALUE\n"
    )
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "test")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "before")
    _git(tmp_path, "tag", "ego-pre-v2-only-mainline-test")

    paths = select_retired_paths(tmp_path, ref="ego-pre-v2-only-mainline-test")
    assert paths == (
        "EgoDesktop/main.js",
        "EgoOperator/agent_base.py",
        "scripts/run_ego_experience_trial.py",
    )
    manifest = build_retirement_manifest(
        tmp_path,
        tag="ego-pre-v2-only-mainline-test",
        task_id="TEST",
    )
    assert [row["path"] for row in manifest["removed_paths"]] == list(paths)
    assert all(
        {"mode", "object_oid", "sha256", "legacy_import_or_caller_hits", "rollback", "claim_boundary"}.issubset(row)
        for row in manifest["removed_paths"]
    )
    assert manifest["caller_inventory"]
    assert verify_manifest_recoverable(tmp_path, manifest).verdict == "pass"


def test_current_legacy_caller_scan_rejects_import(tmp_path: Path) -> None:
    (tmp_path / "current.py").write_text("from EgoOperator import agent_base\n")
    findings = scan_current_legacy_callers(tmp_path)
    assert findings
    assert findings[0]["path"] == "current.py"


def test_untracked_retired_files_are_hashed_and_moved_outside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    quarantine = tmp_path / "quarantine"
    (repo / "EgoOperator").mkdir(parents=True)
    tracked = repo / "EgoOperator" / "tracked.py"
    untracked = repo / "EgoOperator" / "local.jsonl"
    tracked.write_text("tracked\n", encoding="utf-8")
    untracked.write_text("local\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "add", "EgoOperator/tracked.py")
    _git(repo, "commit", "-m", "tracked")
    inventory = inventory_untracked_retired_files(repo, quarantine_root=quarantine, tracked_ref="HEAD")
    assert inventory["file_count"] == 1
    tracked.unlink()
    result = move_preserved_untracked_roots(repo, inventory)
    assert result["verdict"] == "pass"
    assert not (repo / "EgoOperator").exists()
    assert (quarantine / "EgoOperator/local.jsonl").read_text(encoding="utf-8") == "local\n"
    verification = verify_preserved_untracked_inventory(repo, inventory)
    assert verification["verdict"] == "pass"
    (quarantine / "EgoOperator/local.jsonl").write_text("changed\n", encoding="utf-8")
    assert verify_preserved_untracked_inventory(repo, inventory)["verdict"] == "fail"
