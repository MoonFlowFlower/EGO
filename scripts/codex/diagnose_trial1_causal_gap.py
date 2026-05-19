#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"

DEFAULT_RAW_REPLAY_JSON = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_CURRENT.json"
DEFAULT_SCORED_REPLAY_JSON = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_SCORED_CURRENT.json"
DEFAULT_HARD_SET_JSON = TASK_ROOT / "TRIAL1_COUNTERFACTUAL_HARD_SET.json"

DEFAULT_REPORT_JSON = ARTIFACT_ROOT / "TRIAL1_CAUSAL_SEPARATION_CURRENT.json"
DEFAULT_REPORT_MD = ARTIFACT_ROOT / "TRIAL1_CAUSAL_SEPARATION_CURRENT.md"
DEFAULT_TABLE_MD = ARTIFACT_ROOT / "TRIAL1_CAUSAL_SEPARATION_TABLE_CURRENT.md"

PUBLIC_POLICY_KEYS = (
    "risk_bias",
    "ask_preferred",
    "closure_bias",
    "should_avoid_commitment_upgrade",
)
RESPONSE_TENDENCY_KEYS = (
    "preferred_mode",
    "preferred_tone",
    "certainty_bound",
    "suggested_next_step",
    "ask_needed",
)
PRIVATE_DIAGNOSTIC_FIELDS = (
    "state_snapshot.counterfactual_success_by_action",
    "memory_update.counterfactual_prediction",
    "policy_hint.shadow_counterfactual_guard",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose Trial-1 causal separation on a scored replay artifact")
    parser.add_argument("--raw-report", type=Path, default=DEFAULT_RAW_REPLAY_JSON)
    parser.add_argument("--scored-report", type=Path, default=DEFAULT_SCORED_REPLAY_JSON)
    parser.add_argument("--hard-set", type=Path, default=DEFAULT_HARD_SET_JSON)
    parser.add_argument(
        "--strongest-ablation-id",
        default="trial1_ablation_minus_counterfactual_writeback",
    )
    parser.add_argument(
        "--neighboring-ablation-id",
        default="trial1_ablation_minus_viability_pressure",
    )
    parser.add_argument("--output-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--table-md", type=Path, default=DEFAULT_TABLE_MD)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _public_policy(step: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(step.get("policy_hint") or {})
    return {key: policy.get(key) for key in PUBLIC_POLICY_KEYS}


def _public_tendency(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = dict(step.get("response_tendency") or {})
    return {key: tendency.get(key) for key in RESPONSE_TENDENCY_KEYS}


def _decision_surface(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = _public_tendency(step)
    policy = _public_policy(step)
    preferred_mode = tendency.get("preferred_mode") or "unknown"
    if preferred_mode in {"repair", "ask", "defer"}:
        lane = preferred_mode
    elif bool(tendency.get("ask_needed")):
        lane = "ask"
    elif tendency.get("suggested_next_step") in {"clarify_or_repair", "request_replan"}:
        lane = "repair"
    elif tendency.get("suggested_next_step") == "prioritize_closure":
        lane = "closure"
    else:
        lane = "continue"
    return {
        "lane": lane,
        "ask_needed": bool(tendency.get("ask_needed")),
        "risk_bias": policy.get("risk_bias"),
        "commitment_guard": bool(policy.get("should_avoid_commitment_upgrade")),
    }


def _decision_surface_label(surface: Dict[str, Any]) -> str:
    return (
        f"{surface.get('lane')}|ask={surface.get('ask_needed')}|"
        f"risk={surface.get('risk_bias')}|guard={surface.get('commitment_guard')}"
    )


def _trace_present(step: Dict[str, Any]) -> bool:
    return bool((step.get("memory_update") or {}).get("corrective_trace"))


def _private_diffs(candidate_step: Dict[str, Any], other_step: Dict[str, Any]) -> List[str]:
    diffs: List[str] = []
    if (
        candidate_step["state_snapshot"].get("counterfactual_success_by_action")
        != other_step["state_snapshot"].get("counterfactual_success_by_action")
    ):
        diffs.append("state_snapshot.counterfactual_success_by_action")
    if (
        (candidate_step.get("memory_update") or {}).get("counterfactual_prediction")
        != (other_step.get("memory_update") or {}).get("counterfactual_prediction")
    ):
        diffs.append("memory_update.counterfactual_prediction")
    if (
        (candidate_step.get("policy_hint") or {}).get("shadow_counterfactual_guard")
        != (other_step.get("policy_hint") or {}).get("shadow_counterfactual_guard")
    ):
        diffs.append("policy_hint.shadow_counterfactual_guard")
    return diffs


def _classify_case_gap(
    *,
    trace_only_steps: int,
    decision_adjacent_steps: int,
    downstream_steps: int,
    private_only_steps: int,
) -> str:
    if downstream_steps > 0:
        return "gap"
    if decision_adjacent_steps > 0:
        return "gap"
    if trace_only_steps > 0:
        return "trace_only_no_gap"
    if private_only_steps > 0:
        return "private_only_no_gap"
    return "no_gap"


def _compare_cases(
    *,
    candidate_case: Dict[str, Any],
    other_case: Dict[str, Any],
    pair_label: str,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    trace_only_steps = 0
    decision_adjacent_steps = 0
    downstream_steps = 0
    private_only_steps = 0
    trace_steps = 0

    for candidate_step, other_step in zip(candidate_case["steps"], other_case["steps"]):
        candidate_policy = _public_policy(candidate_step)
        other_policy = _public_policy(other_step)
        candidate_tendency = _public_tendency(candidate_step)
        other_tendency = _public_tendency(other_step)
        candidate_surface = _decision_surface(candidate_step)
        other_surface = _decision_surface(other_step)
        candidate_trace = _trace_present(candidate_step)
        other_trace = _trace_present(other_step)

        trace_diff = candidate_trace != other_trace
        response_diff = candidate_tendency != other_tendency
        policy_diff = candidate_policy != other_policy
        downstream_diff = candidate_surface != other_surface
        private_diffs = _private_diffs(candidate_step, other_step)

        if trace_diff:
            trace_steps += 1
        if trace_diff and not response_diff and not policy_diff and not downstream_diff:
            trace_only_steps += 1
        if response_diff or policy_diff:
            decision_adjacent_steps += 1
        if downstream_diff:
            downstream_steps += 1
        if private_diffs and not trace_diff and not response_diff and not policy_diff and not downstream_diff:
            private_only_steps += 1

        why_parts: List[str] = []
        if downstream_diff:
            why_parts.append(
                f"downstream: {_decision_surface_label(candidate_surface)} != {_decision_surface_label(other_surface)}"
            )
        if response_diff:
            why_parts.append("response_tendency public fields differ")
        if policy_diff:
            changed = ", ".join(key for key in PUBLIC_POLICY_KEYS if candidate_policy.get(key) != other_policy.get(key))
            why_parts.append(f"policy_hint public fields differ: {changed}")
        if trace_diff:
            why_parts.append(f"corrective_trace present={candidate_trace} vs {other_trace}")
        if private_diffs:
            why_parts.append(f"private-only diffs: {', '.join(private_diffs)}")
        if not why_parts:
            why_parts.append("no representation-neutral gap detected")

        rows.append(
            {
                "pair": pair_label,
                "case_id": candidate_case["case_id"],
                "bucket_id": candidate_case["bucket_id"],
                "step_id": candidate_step["step_id"],
                "trace_only_difference": trace_diff and not response_diff and not policy_diff and not downstream_diff,
                "decision_adjacent_difference": response_diff or policy_diff,
                "host_consumable_downstream_difference": downstream_diff,
                "corrective_trace_difference": trace_diff,
                "private_only_difference": bool(private_diffs)
                and not trace_diff
                and not response_diff
                and not policy_diff
                and not downstream_diff,
                "why_scored": why_parts,
            }
        )

    verdict = _classify_case_gap(
        trace_only_steps=trace_only_steps,
        decision_adjacent_steps=decision_adjacent_steps,
        downstream_steps=downstream_steps,
        private_only_steps=private_only_steps,
    )
    if verdict == "gap":
        verdict_why = "representation-neutral public gap detected"
    elif verdict == "trace_only_no_gap":
        verdict_why = "only trace-level difference observed; hard rule blocks efficacy credit"
    elif verdict == "private_only_no_gap":
        verdict_why = "only private-state difference observed; scorer ontology intentionally ignores it"
    else:
        verdict_why = "no public or trace gap detected"

    return {
        "case_id": candidate_case["case_id"],
        "bucket_id": candidate_case["bucket_id"],
        "pair": pair_label,
        "verdict": verdict,
        "verdict_why": verdict_why,
        "trace_only_step_count": trace_only_steps,
        "decision_adjacent_step_count": decision_adjacent_steps,
        "downstream_step_count": downstream_steps,
        "trace_step_count": trace_steps,
        "private_only_step_count": private_only_steps,
        "rows": rows,
    }


def _summarize_pair(case_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_cases = len(case_summaries)
    total_steps = sum(len(case["rows"]) for case in case_summaries)
    return {
        "case_count": total_cases,
        "step_count": total_steps,
        "gap_case_count": sum(1 for case in case_summaries if case["verdict"] == "gap"),
        "trace_only_case_count": sum(1 for case in case_summaries if case["verdict"] == "trace_only_no_gap"),
        "private_only_case_count": sum(1 for case in case_summaries if case["verdict"] == "private_only_no_gap"),
        "public_gap_step_count": sum(
            case["decision_adjacent_step_count"] + case["downstream_step_count"] for case in case_summaries
        ),
        "private_only_step_count": sum(case["private_only_step_count"] for case in case_summaries),
        "trace_only_step_count": sum(case["trace_only_step_count"] for case in case_summaries),
    }


def _build_current_diagnosis(
    raw_report: Dict[str, Any],
    scored_report: Dict[str, Any],
    *,
    strongest_ablation_id: str,
    neighboring_ablation_id: str,
) -> Dict[str, Any]:
    baseline_id = raw_report["contract"]["baseline_id"]
    candidate_id = raw_report["contract"]["candidate_id"]

    by_variant = {
        variant_id: {case["case_id"]: case for case in cases}
        for variant_id, cases in raw_report["results_by_variant"].items()
    }
    case_ids = list(by_variant[candidate_id].keys())

    cf_cases = [
        _compare_cases(
            candidate_case=by_variant[candidate_id][case_id],
            other_case=by_variant[strongest_ablation_id][case_id],
            pair_label="candidate_vs_counterfactual_ablation",
        )
        for case_id in case_ids
    ]
    neighbor_cases = [
        _compare_cases(
            candidate_case=by_variant[candidate_id][case_id],
            other_case=by_variant[neighboring_ablation_id][case_id],
            pair_label="candidate_vs_neighbor_viability_ablation",
        )
        for case_id in case_ids
    ]

    variant_scores = {
        variant_id: scored_report["variant_scores"][variant_id]
        for variant_id in (
            baseline_id,
            candidate_id,
            strongest_ablation_id,
            neighboring_ablation_id,
        )
    }

    return {
        "baseline_id": baseline_id,
        "candidate_id": candidate_id,
        "strongest_ablation_id": strongest_ablation_id,
        "neighboring_ablation_id": neighboring_ablation_id,
        "variant_score_summary": variant_scores,
        "candidate_vs_counterfactual_ablation": {
            "summary": _summarize_pair(cf_cases),
            "cases": cf_cases,
        },
        "candidate_vs_neighboring_ablation": {
            "summary": _summarize_pair(neighbor_cases),
            "cases": neighbor_cases,
        },
    }


def _build_reachability_diagnosis() -> Dict[str, Any]:
    failure_transitions = []
    for outcome_type, predicted_success, correction_strength in (
        ("blocked", 0.12, 1.0),
        ("failure", 0.18, 1.0),
        ("partial", 0.35, 0.7),
    ):
        failure_transitions.append(
            {
                "outcome_type": outcome_type,
                "after_failure": {
                    "predicted_success": predicted_success,
                    "correction_strength": correction_strength,
                    "correction_path_triggers_public_guard": correction_strength >= 0.6,
                    "counterfactual_path_triggers_public_guard": predicted_success < 0.35,
                },
                "after_success_followup": {
                    "predicted_success": max(0.65, predicted_success),
                    "correction_strength": max(0.0, correction_strength - 0.75),
                    "correction_path_triggers_public_guard": max(0.0, correction_strength - 0.75) >= 0.6,
                    "counterfactual_path_triggers_public_guard": max(0.65, predicted_success) < 0.35,
                },
            }
        )
    return {
        "rule_summary": [
            "failure/blocked updates set both recent_correction_tags and low counterfactual prediction together",
            "derive_policy_hint turns on ask_preferred for either correction_pressure >= 0.6 or viability_pressure >= 0.5 before counterfactual-only isolation matters",
            "success-after-correction decays correction tags but also restores counterfactual prediction to >= 0.65",
            "therefore the current Trial-1 path does not naturally expose a low-prediction/public-gap phase after correction pressure has decayed",
        ],
        "transition_examples": failure_transitions,
        "diagnosis": "current strongest ablation is mis-specified relative to the representation-neutral scorer surface",
    }


def _final_decision(current_diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    cf_summary = current_diagnosis["candidate_vs_counterfactual_ablation"]["summary"]
    if cf_summary["gap_case_count"] == 0 and cf_summary["private_only_case_count"] > 0:
        return {
            "decision": "redesign_ablation",
            "why": [
                "candidate does not beat the strongest ablation on any current representation-neutral case",
                "the strongest ablation differs only on private-state fields the scorer intentionally ignores",
                "the current update rules make counterfactual-only public separation unreachable on the existing Trial-1 path",
            ],
            "claim_change": "demote the narrow claim that counterfactual_writeback is already shown as a replay-efficacy contributor under the current ontology",
        }
    return {
        "decision": "expand replay_suite",
        "why": ["current diagnosis found at least one representation-neutral gap and needs more held-out evidence"],
        "claim_change": "keep current mechanism claim provisional",
    }


def _render_report_md(report: Dict[str, Any]) -> str:
    current = report["current_diagnosis"]
    decision = report["final_decision"]
    lines = [
        "# Trial-1 Causal Separation Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- source_raw: `{report['source_raw_artifact']}`",
        f"- source_scored: `{report['source_scored_artifact']}`",
        f"- hard_set: `{report['hard_replay_set']}`",
        f"- final_decision: `{decision['decision']}`",
        "",
        "## Variant Summary",
        "",
        "| Variant | Admission | Decision Adjacent | Replay Efficacy | Weighted | Decision | Policy | Trace |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for variant_id, payload in current["variant_score_summary"].items():
        levels = payload["levels"]
        component_means = payload["component_means"]
        scores = payload["scores"]
        lines.append(
            f"| `{variant_id}` | `{levels['admission_passed']}` | `{levels['decision_adjacent_passed']}` | "
            f"`{levels['replay_efficacy_passed']}` | {scores['weighted_support_score']:.4f} | "
            f"{component_means['downstream_decision_change']:.4f} | {component_means['host_policy_change']:.4f} | "
            f"{component_means['corrective_trace_presence']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Current Gap",
            "",
            f"- candidate vs strongest ablation gap cases: `{current['candidate_vs_counterfactual_ablation']['summary']['gap_case_count']}`",
            f"- candidate vs strongest ablation private-only cases: `{current['candidate_vs_counterfactual_ablation']['summary']['private_only_case_count']}`",
            f"- candidate vs strongest ablation public-gap steps: `{current['candidate_vs_counterfactual_ablation']['summary']['public_gap_step_count']}`",
            f"- candidate vs neighboring ablation gap cases: `{current['candidate_vs_neighboring_ablation']['summary']['gap_case_count']}`",
            "",
            "## Reachability Diagnosis",
            "",
        ]
    )
    for line in report["reachability_diagnosis"]["rule_summary"]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "## Hard Set",
            "",
            f"- diagnostic_case_count: `{report['hard_set_summary']['case_count']}`",
            f"- positive_isolation_cases: `{report['hard_set_summary']['positive_isolation_case_count']}`",
            f"- negative_control_cases: `{report['hard_set_summary']['negative_control_case_count']}`",
            "- note: this hard set is diagnostic-only and does not upgrade the official replay suite.",
            "",
            "## Decision",
            "",
            f"- `{decision['decision']}`",
        ]
    )
    for reason in decision["why"]:
        lines.append(f"- {reason}")
    lines.append(f"- claim_change: {decision['claim_change']}")
    return "\n".join(lines) + "\n"


def _render_table_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Causal Separation Tables",
        "",
        "## Candidate vs Strongest Ablation",
        "",
        "| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in report["current_diagnosis"]["candidate_vs_counterfactual_ablation"]["cases"]:
        for row in case["rows"]:
            why = "; ".join(row["why_scored"])
            lines.append(
                f"| `{row['case_id']}` | `{row['bucket_id']}` | `{row['step_id']}` | "
                f"`{row['trace_only_difference']}` | `{row['decision_adjacent_difference']}` | "
                f"`{row['host_consumable_downstream_difference']}` | {why} |"
            )
    lines.extend(
        [
            "",
            "## Candidate vs Neighboring Ablation",
            "",
            "| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in report["current_diagnosis"]["candidate_vs_neighboring_ablation"]["cases"]:
        for row in case["rows"]:
            why = "; ".join(row["why_scored"])
            lines.append(
                f"| `{row['case_id']}` | `{row['bucket_id']}` | `{row['step_id']}` | "
                f"`{row['trace_only_difference']}` | `{row['decision_adjacent_difference']}` | "
                f"`{row['host_consumable_downstream_difference']}` | {why} |"
            )
    return "\n".join(lines) + "\n"


def _summarize_hard_set(hard_set: Dict[str, Any]) -> Dict[str, Any]:
    cases = list(hard_set.get("cases") or [])
    return {
        "case_count": len(cases),
        "positive_isolation_case_count": sum(1 for case in cases if case.get("diagnostic_role") == "positive_isolation"),
        "negative_control_case_count": sum(1 for case in cases if case.get("diagnostic_role") == "negative_control"),
        "case_ids": [str(case.get("case_id") or "") for case in cases],
    }


def build_report(
    *,
    raw_report_path: Path,
    scored_report_path: Path,
    hard_set_path: Path,
    strongest_ablation_id: str,
    neighboring_ablation_id: str,
) -> Dict[str, Any]:
    raw_report = _load_json(raw_report_path)
    scored_report = _load_json(scored_report_path)
    hard_set = _load_json(hard_set_path)
    current_diagnosis = _build_current_diagnosis(
        raw_report,
        scored_report,
        strongest_ablation_id=strongest_ablation_id,
        neighboring_ablation_id=neighboring_ablation_id,
    )
    reachability_diagnosis = _build_reachability_diagnosis()
    report = {
        "generated_at": _now_iso(),
        "source_raw_artifact": str(raw_report_path),
        "source_scored_artifact": str(scored_report_path),
        "hard_replay_set": str(hard_set_path),
        "scorer_ontology": {
            "public_policy_keys": list(PUBLIC_POLICY_KEYS),
            "response_tendency_keys": list(RESPONSE_TENDENCY_KEYS),
            "private_diagnostic_fields": list(PRIVATE_DIAGNOSTIC_FIELDS),
        },
        "current_diagnosis": current_diagnosis,
        "reachability_diagnosis": reachability_diagnosis,
        "hard_set_summary": _summarize_hard_set(hard_set),
    }
    report["final_decision"] = _final_decision(current_diagnosis)
    return report


def main() -> int:
    args = parse_args()
    report = build_report(
        raw_report_path=args.raw_report,
        scored_report_path=args.scored_report,
        hard_set_path=args.hard_set,
        strongest_ablation_id=args.strongest_ablation_id,
        neighboring_ablation_id=args.neighboring_ablation_id,
    )
    _write_json(args.output_json, report)
    args.output_md.write_text(_render_report_md(report), encoding="utf-8")
    args.table_md.write_text(_render_table_md(report), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.table_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
