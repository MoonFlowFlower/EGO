"""Fail-closed scanner for machine-generated active agent context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping
import uuid

from .product_axis import ACTIVE_VIEW_PATHS, render_active_views


@dataclass(frozen=True)
class ScanResult:
    verdict: str
    findings: tuple[dict[str, str], ...]
    producer_function: str
    input_artifacts: tuple[str, ...]
    run_id: str
    aggregation_rule: str
    code_path_hash: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = list(self.findings)
        payload["input_artifacts"] = list(self.input_artifacts)
        return payload


OLD_ACTIVE_PATTERNS = (
    re.compile(r"EgoOperator.{0,48}\b(active|default|runtime owner)\b", re.I),
    re.compile(r"\b(active|default|runtime owner)\b.{0,48}EgoOperator", re.I),
    re.compile(r"EgoDesktop.{0,48}\b(successor|active|default)\b", re.I),
    re.compile(r"\b(successor|active|default)\b.{0,48}EgoDesktop", re.I),
)


def _code_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def scan_active_views(
    views: Mapping[str, str],
    state: Mapping[str, Any],
    source_pin: Mapping[str, Any] | None = None,
) -> ScanResult:
    expected = render_active_views(state, source_pin)
    findings: list[dict[str, str]] = []
    actual_paths = set(views)
    expected_paths = set(expected)
    for path in sorted(expected_paths - actual_paths):
        findings.append({"code": "missing_active_view", "path": path})
    for path in sorted(actual_paths - expected_paths):
        findings.append({"code": "unexpected_active_view", "path": path})
    for path in sorted(expected_paths & actual_paths):
        text = views[path]
        if text != expected[path]:
            findings.append({"code": "generated_view_drift", "path": path})
        for pattern in OLD_ACTIVE_PATTERNS:
            if pattern.search(text):
                findings.append({"code": "retired_active_owner_claim", "path": path})
                break
    return ScanResult(
        verdict="pass" if not findings else "fail",
        findings=tuple(findings),
        producer_function="scan_active_views",
        input_artifacts=tuple(sorted(actual_paths)),
        run_id=f"stale-context-{uuid.uuid4().hex}",
        aggregation_rule=(
            "pass iff active path set and bytes equal the production renderer and no "
            "retired project is described with active/default/runtime-owner/successor semantics"
        ),
        code_path_hash=_code_hash(),
    )


def scan_repository(root: str | Path, state: Mapping[str, Any], source_pin: Mapping[str, Any] | None = None) -> ScanResult:
    repo = Path(root).resolve()
    views = {
        path: (repo / path).read_text(encoding="utf-8")
        for path in ACTIVE_VIEW_PATHS
        if (repo / path).is_file()
    }
    return scan_active_views(views, state, source_pin)


def run_positive_controls(state: Mapping[str, Any], source_pin: Mapping[str, Any] | None = None) -> dict[str, Any]:
    base = render_active_views(state, source_pin)
    cases: dict[str, dict[str, Any]] = {}

    def run(name: str, mutate) -> None:
        candidate = dict(base)
        mutate(candidate)
        result = scan_active_views(candidate, state, source_pin)
        cases[name] = {
            "detected": result.verdict == "fail",
            "scanner_producer": result.producer_function,
            "finding_codes": sorted({row["code"] for row in result.findings}),
        }

    run("old_active_owner", lambda v: v.__setitem__("README.md", v["README.md"] + "\nEgoOperator is active runtime owner.\n"))
    run("entrypoint_drift", lambda v: v.__setitem__("README.md", v["README.md"].replace("scripts/run_ego_life_playground_v0.py", "scripts/wrong.py")))
    run("source_pin_drift", lambda v: v.__setitem__("docs/ACTIVE_CONTEXT_PACK.md", v["docs/ACTIVE_CONTEXT_PACK.md"] + "\nitl_source_commit: tampered\n"))
    run("enablement_drift", lambda v: v.__setitem__("AGENTS.md", v["AGENTS.md"].replace("default_enabled: false", "default_enabled: true")))
    verdict = "pass" if all(row["detected"] for row in cases.values()) else "fail"
    return {
        "verdict": verdict,
        "producer_function": "run_positive_controls",
        "input_artifacts": list(ACTIVE_VIEW_PATHS),
        "run_id": f"stale-positive-control-{uuid.uuid4().hex}",
        "aggregation_rule": "pass iff every injected defect is rejected by scan_active_views",
        "code_path_hash": _code_hash(),
        "cases": cases,
    }
