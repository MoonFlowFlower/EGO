#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from route_convergence_common import build_route_entries, load_program_state


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_INDEX = ROOT / "docs" / "archive" / "ARCHIVE_INDEX.yaml"

MOVED_FILES = {
    "docs/EGO 验收证据分级协议 v1.md": "docs/archive/EGO 验收证据分级协议 v1.md",
    "docs/EGO_DEVELOPMENT_CLOSED_LOOP_V1.md": "docs/archive/EGO_DEVELOPMENT_CLOSED_LOOP_V1.md",
}

MOVED_DIRS = {
    f"artifacts/P{index}": f"artifacts/archive/repo_cleanup_history/P{index}"
    for index in range(8)
}

PROTECTED_CURRENT_PATHS = [
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "artifacts/evidence_ledger/index.yaml",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
    "docs/REPO_HYGIENE_POLICY.md",
    "docs/MAINLINE_QUICKSTART.md",
]

LEGACY_REFERENCE_NEEDLES = [
    *MOVED_FILES.keys(),
    *MOVED_DIRS.keys(),
]

LEGACY_REFERENCE_SCAN_ROOTS = [
    "docs",
    "scripts",
    "OpenEmotion/compatibility-only",
]

ALLOWED_LEGACY_REFERENCE_PREFIXES = (
    "docs/archive/",
    "artifacts/archive/",
    "docs/codex/tasks/repo-authority-cleanup/",
)

ALLOWED_LEGACY_REFERENCE_FILES = {
    # Historical report preserves a git-status snapshot from before archive
    # reconciliation. It is evidence text, not a current route source.
    "docs/SEMANTIC_PROVIDER_ABSTRACTION_V5B_REPORT.md",
    # This verifier must name the old paths it protects against.
    "scripts/codex/verify_archive_reconciliation.py",
}

FORBIDDEN_STAGED_PREFIXES = (
    "temp/",
    "logs/",
    ".pytest_cache/",
    "EgoCore/logs/",
    "OpenEmotion/logs/",
)

FORBIDDEN_STAGED_FILES = {
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "artifacts/evidence_ledger/index.yaml",
}


def _git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _git_blob(path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _archive_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("  - archive_id:") and current:
            blocks.append("\n".join(current))
            current = [line]
            continue
        if current or line.startswith("  - archive_id:"):
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _find_archive_block(blocks: list[str], old_path: str, current_path: str) -> str | None:
    old_snippet = f'original_path: "{old_path}"'
    current_snippet = f'current_path: "{current_path}"'
    for block in blocks:
        if old_snippet in block and current_snippet in block:
            return block
    return None


def _is_allowed_legacy_reference(path: str) -> bool:
    if path in ALLOWED_LEGACY_REFERENCE_FILES:
        return True
    if path.startswith(ALLOWED_LEGACY_REFERENCE_PREFIXES):
        return True
    name = Path(path).name
    return path.startswith("docs/") and "REPORT" in name


def _check_index_entries(errors: list[str]) -> list[str]:
    if not ARCHIVE_INDEX.exists():
        errors.append("missing archive index: docs/archive/ARCHIVE_INDEX.yaml")
        return []

    text = ARCHIVE_INDEX.read_text(encoding="utf-8")
    blocks = _archive_blocks(text)
    for old_path, current_path in {**MOVED_FILES, **MOVED_DIRS}.items():
        block = _find_archive_block(blocks, old_path, current_path)
        if block is None:
            errors.append(f"archive index missing moved entry: {old_path} -> {current_path}")
            continue
        if 'index_only_or_moved: "moved"' not in block:
            errors.append(f"archive index entry is not marked moved: {old_path}")
        if 'classification: "archive"' not in block:
            errors.append(f"archive index entry is not classified archive: {old_path}")
    return blocks


def _check_paths(errors: list[str]) -> None:
    for old_path, current_path in MOVED_FILES.items():
        if (ROOT / old_path).exists():
            errors.append(f"old top-level archived doc still exists: {old_path}")
        current = ROOT / current_path
        if not current.is_file():
            errors.append(f"archived doc missing: {current_path}")
            continue
        old_blob = _git_blob(old_path)
        if old_blob is not None and old_blob != current.read_bytes():
            errors.append(f"archived doc content does not match previous HEAD content: {current_path}")

    for old_dir, current_dir in MOVED_DIRS.items():
        if (ROOT / old_dir).exists():
            errors.append(f"old archived artifact directory still exists: {old_dir}")
        current = ROOT / current_dir
        if not current.is_dir():
            errors.append(f"archived artifact directory missing: {current_dir}")
            continue
        old_files = _git_lines(["ls-files", old_dir])
        for old_file in old_files:
            rel = Path(old_file).relative_to(old_dir)
            current_file = current / rel
            if not current_file.is_file():
                errors.append(f"archived artifact file missing: {current_file.relative_to(ROOT)}")
                continue
            old_blob = _git_blob(old_file)
            if old_blob is not None and old_blob != current_file.read_bytes():
                errors.append(f"archived artifact content mismatch: {current_file.relative_to(ROOT)}")

    for path in PROTECTED_CURRENT_PATHS:
        if not (ROOT / path).exists():
            errors.append(f"protected current path missing after archive reconciliation: {path}")


def _check_legacy_references(errors: list[str]) -> None:
    tracked = _git_lines(["ls-files", *LEGACY_REFERENCE_SCAN_ROOTS])
    for path in tracked:
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        text = full_path.read_text(encoding="utf-8", errors="ignore")
        matches = [needle for needle in LEGACY_REFERENCE_NEEDLES if needle in text]
        if not matches:
            continue
        if _is_allowed_legacy_reference(path):
            continue
        errors.append(f"current file still references archived old path(s): {path}: {', '.join(matches)}")


def _check_staged_boundary(errors: list[str]) -> None:
    staged = _git_lines(["diff", "--cached", "--name-only"])
    for path in staged:
        if path in FORBIDDEN_STAGED_FILES:
            errors.append(f"forbidden staged authority/evidence file for archive reconciliation: {path}")
        if path.endswith(".jsonl"):
            errors.append(f"forbidden staged runtime JSONL for archive reconciliation: {path}")
        if "__pycache__/" in path or path.endswith(".pyc"):
            errors.append(f"forbidden staged Python cache for archive reconciliation: {path}")
        if path.startswith(FORBIDDEN_STAGED_PREFIXES):
            errors.append(f"forbidden staged operational exhaust for archive reconciliation: {path}")


def _check_active_default(errors: list[str]) -> str | None:
    entries = build_route_entries(load_program_state())
    active_default = [entry for entry in entries if entry.lane == "active_default"]
    if len(active_default) != 1:
        errors.append(f"expected exactly one active default lane, found {len(active_default)}")
        return None
    if active_default[0].key != "subject-system-v1-governed-proactivity":
        errors.append(f"unexpected active default lane: {active_default[0].key}")
    return active_default[0].key


def main() -> int:
    errors: list[str] = []
    _check_index_entries(errors)
    _check_paths(errors)
    _check_legacy_references(errors)
    _check_staged_boundary(errors)
    active_default = _check_active_default(errors)

    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "active_default": active_default,
                "archive_index": str(ARCHIVE_INDEX.relative_to(ROOT)),
                "moved_docs": len(MOVED_FILES),
                "moved_artifact_dirs": len(MOVED_DIRS),
                "protected_current_paths": PROTECTED_CURRENT_PATHS,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
