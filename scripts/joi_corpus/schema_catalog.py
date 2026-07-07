"""Observed result/baseline schema catalog for the frozen joi-demo corpus."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .corpus_path import resolve_corpus_root


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_key(data: Any, key: str, prefix: tuple[str, ...] = ()) -> tuple[Any, str] | None:
    if isinstance(data, dict):
        if key in data:
            return data[key], ".".join((*prefix, key))
        for k, v in data.items():
            found = _find_key(v, key, (*prefix, str(k)))
            if found is not None:
                return found
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            found = _find_key(value, key, (*prefix, str(idx)))
            if found is not None:
                return found
    return None


def _find_config_sha(data: Any) -> tuple[Any, str] | None:
    if isinstance(data, dict):
        for k, v in data.items():
            lk = str(k).lower()
            if "config" in lk and "sha" in lk and isinstance(v, str):
                return v, str(k)
        for k, v in data.items():
            found = _find_config_sha(v)
            if found is not None:
                return found[0], f"{k}.{found[1]}"
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            found = _find_config_sha(value)
            if found is not None:
                return found[0], f"{idx}.{found[1]}"
    return None


def _path_value(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def extract_canonical_fields(data: dict) -> dict:
    fields: dict[str, dict] = {}
    for name, key in {
        "task_id": "task_id",
        "verdict": "verdict",
        "run_id": "run_id",
        "claim_ceiling": "claim_ceiling",
    }.items():
        found = _find_key(data, key)
        if found is not None:
            fields[name] = {"path": found[1], "value": found[0]}
    if isinstance(data.get("brier"), dict) and "candidate" in data["brier"]:
        fields["candidate_brier"] = {"path": "brier.candidate", "value": data["brier"]["candidate"]}
    else:
        found = _find_key(data, "candidate_brier")
        if found is not None:
            fields["candidate_brier"] = {"path": found[1], "value": found[0]}
    found = _find_config_sha(data)
    if found is not None:
        fields["config_sha"] = {"path": found[1], "value": found[0]}
    return fields


def build_shape_catalog(corpus_path: str | Path | None = None) -> dict:
    root = resolve_corpus_root(corpus_path)
    entries: list[dict] = []
    variants: dict[str, dict] = {}
    for path in sorted((root / "artifacts").glob("*/result.json")):
        data = _load_json(path)
        top_fields = sorted(data) if isinstance(data, dict) else []
        variant_id = "variant_" + hashlib.sha1("\n".join(top_fields).encode()).hexdigest()[:10]
        variants.setdefault(
            variant_id,
            {
                "variant_id": variant_id,
                "top_level_fields": top_fields,
                "result_count": 0,
                "examples": [],
            },
        )
        variants[variant_id]["result_count"] += 1
        if len(variants[variant_id]["examples"]) < 3:
            variants[variant_id]["examples"].append(path.parent.name)
        entries.append(
            {
                "artifact_dir": path.parent.name,
                "relative_path": path.relative_to(root).as_posix(),
                "variant_id": variant_id,
                "top_level_fields": top_fields,
                "canonical_fields": extract_canonical_fields(data),
            }
        )
    coverage: dict[str, int] = defaultdict(int)
    for entry in entries:
        for name in entry["canonical_fields"]:
            coverage[name] += 1
    common_top = sorted(set(entries[0]["top_level_fields"]).intersection(*(set(e["top_level_fields"]) for e in entries[1:]))) if entries else []
    return {
        "corpus_root": str(root),
        "result_count": len(entries),
        "common_top_level_fields": common_top,
        "canonical_field_coverage": dict(sorted(coverage.items())),
        "core_contract_rule": (
            "Ego-side rewrites MUST emit at least task_id, verdict, claim_ceiling, "
            "and provenance/run_id when the run has one; new fields are additive, "
            "never redefinitions of observed corpus fields."
        ),
        "variants": sorted(variants.values(), key=lambda row: row["variant_id"]),
        "entries": entries,
    }


def load_result(corpus_path: str | Path | None, artifact_dir: str) -> dict:
    root = resolve_corpus_root(corpus_path)
    return _load_json(root / "artifacts" / artifact_dir / "result.json")


def render_schema_contract(catalog: dict) -> str:
    lines = [
        "# JOI Demo Frozen Corpus Schema Contract",
        "",
        "This file is generated from observed `artifacts/*/result.json` files in the frozen joi-demo corpus.",
        "It catalogs observed reality; it does not normalize or reinterpret heterogeneous eras.",
        "",
        "## Canonical core rule",
        "",
        catalog["core_contract_rule"],
        "",
        "## Coverage",
        "",
    ]
    for name, count in catalog["canonical_field_coverage"].items():
        lines.append(f"- `{name}`: {count}/{catalog['result_count']} result files")
    lines.extend(["", "## Common top-level fields", ""])
    lines.append(", ".join(f"`{field}`" for field in catalog["common_top_level_fields"]) or "_none_")
    lines.extend(["", "## Variant table", "", "| Variant | Count | Example dirs | Top-level fields |", "|---|---:|---|---|"])
    for variant in catalog["variants"]:
        examples = ", ".join(f"`{name}`" for name in variant["examples"])
        fields = ", ".join(f"`{field}`" for field in variant["top_level_fields"])
        lines.append(f"| `{variant['variant_id']}` | {variant['result_count']} | {examples} | {fields} |")
    lines.extend(
        [
            "",
            "## Rewrite boundary",
            "",
            "- Ego-side rewrites must be clean implementations, not corpus code ports.",
            "- New fields are additive only; observed field names may not be redefined.",
            "- This contract is file-format compatibility evidence only.",
        ]
    )
    return "\n".join(lines) + "\n"
