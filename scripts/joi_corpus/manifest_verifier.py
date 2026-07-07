"""SHA pin verifier for frozen joi-demo artifact manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .corpus_path import resolve_corpus_root
from .reader import sha256_file

MANIFEST_NAMES = {"pre_run_hashes.json", "manifest.json", "freeze_manifest.json"}
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")

CREATURESTATE_CARD = "JOI-DEMO-GRAD-CREATURESTATE-INTERFACE-SPEC-001A-v0_2.md"
CREATURESTATE_SCHEMA = (
    "artifacts/JOI-DEMO-GRAD-CREATURESTATE-INTERFACE-SPEC-001A/"
    "creaturestate_schema_v0_2.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pathish(value: str) -> bool:
    return any(ch in value for ch in ("/", "\\")) or "." in Path(value).name


def _pin_items(manifest_path: Path, data: dict) -> list[dict]:
    items: list[dict] = []
    if isinstance(data.get("artifact_hashes"), dict):
        for rel, sha in data["artifact_hashes"].items():
            if isinstance(rel, str) and isinstance(sha, str) and SHA_RE.match(sha):
                items.append({"pin_path": rel, "expected_sha256": sha, "source": "artifact_hashes"})
    if isinstance(data.get("pins"), dict):
        for rel, sha in data["pins"].items():
            if isinstance(rel, str) and isinstance(sha, str) and SHA_RE.match(sha):
                items.append({"pin_path": rel, "expected_sha256": sha, "source": "pins"})
    superseded = data.get("superseded")
    if isinstance(superseded, dict) and isinstance(superseded.get("v0_1_pins"), dict):
        for rel, sha in superseded["v0_1_pins"].items():
            if isinstance(rel, str) and isinstance(sha, str) and SHA_RE.match(sha):
                items.append({"pin_path": rel, "expected_sha256": sha, "source": "superseded.v0_1_pins"})
    if manifest_path.name == "pre_run_hashes.json":
        for rel, sha in data.items():
            if isinstance(rel, str) and isinstance(sha, str) and SHA_RE.match(sha) and _pathish(rel):
                items.append({"pin_path": rel, "expected_sha256": sha, "source": "pre_run_hashes"})
    return items


def _resolve(corpus_root: Path, manifest_path: Path, pin_path: str) -> tuple[Path | None, str]:
    rel = pin_path.replace("\\", "/")
    candidates = [manifest_path.parent / rel, corpus_root / rel]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate, "direct"
    if "/" not in rel:
        matches = [
            p for p in corpus_root.rglob(Path(rel).name) if ".git" not in p.parts and p.is_file()
        ]
        if len(matches) == 1:
            return matches[0], "basename_unique"
        if len(matches) > 1:
            return None, f"basename_ambiguous:{len(matches)}"
    return None, "missing"


def _check_pin(corpus_root: Path, manifest_path: Path, item: dict) -> dict:
    resolved, resolution = _resolve(corpus_root, manifest_path, item["pin_path"])
    result = {
        "manifest": manifest_path.relative_to(corpus_root).as_posix(),
        "pin_path": item["pin_path"],
        "source": item["source"],
        "expected_sha256": item["expected_sha256"],
        "resolution": resolution,
    }
    if resolved is None:
        result.update({"verdict": "pinned_file_missing", "actual_sha256": None})
        return result
    actual = sha256_file(resolved)
    result.update(
        {
            "resolved_path": resolved.relative_to(corpus_root).as_posix(),
            "actual_sha256": actual,
            "verdict": "match" if actual.lower() == item["expected_sha256"].lower() else "mismatch",
        }
    )
    return result


def verify_manifests(corpus_path: str | Path | None = None) -> dict:
    root = resolve_corpus_root(corpus_path)
    manifest_paths = sorted(
        p for p in (root / "artifacts").rglob("*") if p.is_file() and p.name in MANIFEST_NAMES
    )
    checks: list[dict] = []
    for manifest_path in manifest_paths:
        data = _load(manifest_path)
        for item in _pin_items(manifest_path, data):
            checks.append(_check_pin(root, manifest_path, item))
    counts = {name: sum(1 for row in checks if row["verdict"] == name) for name in (
        "match",
        "mismatch",
        "pinned_file_missing",
    )}
    named = {}
    for name, pin_path in {
        "creaturestate_v0_2_card": CREATURESTATE_CARD,
        "creaturestate_v0_2_schema": CREATURESTATE_SCHEMA,
    }.items():
        rows = [row for row in checks if row["pin_path"].replace("\\", "/") == pin_path]
        named[name] = rows[0] if rows else {"verdict": "pinned_file_missing", "pin_path": pin_path}
    return {
        "corpus_root": str(root),
        "manifest_count": len(manifest_paths),
        "pin_count": len(checks),
        "counts": counts,
        "named_checks": named,
        "checks": checks,
    }
