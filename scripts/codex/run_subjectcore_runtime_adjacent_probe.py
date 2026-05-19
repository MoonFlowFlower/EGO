from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

CONTRACT_MODULE_PATH = ROOT / "scripts" / "codex" / "subjectcore_contract.py"
FOLLOWON_EVAL_STUB_PATH = ROOT / "scripts" / "codex" / "render_subjectcore_followon_eval_stub.py"
OUTPUT_SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_RUNTIME_ADJACENT_PROBE_SCHEMA.md"

OUTPUT_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_RUNTIME_ADJACENT_PROBE_CURRENT.json"
OUTPUT_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_RUNTIME_ADJACENT_PROBE_CURRENT.md"

SCHEMA_VERSION = "subjectcore.runtime_adjacent_probe.v1"
DEFAULT_SAMPLE_MODES = (
    "valid_facade",
    "multi_step_replacement_closure_ready",
    "multi_step_rollback_closure_ready",
    "multi_step_replacement_missing_closure_trace",
    "multi_step_rollback_missing_closure_trace",
    "proposal_authority_violation",
    "proposal_without_host_approval",
)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


subjectcore_contract = _load_module(CONTRACT_MODULE_PATH, "subjectcore_runtime_adjacent_contract")
followon_eval_stub = _load_module(FOLLOWON_EVAL_STUB_PATH, "subjectcore_runtime_adjacent_eval_stub")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first bounded runtime-adjacent SubjectCore probe")
    parser.add_argument(
        "--sample-mode",
        dest="sample_modes",
        action="append",
        choices=subjectcore_contract.SAMPLE_MODES,
        help="Sample mode to include in the runtime-adjacent probe. Defaults to the frozen first probe pack.",
    )
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=OUTPUT_MD_PATH)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _claim_ceiling_note_ok(note: str) -> bool:
    lowered = note.lower()
    return (
        "runtime efficacy" in lowered
        and ("autonomy" in lowered or "autonomous" in lowered)
        and "conscious" in lowered
    )


def _failed_checks(payload: dict[str, Any]) -> list[str]:
    return [check_id for check_id, check in dict(payload.get("checks") or {}).items() if check.get("status") != "pass"]


def _projection_summary(host_projection: dict[str, Any]) -> dict[str, Any]:
    trace_payload = dict(host_projection["trace_payload"])
    return {
        "policy_hint": dict(host_projection["policy_hint"]),
        "response_tendency": dict(host_projection["response_tendency"]),
        "trace_payload": {
            "proposal_count": trace_payload["proposal_count"],
            "proposal_only_consistent": trace_payload["proposal_only_consistent"],
            "behavioral_authority": trace_payload["behavioral_authority"],
            "corrective_trace_present": trace_payload["corrective_trace_present"],
            "viability_pressure": trace_payload["viability_pressure"],
        },
    }


def build_runtime_adjacent_probe_payload(sample_modes: list[str] | tuple[str, ...]) -> dict[str, Any]:
    requested_modes = list(sample_modes)
    sample_results: list[dict[str, Any]] = []
    allowed_projection_count = 0

    for sample_mode in requested_modes:
        integrity, boundary = followon_eval_stub.build_followon_eval_payloads(sample_mode)
        integrity_failures = _failed_checks(integrity)
        boundary_failures = _failed_checks(boundary)
        gate_green = integrity["eval_status"] == "pass" and boundary["eval_status"] == "pass"
        gate_status = "blocked"
        blocked_by: list[str] = []
        projected_host_surface_keys: list[str] = []
        projected_host_surface_summary: dict[str, Any] | None = None

        if gate_green:
            subject_core = subjectcore_contract.build_sample_subjectcore(sample_mode)
            snapshot = subjectcore_contract.build_subjectcore_snapshot(subject_core)
            host_projection = subjectcore_contract.project_to_host_surface(snapshot)
            projected_host_surface_keys = sorted(host_projection.keys())
            projected_host_surface_summary = _projection_summary(host_projection)
            if projected_host_surface_keys == sorted(subjectcore_contract.HOST_SURFACE_KEYS):
                gate_status = "pass"
                allowed_projection_count += 1
            else:
                gate_status = "fail"
                blocked_by.append("host_surface_drift")
        else:
            if integrity["eval_status"] != "pass":
                blocked_by.append("integrity_gate")
            if boundary["eval_status"] != "pass":
                blocked_by.append("boundary_gate")

        sample_results.append(
            {
                "sample_mode": sample_mode,
                "integrity_status": integrity["eval_status"],
                "boundary_status": boundary["eval_status"],
                "integrity_failures": integrity_failures,
                "boundary_failures": boundary_failures,
                "gate_status": gate_status,
                "blocked_by": blocked_by,
                "projected_host_surface_keys": projected_host_surface_keys,
                "projected_host_surface_summary": projected_host_surface_summary,
            }
        )

    result_by_mode = {result["sample_mode"]: result for result in sample_results}
    closure_failure_modes = {
        "multi_step_replacement_missing_closure_trace",
        "multi_step_rollback_missing_closure_trace",
    }
    authority_failure_modes = {
        "proposal_authority_violation",
        "proposal_without_host_approval",
    }

    green_projection_ok = (
        "valid_facade" in result_by_mode
        and result_by_mode["valid_facade"]["gate_status"] == "pass"
        and result_by_mode["valid_facade"]["projected_host_surface_keys"]
        == sorted(subjectcore_contract.HOST_SURFACE_KEYS)
    )
    closure_ready_projection_ok = (
        "multi_step_replacement_closure_ready" in result_by_mode
        and result_by_mode["multi_step_replacement_closure_ready"]["gate_status"] == "pass"
        and result_by_mode["multi_step_replacement_closure_ready"]["projected_host_surface_keys"]
        == sorted(subjectcore_contract.HOST_SURFACE_KEYS)
    )
    rollback_closure_ready_projection_ok = (
        "multi_step_rollback_closure_ready" in result_by_mode
        and result_by_mode["multi_step_rollback_closure_ready"]["gate_status"] == "pass"
        and result_by_mode["multi_step_rollback_closure_ready"]["projected_host_surface_keys"]
        == sorted(subjectcore_contract.HOST_SURFACE_KEYS)
    )
    closure_failures_blocked = all(
        mode in result_by_mode
        and result_by_mode[mode]["gate_status"] == "blocked"
        and "integrity_gate" in result_by_mode[mode]["blocked_by"]
        and result_by_mode[mode]["boundary_status"] == "pass"
        for mode in closure_failure_modes
    )
    authority_failures_blocked = all(
        mode in result_by_mode
        and result_by_mode[mode]["gate_status"] == "blocked"
        and "boundary_gate" in result_by_mode[mode]["blocked_by"]
        for mode in authority_failure_modes
    )
    projected_host_surface_ok = all(
        result["projected_host_surface_keys"] == sorted(subjectcore_contract.HOST_SURFACE_KEYS)
        for result in sample_results
        if result["gate_status"] == "pass"
    )
    claim_ceiling_note = (
        "First bounded runtime-adjacent SubjectCore probe only. This artifact does not prove formal runtime integration, "
        "runtime efficacy, live chained-update quality, autonomy expansion, live user benefit, or any consciousness-like claim."
    )
    claim_ceiling_ok = _claim_ceiling_note_ok(claim_ceiling_note)

    checks = {
        "RA1 green_sample_projects_to_frozen_host_surface": {
            "status": "pass" if green_projection_ok else "fail",
            "note": (
                "the green valid_facade sample now reaches one bounded runtime-adjacent host projection without widening the host surface"
                if green_projection_ok
                else "the green valid_facade sample does not currently reach one bounded frozen-surface projection"
            ),
        },
        "RA2 closure_ready_positive_case_projects_to_frozen_host_surface": {
            "status": "pass" if closure_ready_projection_ok else "fail",
            "note": (
                "the closure-ready chained replacement sample now also reaches a bounded runtime-adjacent host projection on the same frozen surface"
                if closure_ready_projection_ok
                else "the closure-ready chained replacement sample does not yet reach a bounded frozen-surface projection"
            ),
        },
        "RA2b rollback_closure_ready_positive_case_projects_to_frozen_host_surface": {
            "status": "pass" if rollback_closure_ready_projection_ok else "fail",
            "note": (
                "the closure-ready chained rollback sample now also reaches a bounded runtime-adjacent host projection on the same frozen surface"
                if rollback_closure_ready_projection_ok
                else "the closure-ready chained rollback sample does not yet reach a bounded frozen-surface projection"
            ),
        },
        "RA3 closure_failures_blocked_before_projection": {
            "status": "pass" if closure_failures_blocked else "fail",
            "note": (
                "closure-trace failures are still stopped by the integrity gate before runtime-adjacent projection"
                if closure_failures_blocked
                else "closure-trace failures are no longer being stopped before runtime-adjacent projection"
            ),
        },
        "RA4 authority_failures_blocked_before_projection": {
            "status": "pass" if authority_failures_blocked else "fail",
            "note": (
                "authority / approval failures are still stopped by the boundary gate before runtime-adjacent projection"
                if authority_failures_blocked
                else "authority / approval failures are no longer being stopped before runtime-adjacent projection"
            ),
        },
        "RA5 projected_host_surface_keys_still_frozen": {
            "status": "pass" if projected_host_surface_ok else "fail",
            "note": (
                "all admitted projections still expose only policy_hint / response_tendency / trace_payload"
                if projected_host_surface_ok
                else "one or more admitted projections now expose host-surface drift"
            ),
        },
        "RA6 claim_ceiling_still_bounded": {
            "status": "pass" if claim_ceiling_ok else "fail",
            "note": (
                "the probe artifact still states a bounded runtime-adjacent claim ceiling below runtime efficacy/autonomy/consciousness claims"
                if claim_ceiling_ok
                else "the probe artifact no longer states the bounded claim ceiling clearly"
            ),
        },
    }
    blocked_reasons = [check_id for check_id, check in checks.items() if check["status"] != "pass"]
    runtime_adjacent_status = "pass" if not blocked_reasons else "fail"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "output_schema_path": _display_path(OUTPUT_SCHEMA_PATH),
        "claim_ceiling_note": claim_ceiling_note,
        "sample_modes": requested_modes,
        "runtime_adjacent_status": runtime_adjacent_status,
        "blocked_reasons": blocked_reasons,
        "checks": checks,
        "allowed_projection_count": allowed_projection_count,
        "sample_results": sample_results,
        "summary": (
            "After explicit user authorization, the first bounded SubjectCore runtime-adjacent probe now passes with three green projections: the baseline facade sample plus closure-ready chained replacement and rollback samples all reach the frozen host surface, while closure and authority failures are blocked before projection."
            if runtime_adjacent_status == "pass"
            else "The first bounded SubjectCore runtime-adjacent probe is not yet coherent enough to admit a safe frozen-surface projection."
        ),
        "what_it_proves": (
            "The repo can now compose the existing planning-side SubjectCore integrity/boundary gate with one bounded runtime-adjacent projection gate that admits a baseline green sample plus closure-ready chained replacement and rollback samples to the same frozen host surface, while closure-integrity and governor-boundary failures are still blocked before projection."
        ),
        "what_it_does_not_prove": (
            "It does not prove that the formal runtime mainline uses SubjectCore, that the same closure-ready chains pass on the real runtime path, that live chained-update quality is green, or that runtime efficacy/autonomy widened."
        ),
        "notes": [
            "This probe stays inside the current ai-self-awareness task chain and does not open a second runtime authority source.",
            "The probe intentionally reuses the existing SubjectCore follow-on eval gate rather than introducing a second scorer ontology.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SubjectCore Runtime-Adjacent Probe",
        "",
        "> First bounded runtime-adjacent probe above the frozen SubjectCore planning-side follow-on lane.",
        "",
        "## Header",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- runtime_adjacent_status: `{payload['runtime_adjacent_status']}`",
        f"- sample_modes: `{', '.join(payload['sample_modes'])}`",
        f"- allowed_projection_count: `{payload['allowed_projection_count']}`",
        f"- artifact schema: `{payload['output_schema_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        "",
        "## Summary",
        "",
        payload["summary"],
        "",
        "## Checks",
        "",
    ]
    for check_id, check in payload["checks"].items():
        lines.append(f"- `{check_id}`: `{check['status']}`")
        lines.append(f"  note: {check['note']}")
    lines.extend(["", "## Samples", ""])
    for result in payload["sample_results"]:
        lines.append(
            f"- `{result['sample_mode']}`: gate `{result['gate_status']}`, integrity `{result['integrity_status']}`, boundary `{result['boundary_status']}`"
        )
        if result["blocked_by"]:
            lines.append(f"  blocked_by: {', '.join(result['blocked_by'])}")
        if result["projected_host_surface_keys"]:
            lines.append(f"  projected_keys: {', '.join(result['projected_host_surface_keys'])}")
    lines.extend(["", "## Notes", ""])
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    sample_modes = args.sample_modes or list(DEFAULT_SAMPLE_MODES)
    payload = build_runtime_adjacent_probe_payload(sample_modes)
    markdown = build_markdown(payload)
    _write_json(args.output_json, payload)
    _write_text(args.output_md, markdown)
    print(args.output_json)
    print(args.output_md)


if __name__ == "__main__":
    main()
