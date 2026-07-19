from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from scripts.codex.product_axis import (
    load_product_axis,
    render_active_views,
    sync_pinned_itl_mirror,
    verify_pinned_itl_mirror,
)


def _git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _axis() -> dict:
    return {
        "schema_version": "itl.route_axis_state.v2",
        "authority_semantics": "SOLE_MACHINE_READABLE_PRODUCT_DEVELOPMENT_AXIS_AUTHORITY",
        "product_development_axis": {
            "authority": "SOLE",
            "authority_route_id": "V2",
            "product_mainline": True,
            "interactive_entrypoint": "scripts/run_ego_life_playground_v0.py",
            "enabled": True,
            "default_enabled": False,
            "autostart": False,
            "background_dispatch": False,
            "network": False,
            "llm": False,
            "science_weight": 0,
            "runtime_authority": "local_explicit_v2_only",
            "repository_main_placement_complete": True,
            "retired_projects": {
                "EgoOperator": "retired_from_current_tree",
                "EgoDesktop": "retired_from_current_tree",
            },
            "next_actions": ["develop_v2_in_ego_with_local_bounded_task_card"],
            "claim_ceiling": "local explicit V2 product entry and evidence hygiene only",
        },
    }


def test_verify_mirror_reads_pinned_git_object_not_dirty_source_worktree(tmp_path: Path) -> None:
    itl = tmp_path / "itl"
    ego = tmp_path / "ego"
    itl.mkdir()
    (itl / "artifacts" / "ROUTE-STATE-MACHINE-001A").mkdir(parents=True)
    _git(itl, "init")
    _git(itl, "config", "user.name", "test")
    _git(itl, "config", "user.email", "test@example.invalid")
    source_path = "artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json"
    raw = (json.dumps(_axis(), indent=2, sort_keys=True) + "\n").encode()
    (itl / source_path).write_bytes(raw)
    _git(itl, "add", source_path)
    _git(itl, "commit", "-m", "axis")
    commit = _git(itl, "rev-parse", "HEAD").decode().strip()
    blob = _git(itl, "rev-parse", f"{commit}:{source_path}").decode().strip()

    mirror_dir = ego / "artifacts" / "ROUTE-STATE-MACHINE-001A"
    mirror_dir.mkdir(parents=True)
    (mirror_dir / "product_axis_state.json").write_bytes(raw)
    (mirror_dir / "product_axis_source_pin.json").write_text(
        json.dumps(
            {
                "schema_version": "ego.itl_product_axis_pin.v1",
                "source_repo_hint": str(itl),
                "source_commit": commit,
                "source_path": source_path,
                "source_blob_oid": blob,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
            }
        ),
        encoding="utf-8",
    )

    # Dirty sibling bytes must be irrelevant; verification reads commit:path.
    (itl / source_path).write_text("dirty worktree", encoding="utf-8")
    result = verify_pinned_itl_mirror(ego)
    assert result.verdict == "pass"
    assert result.errors == ()
    assert load_product_axis(ego) == _axis()


def test_sync_mirror_writes_exact_committed_blob_and_pin(tmp_path: Path) -> None:
    itl = tmp_path / "itl"
    ego = tmp_path / "ego"
    itl.mkdir()
    ego.mkdir()
    (itl / "artifacts" / "ROUTE-STATE-MACHINE-001A").mkdir(parents=True)
    _git(itl, "init")
    _git(itl, "config", "user.name", "test")
    _git(itl, "config", "user.email", "test@example.invalid")
    source_path = "artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json"
    raw = (json.dumps(_axis(), indent=2, sort_keys=True) + "\n").encode()
    (itl / source_path).write_bytes(raw)
    _git(itl, "add", source_path)
    _git(itl, "commit", "-m", "axis")
    commit = _git(itl, "rev-parse", "HEAD").decode().strip()

    pin = sync_pinned_itl_mirror(ego, itl, commit)
    assert (ego / source_path).read_bytes() == raw
    assert pin["source_commit"] == commit
    assert pin["source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert verify_pinned_itl_mirror(ego).verdict == "pass"


def test_verify_mirror_rejects_byte_or_pin_drift(tmp_path: Path) -> None:
    root = tmp_path
    mirror_dir = root / "artifacts" / "ROUTE-STATE-MACHINE-001A"
    mirror_dir.mkdir(parents=True)
    (mirror_dir / "product_axis_state.json").write_text("{}\n", encoding="utf-8")
    (mirror_dir / "product_axis_source_pin.json").write_text(
        json.dumps(
            {
                "source_repo_hint": str(tmp_path / "missing"),
                "source_commit": "0" * 40,
                "source_path": "axis.json",
                "source_blob_oid": "0" * 40,
                "source_sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    result = verify_pinned_itl_mirror(root)
    assert result.verdict == "fail"
    assert result.errors


def test_render_active_views_has_one_entry_and_no_retired_active_owner() -> None:
    views = render_active_views(_axis())
    assert "AGENTS.md" in views
    assert "docs/ACTIVE_CONTEXT_PACK.md" in views
    assert "docs/PROGRAM_STATE_UNIFIED.yaml" in views
    joined = "\n".join(views.values())
    assert "scripts/run_ego_life_playground_v0.py" in joined
    assert "runtime_authority: local_explicit_v2_only" in joined
    assert "EgoOperator is active" not in joined
    assert "EgoDesktop is successor" not in joined
