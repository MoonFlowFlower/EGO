from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import codex_session_guard


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def test_git_readback_reports_identity() -> None:
    result = codex_session_guard.git_readback(ROOT)
    assert result["branch"]
    assert len(result["head"]) == 40
    assert result["repo_root"] == str(ROOT.resolve())


def test_bootstrap_and_closeout_are_v2_only(monkeypatch, tmp_path: Path) -> None:
    mirror = {"verdict": "pass", "errors": []}
    stale = {"verdict": "pass", "findings": []}
    monkeypatch.setattr(codex_session_guard, "_product_checks", lambda root, itl: (mirror, stale))
    bootstrap = codex_session_guard.build_bootstrap_snapshot(ROOT)
    assert bootstrap["verdict"] == "pass"
    assert "product_axis_mirror" in bootstrap
    assert "route_guard_readback" not in bootstrap


def test_closeout_rejects_path_outside_exact_scope(monkeypatch, tmp_path: Path) -> None:
    scope = tmp_path / "scope.json"
    scope.write_text(json.dumps({"exact_non_deletion_paths": ["allowed.py"], "deletion_rules": []}), encoding="utf-8")
    monkeypatch.setattr(codex_session_guard, "build_bootstrap_snapshot", lambda *a, **k: {"errors": [], "git": {}, "verdict": "pass"})
    monkeypatch.setattr(codex_session_guard, "_changed_paths", lambda root, cached: [] if cached else ["outside.py"])
    result = codex_session_guard.build_closeout_check(ROOT, mutation_scope=scope)
    assert result["verdict"] == "fail"
    assert result["outside_scope"] == ["outside.py"]


def test_pinned_itl_object_fixture_is_independent_of_worktree(tmp_path: Path) -> None:
    itl = tmp_path / "itl"
    itl.mkdir()
    _git(itl, "init", "-q")
    _git(itl, "config", "user.email", "test@example.invalid")
    _git(itl, "config", "user.name", "test")
    path = itl / "axis.json"
    raw = b'{"value":1}\n'
    path.write_bytes(raw)
    _git(itl, "add", "axis.json")
    _git(itl, "commit", "-qm", "axis")
    commit = _git(itl, "rev-parse", "HEAD")
    blob = _git(itl, "rev-parse", f"{commit}:axis.json")
    path.write_text('{"value":999}\n', encoding="utf-8")
    assert _git(itl, "cat-file", "-p", blob) == '{"value":1}'
    assert hashlib.sha256(raw).hexdigest()
