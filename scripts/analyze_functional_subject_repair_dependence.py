from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ego_operator.functional_subject_repair_dependence_audit.v0"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def classify_repair_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "")
    repair_types = [str(item) for item in _as_list(case.get("repair_types"))]
    repair_set = set(repair_types)

    if repair_set & {"internal_mechanism_leak", "internal_mechanism_leak_fallback"}:
        blocker_class = "visible_internal_context_leak"
        owner = "prompt_contract_and_output_admission"
        zeno_class = "mechanism-critical"
        priority = 1
        recommended_slice = (
            "Move internal-mechanism wording out of first-pass visible replies and "
            "prove the same case no longer needs runtime leak repair."
        )
    elif "unbacked_memory_language" in repair_set:
        blocker_class = "memory_language_first_pass_gap"
        owner = "memory_gate_and_first_pass_rendering"
        zeno_class = "mechanism-critical"
        priority = 1
        recommended_slice = (
            "Make uncertainty-aware memory language part of the first-pass path "
            "instead of repairing unsupported continuity claims afterward."
        )
    elif "memory_save_success_terminal_reply" in repair_set:
        blocker_class = "memory_terminal_reply_first_pass_gap"
        owner = "memory_gate_terminal_response"
        zeno_class = "mechanism-critical"
        priority = 1
        recommended_slice = (
            "Separate candidate-local save confirmation from generic assistant text "
            "before runtime repair has to rewrite the terminal reply."
        )
    elif "outcome_prediction_safety_checkpoint" in repair_set:
        blocker_class = "safety_checkpoint_first_pass_gap"
        owner = "outcome_prediction_and_action_gate_rendering"
        zeno_class = "mechanism-critical"
        priority = 2
        recommended_slice = (
            "Keep the safety gate, but render the checkpoint as a normal first-pass "
            "proposal/approval boundary."
        )
    elif repair_set & {"self_selected_topic_traceability", "self_selected_topic_traceability_fallback"}:
        blocker_class = "self_selected_topic_traceability_gap"
        owner = "bounded_initiative_topic_selection"
        zeno_class = "mechanism-critical"
        priority = 2
        recommended_slice = (
            "Make self-selected topic choice visible through bounded initiative "
            "without leaking trace mechanics or relying on fallback repair."
        )
    elif repair_set & {"bounded_next_action", "bounded_next_action_fallback"}:
        blocker_class = "bounded_next_action_first_pass_gap"
        owner = "bounded_initiative_rendering"
        zeno_class = "mechanism-critical"
        priority = 2
        recommended_slice = (
            "Render low-instruction initiative as one concrete reversible next step "
            "in the primary path."
        )
    elif "boundary_quieting" in repair_set:
        blocker_class = "boundary_quieting_first_pass_gap"
        owner = "boundary_contract_prompting"
        zeno_class = "observation-critical"
        priority = 3
        recommended_slice = (
            "Reduce visible boundary disclaimers for non-trigger turns while "
            "preserving true boundary honesty."
        )
    else:
        blocker_class = "unclassified_runtime_repair"
        owner = "runtime_repair_triage"
        zeno_class = "mechanism-critical"
        priority = 2
        recommended_slice = "Inspect trace and classify before patching."

    return {
        "case_id": case_id,
        "origin": case.get("origin"),
        "repair_types": repair_types,
        "blocker_class": blocker_class,
        "owner": owner,
        "zeno_class": zeno_class,
        "priority": priority,
        "recommended_slice": recommended_slice,
    }


def build_repair_dependence_audit(report: dict[str, Any], *, source_report: str = "") -> dict[str, Any]:
    attribution = report.get("response_attribution_summary")
    if not isinstance(attribution, dict):
        attribution = {}
    per_case = [item for item in _as_list(attribution.get("per_case")) if isinstance(item, dict)]
    repair_cases = [
        classify_repair_case(item)
        for item in per_case
        if item.get("origin") == "runtime_repair" or _as_list(item.get("repair_types"))
    ]
    repair_cases.sort(key=lambda item: (int(item["priority"]), str(item["case_id"])))

    priority_cases = [item for item in repair_cases if int(item["priority"]) == 1]
    class_counts = Counter(str(item["blocker_class"]) for item in repair_cases)
    owner_counts = Counter(str(item["owner"]) for item in repair_cases)

    case_count = int(attribution.get("case_count") or report.get("case_count") or 0)
    repair_case_count = len(repair_cases)
    clean_first_pass_count = int(attribution.get("clean_first_pass_count") or max(case_count - repair_case_count, 0))
    target_repair_case_count = max(0, repair_case_count - len(priority_cases))

    checks = {
        "source_report_present": bool(report),
        "response_attribution_present": attribution.get("schema_version") == "ego_operator.response_attribution_summary.v1",
        "repair_cases_detected": repair_case_count > 0,
        "priority_cases_selected": bool(priority_cases),
        "no_runtime_mutation_required": True,
    }
    status = (
        "functional_subject_repair_dependence_audit_pass"
        if all(checks.values())
        else "functional_subject_repair_dependence_audit_partial"
    )
    next_action = (
        "Open the next behavior-changing slice on priority repair cases "
        f"{', '.join(item['case_id'] for item in priority_cases)}; target repair_case_count <= {target_repair_case_count} "
        "on the next #94 rerun before making stronger runtime-efficacy claims."
        if priority_cases
        else "Inspect runtime repair traces manually before creating a behavior-changing slice."
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "claim_ceiling": "Functional Subject repair-dependence audit local workflow candidate pass",
        "source_report": source_report,
        "source_status": report.get("status"),
        "source_judge_verdict": (report.get("gpt55_judge") or {}).get("verdict")
        if isinstance(report.get("gpt55_judge"), dict)
        else None,
        "case_count": case_count,
        "clean_first_pass_count": clean_first_pass_count,
        "repair_case_count": repair_case_count,
        "target_repair_case_count": target_repair_case_count,
        "class_counts": dict(sorted(class_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
        "repair_cases": repair_cases,
        "priority_cases": priority_cases,
        "checks": checks,
        "next_action": next_action,
        "not_claimed": [
            "runtime repair dependence solved",
            "runtime efficacy",
            "stable user benefit",
            "durable memory efficacy",
            "live autonomy",
            "consciousness",
            "real subjective experience",
            "independent personhood",
        ],
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Functional Subject Repair-Dependence Audit",
        "",
        f"status = `{report.get('status')}`",
        f"source_report = `{report.get('source_report')}`",
        f"source_status = `{report.get('source_status')}`",
        f"source_judge_verdict = `{report.get('source_judge_verdict')}`",
        f"clean_first_pass = `{report.get('clean_first_pass_count')}/{report.get('case_count')}`",
        f"repair_case_count = `{report.get('repair_case_count')}`",
        f"target_repair_case_count = `{report.get('target_repair_case_count')}`",
        "",
        "## Priority Cases",
        "",
        "| case | blocker | owner | priority | next slice |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in _as_list(report.get("priority_cases")):
        lines.append(
            f"| `{item.get('case_id')}` | `{item.get('blocker_class')}` | `{item.get('owner')}` | `{item.get('priority')}` | {item.get('recommended_slice')} |"
        )
    lines.extend([
        "",
        "## All Repair Cases",
        "",
        "| case | repair types | blocker | owner | zeno class | priority |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for item in _as_list(report.get("repair_cases")):
        repair_types = ", ".join(item.get("repair_types") or [])
        lines.append(
            f"| `{item.get('case_id')}` | {repair_types or 'none'} | `{item.get('blocker_class')}` | `{item.get('owner')}` | `{item.get('zeno_class')}` | `{item.get('priority')}` |"
        )
    lines.extend([
        "",
        "## Next Action",
        "",
        str(report.get("next_action") or ""),
        "",
        "## What This Does Not Prove",
        "",
    ])
    for item in _as_list(report.get("not_claimed")):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def run(*, report_path: Path, out_dir: Path) -> dict[str, Any]:
    source = json.loads(report_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = build_repair_dependence_audit(source, source_report=str(report_path))
    (out_dir / "functional_subject_repair_dependence_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "functional_subject_repair_dependence_audit.md").write_text(
        format_markdown(audit),
        encoding="utf-8",
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Functional Subject runtime-repair dependence from a trial report.")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    audit = run(report_path=args.report, out_dir=args.out)
    print(json.dumps({
        "status": audit["status"],
        "json": str(args.out / "functional_subject_repair_dependence_audit.json"),
        "markdown": str(args.out / "functional_subject_repair_dependence_audit.md"),
        "repair_case_count": audit["repair_case_count"],
        "priority_cases": [item["case_id"] for item in audit["priority_cases"]],
        "next_action": audit["next_action"],
    }, ensure_ascii=False, indent=2))
    return 0 if audit["status"].endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
