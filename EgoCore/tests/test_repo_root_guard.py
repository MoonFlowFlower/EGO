from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "EgoCore" / "tools" / "repo-root-guard"


def _load_module(path: Path, name: str):
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_repo_root_guard_allows_same_common_dir_worktree_with_explicit_flag(monkeypatch):
    module = _load_module(MODULE_PATH, "repo_root_guard_worktree")
    guard = module.RepoRootGuard(repo_name="EgoCore")
    current_dir = r"D:\Project\AIProject\MyProject\_codex_clean_binds\ego_h1_clean_bind_demo\EgoCore"
    canonical_root = r"D:\Project\AIProject\MyProject\Ego\EgoCore"

    monkeypatch.setenv("EGO_ALLOW_GIT_WORKTREE_ROOT", "1")
    monkeypatch.setattr(os, "getcwd", lambda: current_dir)
    monkeypatch.setattr(
        guard.registry,
        "get_repo",
        lambda _repo_name: {
            "canonical_root": canonical_root,
            "forbidden_alternatives": [],
            "enforcement": {"auto_switch_allowed": False, "blocked_operations": ["application_startup"]},
        },
    )

    git_map = {
        (current_dir, ("rev-parse", "--show-toplevel")): r"D:\Project\AIProject\MyProject\_codex_clean_binds\ego_h1_clean_bind_demo",
        (current_dir, ("rev-parse", "--git-common-dir")): r"D:\Project\AIProject\MyProject\Ego\.git",
        (canonical_root, ("rev-parse", "--show-toplevel")): r"D:\Project\AIProject\MyProject\Ego",
        (canonical_root, ("rev-parse", "--git-common-dir")): r"D:\Project\AIProject\MyProject\Ego\.git",
    }

    monkeypatch.setattr(guard, "_run_git", lambda cwd, args: git_map.get((cwd, tuple(args))))

    result = guard.check()

    assert result.status.value == "canonical"
    assert "allowed git worktree" in result.message


def test_repo_root_guard_allows_explicit_env_worktree_root(monkeypatch):
    module = _load_module(MODULE_PATH, "repo_root_guard_env_allow")
    guard = module.RepoRootGuard(repo_name="EgoCore")
    current_dir = r"D:\Project\AIProject\MyProject\_codex_clean_binds\ego_h1_clean_bind_demo\EgoCore"
    canonical_root = r"D:\Project\AIProject\MyProject\Ego\EgoCore"
    worktree_repo_root = r"D:\Project\AIProject\MyProject\_codex_clean_binds\ego_h1_clean_bind_demo"

    monkeypatch.setenv("EGO_ALLOW_GIT_WORKTREE_ROOT", "1")
    monkeypatch.setenv("EGO_REPO_ROOT", worktree_repo_root)
    monkeypatch.setattr(os, "getcwd", lambda: current_dir)
    monkeypatch.setattr(
        guard.registry,
        "get_repo",
        lambda _repo_name: {
            "canonical_root": canonical_root,
            "forbidden_alternatives": [],
            "enforcement": {"auto_switch_allowed": False, "blocked_operations": ["application_startup"]},
        },
    )

    result = guard.check()

    assert result.status.value == "canonical"
    assert "allowed git worktree" in result.message


def test_repo_root_guard_blocks_same_worktree_without_explicit_flag(monkeypatch):
    module = _load_module(MODULE_PATH, "repo_root_guard_blocked")
    guard = module.RepoRootGuard(repo_name="EgoCore")
    current_dir = r"D:\Project\AIProject\MyProject\_codex_clean_binds\ego_h1_clean_bind_demo\EgoCore"
    canonical_root = r"D:\Project\AIProject\MyProject\Ego\EgoCore"

    monkeypatch.delenv("EGO_ALLOW_GIT_WORKTREE_ROOT", raising=False)
    monkeypatch.setattr(os, "getcwd", lambda: current_dir)
    monkeypatch.setattr(
        guard.registry,
        "get_repo",
        lambda _repo_name: {
            "canonical_root": canonical_root,
            "forbidden_alternatives": [],
            "enforcement": {"auto_switch_allowed": False, "blocked_operations": ["application_startup"]},
        },
    )

    result = guard.check()

    assert result.status.value == "wrong_repo"
    assert result.blocked_operations == ["application_startup"]
