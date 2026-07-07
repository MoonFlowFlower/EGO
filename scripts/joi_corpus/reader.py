"""Read-only frozen artifact reader for joi-demo corpus artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .corpus_path import resolve_corpus_root


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
        keys = sorted(payload) if isinstance(payload, dict) else []
        return {
            "sha256": digest,
            "parse_status": "ok",
            "json_top_level_type": type(payload).__name__,
            "json_top_level_keys": keys,
            "parse_error_count": 0,
        }
    except Exception as exc:  # pragma: no cover - exact parser text varies
        return {
            "sha256": digest,
            "parse_status": "error",
            "json_top_level_type": None,
            "json_top_level_keys": [],
            "parse_error_count": 1,
            "parse_errors": [str(exc)],
        }


def _read_jsonl(path: Path) -> dict:
    h = hashlib.sha256()
    line_count = 0
    parse_error_count = 0
    first_errors: list[dict] = []
    with path.open("rb") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            h.update(raw_line)
            line_count += 1
            try:
                if not raw_line.strip():
                    raise ValueError("blank JSONL line")
                json.loads(raw_line)
            except Exception as exc:  # pragma: no cover - corpus-specific
                parse_error_count += 1
                if len(first_errors) < 5:
                    first_errors.append({"line": line_no, "error": str(exc)})
    return {
        "sha256": h.hexdigest(),
        "parse_status": "ok" if parse_error_count == 0 else "error",
        "jsonl_line_count": line_count,
        "parse_error_count": parse_error_count,
        "parse_errors": first_errors,
    }


def read_file(path: Path, corpus_root: Path) -> dict:
    rel = path.relative_to(corpus_root).as_posix()
    suffix = path.suffix.lower()
    base = {
        "relative_path": rel,
        "artifact_dir": path.relative_to(corpus_root / "artifacts").parts[0],
        "byte_size": path.stat().st_size,
    }
    if suffix == ".json":
        base.update({"kind": "json"})
        base.update(_read_json(path))
    elif suffix == ".jsonl":
        base.update({"kind": "jsonl"})
        base.update(_read_jsonl(path))
    else:
        base.update(
            {
                "kind": "opaque",
                "sha256": sha256_file(path),
                "parse_status": "not_applicable",
                "parse_error_count": 0,
            }
        )
    return base


def read_artifact_tree(corpus_path: str | Path | None = None) -> dict:
    root = resolve_corpus_root(corpus_path)
    artifacts = root / "artifacts"
    entries: list[dict] = []
    for artifact_dir in sorted(p for p in artifacts.iterdir() if p.is_dir()):
        for path in sorted(p for p in artifact_dir.rglob("*") if p.is_file()):
            entries.append(read_file(path, root))
    jsonl_entries = [entry for entry in entries if entry["kind"] == "jsonl"]
    parse_error_count = sum(entry.get("parse_error_count", 0) for entry in entries)
    critical_parse_error_count = sum(
        entry.get("parse_error_count", 0)
        for entry in entries
        if entry["kind"] == "jsonl" or entry["relative_path"].endswith("/result.json")
    )
    return {
        "corpus_root": str(root),
        "artifact_dir_count": len({entry["artifact_dir"] for entry in entries}),
        "file_count": len(entries),
        "json_count": sum(1 for entry in entries if entry["kind"] == "json"),
        "jsonl_count": len(jsonl_entries),
        "jsonl_total_lines": sum(entry.get("jsonl_line_count", 0) for entry in jsonl_entries),
        "parse_error_count": parse_error_count,
        "critical_parse_error_count": critical_parse_error_count,
        "entries": entries,
    }
