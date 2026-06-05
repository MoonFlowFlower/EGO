from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "archive_verifier_common.py"
spec = importlib.util.spec_from_file_location("archive_verifier_common", MODULE_PATH)
archive_verifier_common = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = archive_verifier_common
spec.loader.exec_module(archive_verifier_common)


def write_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "archive_pointer": {
                    "name": "archive-before-purge",
                    "commit": "abc123",
                },
                "removed_paths": [
                    "legacy/old-runtime/",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_archive_core_passes_when_tag_matches_and_removed_dir_absent(tmp_path: Path) -> None:
    manifest = archive_verifier_common.load_archival_manifest(write_manifest(tmp_path))
    errors: list[str] = []

    archive_verifier_common.check_archive_core(
        root=tmp_path,
        manifest=manifest,
        errors=errors,
        rev_parse=lambda ref: "abc123" if ref == "archive-before-purge" else "",
    )

    assert errors == []


def test_archive_core_fails_when_removed_dir_exists(tmp_path: Path) -> None:
    (tmp_path / "legacy" / "old-runtime").mkdir(parents=True)
    manifest = archive_verifier_common.load_archival_manifest(write_manifest(tmp_path))
    errors: list[str] = []

    archive_verifier_common.check_archive_core(
        root=tmp_path,
        manifest=manifest,
        errors=errors,
        rev_parse=lambda _ref: "abc123",
    )

    assert "removed legacy directory still exists: legacy/old-runtime" in errors


def test_archive_core_fails_when_tag_points_elsewhere(tmp_path: Path) -> None:
    manifest = archive_verifier_common.load_archival_manifest(write_manifest(tmp_path))
    errors: list[str] = []

    archive_verifier_common.check_archive_core(
        root=tmp_path,
        manifest=manifest,
        errors=errors,
        rev_parse=lambda _ref: "wrong",
    )

    assert any("archive tag archive-before-purge resolves to wrong" in item for item in errors)


def test_active_surface_forbidden_snippet_fails_and_historical_note_passes(tmp_path: Path) -> None:
    active = tmp_path / "docs" / "ACTIVE.md"
    historical = tmp_path / "docs" / "HISTORICAL.md"
    active.parent.mkdir()
    active.write_text("runtime path legacy/old-runtime/app.py", encoding="utf-8")
    historical.write_text("historical note archive-before-purge reference only", encoding="utf-8")
    errors: list[str] = []

    archive_verifier_common.check_forbidden_snippets(
        tmp_path,
        ["docs/ACTIVE.md"],
        ["legacy/old-runtime"],
        errors,
    )
    archive_verifier_common.check_historical_safety_notes(
        tmp_path,
        {"docs/HISTORICAL.md": ["historical note", "archive-before-purge"]},
        errors,
    )

    assert len(errors) == 1
    assert errors[0].startswith("docs/ACTIVE.md contains forbidden active legacy path snippets")
