#!/usr/bin/env python3
"""Validate the EgoOperator experience-first rubric sample pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE_PACK = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-experience-roadmap-bootstrap-v1"
    / "chinese_experience_sample_pack.json"
)
DEFAULT_RUBRIC = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-experience-roadmap-bootstrap-v1"
    / "EXPERIENCE_EVAL_RUBRIC.md"
)

REQUIRED_DIMENSIONS = {
    "natural_understanding",
    "continuity",
    "empathy",
    "initiative_boundary",
    "memory_pollution",
    "tool_recovery",
    "correction_burden",
}
ALLOWED_OBSERVATION_CLASSES = {
    "deterministic_local",
    "scripted_real_entry",
    "scripted_with_llm_judge",
    "human_required",
}
FORBIDDEN_CLAIM_WORDS = {
    "真实意识",
    "独立意识已实现",
    "consciousness achieved",
    "live autonomy proved",
    "runtime efficacy proved",
}


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def validate_sample_pack(path: Path = DEFAULT_SAMPLE_PACK, rubric_path: Path = DEFAULT_RUBRIC) -> dict[str, Any]:
    errors: list[str] = []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rubric = rubric_path.read_text(encoding="utf-8")

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("language") != "zh-CN":
        errors.append("language must be zh-CN")
    if payload.get("claim_boundary") != "operational_proxy_only_not_consciousness_claim":
        errors.append("claim_boundary must preserve operational proxy only")

    dimensions = set(payload.get("rubric_dimensions") or [])
    if dimensions != REQUIRED_DIMENSIONS:
        errors.append(f"rubric_dimensions mismatch: {sorted(dimensions)}")
    for dimension in REQUIRED_DIMENSIONS:
        if dimension not in rubric:
            errors.append(f"rubric is missing dimension: {dimension}")

    lowered = f"{json.dumps(payload, ensure_ascii=False)}\n{rubric}".casefold()
    for forbidden in FORBIDDEN_CLAIM_WORDS:
        if forbidden.casefold() in lowered:
            errors.append(f"forbidden overclaim phrase found: {forbidden}")

    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 20:
        errors.append("cases must contain at least 20 entries")
        cases = cases if isinstance(cases, list) else []

    seen_ids: set[str] = set()
    covered_dimensions: set[str] = set()
    covered_observation_classes: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = str(case.get("id") or "")
        if not re.fullmatch(r"[a-z0-9_]+", case_id):
            errors.append(f"{prefix}.id must be snake_case ascii")
        if case_id in seen_ids:
            errors.append(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)

        category = str(case.get("category") or "")
        if category not in REQUIRED_DIMENSIONS:
            errors.append(f"{prefix}.category is not a rubric dimension: {category}")
        else:
            covered_dimensions.add(category)

        observation_class = str(case.get("observation_class") or "")
        if observation_class not in ALLOWED_OBSERVATION_CLASSES:
            errors.append(f"{prefix}.observation_class is invalid: {observation_class}")
        else:
            covered_observation_classes.add(observation_class)

        prompt = str(case.get("prompt") or "")
        if len(prompt) < 4 or not _has_cjk(prompt):
            errors.append(f"{prefix}.prompt must be a non-trivial Chinese prompt")

        for key in ("expected_signals", "failure_signals"):
            value = case.get(key)
            if not isinstance(value, list) or len(value) < 2 or not all(isinstance(item, str) and item for item in value):
                errors.append(f"{prefix}.{key} must contain at least two non-empty strings")

        score_focus = case.get("score_focus")
        if not isinstance(score_focus, list) or not score_focus:
            errors.append(f"{prefix}.score_focus must be a non-empty list")
        else:
            invalid = [item for item in score_focus if item not in REQUIRED_DIMENSIONS]
            if invalid:
                errors.append(f"{prefix}.score_focus contains invalid dimensions: {invalid}")

        if not str(case.get("user_visible_goal") or "").strip():
            errors.append(f"{prefix}.user_visible_goal is required")

    missing_coverage = REQUIRED_DIMENSIONS - covered_dimensions
    if missing_coverage:
        errors.append(f"missing category coverage: {sorted(missing_coverage)}")
    required_observation_coverage = {"deterministic_local", "scripted_real_entry", "scripted_with_llm_judge", "human_required"}
    missing_observation = required_observation_coverage - covered_observation_classes
    if missing_observation:
        errors.append(f"missing observation class coverage: {sorted(missing_observation)}")

    return {
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "case_count": len(cases),
        "dimension_count": len(dimensions),
        "covered_dimensions": sorted(covered_dimensions),
        "covered_observation_classes": sorted(covered_observation_classes),
        "sample_pack": str(path),
        "rubric": str(rubric_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate EgoOperator experience-first eval contract.")
    parser.add_argument("--sample-pack", default=str(DEFAULT_SAMPLE_PACK))
    parser.add_argument("--rubric", default=str(DEFAULT_RUBRIC))
    args = parser.parse_args(argv)
    result = validate_sample_pack(Path(args.sample_pack), Path(args.rubric))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
