from __future__ import annotations

import copy
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex.verify_ego_v2_linked_worktree_retirement_001a import (
    CARD_SHA256,
    TASK_ID,
    V2_HEAD,
    V2_TREE,
    aggregate_checks,
    collect_changed_paths,
    expected_authority,
    find_path_matches,
    parse_worktree_porcelain,
    validate_authority_shape,
    validate_bundle_binding,
    validate_card_binding,
)
from scripts.codex import verify_ego_v2_linked_worktree_retirement_001a as retirement


def test_retirement_aggregator_is_fail_closed() -> None:
    assert aggregate_checks({"ok": True}) == {"verdict": "pass", "failed_checks": []}
    assert aggregate_checks({"ok": True, "hostile": False}) == {
        "verdict": "fail",
        "failed_checks": ["hostile"],
    }
    with pytest.raises(ValueError, match="boolean computed check"):
        aggregate_checks({"forged": {"value": True}})


def test_r2_card_binding_is_exact_and_fail_closed() -> None:
    assert CARD_SHA256 == "0fef18a8a25483f2ff703dcf7a4a35841449ca4b11cf0ac3c087fdafbc63c043"
    assert validate_card_binding(CARD_SHA256) == []
    assert validate_card_binding("0" * 64) == ["retirement_card_sha256_mismatch"]


def test_itl_path_scanner_casefolds_and_normalizes_separators() -> None:
    target = "D:/Project/AIProject/MyProject/Ego-v2-product-first-001a"
    assert find_path_matches({"path": "safe"}, target) == []
    slash = find_path_matches({"path": target.upper()}, target)
    backslash = find_path_matches({"path": target.replace("/", "\\")}, target)
    assert len(slash) == 1
    assert len(backslash) == 1


def test_worktree_parser_preserves_registered_branch_and_head() -> None:
    parsed = parse_worktree_porcelain(
        [
            "worktree D:/Project/AIProject/MyProject/Ego",
            "HEAD a" * 1,
            "branch refs/heads/main",
            "",
            "worktree D:/Project/AIProject/MyProject/Ego-v2-product-first-001a",
            f"HEAD {V2_HEAD}",
            "branch refs/heads/codex/ego-v2-product-first-001a",
            "",
        ]
    )
    assert len(parsed) == 2
    assert parsed[1]["HEAD"] == V2_HEAD
    assert parsed[1]["branch"] == "refs/heads/codex/ego-v2-product-first-001a"


def test_status_probe_enables_windows_long_paths(monkeypatch, tmp_path: Path) -> None:
    captured: list[str] = []

    def fake_git(_repo: Path, *args: str):
        captured.extend(args)
        return {"stdout": [], "stderr": [], "exit_code": 0, "command": ["git"]}

    monkeypatch.setattr(retirement, "_git", fake_git)

    paths, _ = retirement._status_paths(tmp_path)  # noqa: SLF001

    assert paths == []
    assert captured[:2] == ["-c", "core.longpaths=true"]


def test_changed_path_collector_includes_required_ignored_evidence(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("*.txt\n", encoding="utf-8")
    (tmp_path / "tracked.md").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "tracked.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.md").write_text("after\n", encoding="utf-8")
    (tmp_path / "claim_ceiling.txt").write_text("bounded\n", encoding="utf-8")

    paths, _status, ignored_required = collect_changed_paths(
        tmp_path, ["tracked.md", "claim_ceiling.txt"]
    )

    assert paths == ["claim_ceiling.txt", "tracked.md"]
    assert ignored_required == ["claim_ceiling.txt"]


def test_bundle_binding_hostile_controls_reject_hash_ref_and_tree_drift() -> None:
    receipt = {
        "verdict": "pass",
        "bundle": {"sha256": "a" * 64, "bytes": 17},
        "reconstructed_head": V2_HEAD,
        "reconstructed_tree": V2_TREE,
    }
    assert validate_bundle_binding(receipt, actual_sha256="a" * 64, actual_bytes=17) == []
    assert "bundle_sha256_mismatch" in validate_bundle_binding(
        receipt, actual_sha256="b" * 64, actual_bytes=17
    )
    wrong_head = copy.deepcopy(receipt)
    wrong_head["reconstructed_head"] = "0" * 40
    assert "reconstructed_head_mismatch" in validate_bundle_binding(
        wrong_head, actual_sha256="a" * 64, actual_bytes=17
    )
    wrong_tree = copy.deepcopy(receipt)
    wrong_tree["reconstructed_tree"] = "0" * 40
    assert "reconstructed_tree_mismatch" in validate_bundle_binding(
        wrong_tree, actual_sha256="a" * 64, actual_bytes=17
    )


def test_branch_bundle_authority_shape_is_exact_and_runtime_neutral() -> None:
    bundle = {
        "path": "D:/external/EGO-V2-ROLLBACK-722a9cd1.bundle",
        "bytes": 79,
        "sha256": "c" * 64,
    }
    authority = expected_authority(bundle)
    assert validate_authority_shape(authority, bundle) == []
    assert authority["worktree"] is None
    assert authority["worktree_registered"] is False
    assert authority["retention_mode"] == "BRANCH_REF_PLUS_VERIFIED_EXTERNAL_BUNDLE"
    assert authority["retirement_task_id"] == TASK_ID

    stale = copy.deepcopy(authority)
    stale["worktree"] = "D:/Project/AIProject/MyProject/Ego-v2-product-first-001a"
    assert validate_authority_shape(stale, bundle) == [
        "linked_v2_rollback_reference_mismatch"
    ]
