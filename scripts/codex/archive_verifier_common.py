#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class ArchivalManifest:
    manifest_path: Path
    archive_tag: str
    archive_commit: str
    removed_dirs: tuple[str, ...]


def normalize_removed_path(path: str) -> str:
    return path.strip().replace("\\", "/").strip("/")


def load_archival_manifest(manifest_path: Path) -> ArchivalManifest:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_pointer = payload.get("archive_pointer") or {}
    archive_tag = str(archive_pointer.get("name") or "")
    archive_commit = str(archive_pointer.get("commit") or payload.get("created_from_commit") or "")
    removed_dirs = tuple(normalize_removed_path(str(item)) for item in (payload.get("removed_paths") or []))
    return ArchivalManifest(
        manifest_path=manifest_path,
        archive_tag=archive_tag,
        archive_commit=archive_commit,
        removed_dirs=removed_dirs,
    )


def git_rev_parse(root: Path, ref: str) -> str:
    proc = subprocess.run(["git", "rev-parse", "--verify", ref], cwd=root, capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def check_archive_core(
    *,
    root: Path,
    manifest: ArchivalManifest,
    errors: list[str],
    rev_parse: Callable[[str], str] | None = None,
) -> None:
    resolver = rev_parse or (lambda ref: git_rev_parse(root, ref))
    if not manifest.archive_tag:
        errors.append("archive manifest missing archive_pointer.name")
    if not manifest.archive_commit:
        errors.append("archive manifest missing archive commit")
    if not manifest.removed_dirs:
        errors.append("archive manifest missing removed_paths")

    resolved = resolver(manifest.archive_tag) if manifest.archive_tag else ""
    if manifest.archive_tag and resolved != manifest.archive_commit:
        errors.append(
            f"archive tag {manifest.archive_tag} resolves to {resolved or 'unavailable'}, "
            f"expected {manifest.archive_commit}"
        )

    for rel_path in manifest.removed_dirs:
        if (root / rel_path).exists():
            errors.append(f"removed legacy directory still exists: {rel_path}")


def check_required_snippets(root: Path, required_by_path: dict[str, Iterable[str]], errors: list[str]) -> None:
    for rel_path, snippets in required_by_path.items():
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing archive pointer surface: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{rel_path} missing required archive snippet: {snippet}")


def check_forbidden_snippets(root: Path, rel_paths: Iterable[str], forbidden_snippets: Iterable[str], errors: list[str]) -> None:
    snippets = tuple(forbidden_snippets)
    for rel_path in rel_paths:
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing active surface: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        matches = [snippet for snippet in snippets if snippet in text]
        if matches:
            errors.append(f"{rel_path} contains forbidden active legacy path snippets: {', '.join(matches[:5])}")


def check_historical_safety_notes(root: Path, required_by_path: dict[str, Iterable[str]], errors: list[str]) -> None:
    for rel_path, snippets in required_by_path.items():
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing historical surface with safety note: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{rel_path} missing historical safety snippet: {snippet}")
