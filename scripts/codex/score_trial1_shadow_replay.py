#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
INPUT_JSON = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_CURRENT.json"
SCORED_JSON = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_SCORED_CURRENT.json"
SCORED_MD = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_SCORED_CURRENT.md"
CAUSAL_MD = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_CAUSAL_TABLE_CURRENT.md"

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
WEIGHTS = {
    "downstream_decision_change": 0.45,
    "response_tendency_change": 0.25,
    "host_policy_change": 0.20,
    "corrective_trace_presence": 0.10,
}
DEFAULT_POSITIVE_TRIGGER_BUCKETS = {
    "correction_override",
    "tension_driven_divergence",
    "failure_to_revision",
    "restart_restore_boundary_cases",
}
DEFAULT_STABILITY_BUCKETS = {"identity_continuity"}
DEFAULT_NEGATIVE_CONTROL_BUCKETS = {"negative_controls"}


@dataclass
class CaseScore:
    variant_id: str
    case_id: str
    bucket_id: str
    bucket_role: str
    evaluation_step_ids: list[str]
    downstream_decision_change: float
    response_tendency_change: float
    host_policy_change: float
    corrective_trace_presence: float
    weighted_public_score: float
    negative_control_penalty: float
    stability_penalty: float
    any_shift: bool
    public_shift: bool
    why_scored: list[str]
    causal_fields: list[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "case_id": self.case_id,
            "bucket_id": self.bucket_id,
            "bucket_role": self.bucket_role,
            "evaluation_step_ids": self.evaluation_step_ids,
            "downstream_decision_change": self.downstream_decision_change,
            "response_tendency_change": self.response_tendency_change,
            "host_policy_change": self.host_policy_change,
            "corrective_trace_presence": self.corrective_trace_presence,
            "weighted_public_score": self.weighted_public_score,
            "negative_control_penalty": self.negative_control_penalty,
            "stability_penalty": self.stability_penalty,
            "any_shift": self.any_shift,
            "public_shift": self.public_shift,
            "why_scored": self.why_scored,
            "causal_fields": self.causal_fields,
        }


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _load_report(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a Trial-1 shadow replay artifact")
    parser.add_argument("--input", type=Path, default=INPUT_JSON)
    parser.add_argument("--output-json", type=Path, default=SCORED_JSON)
    parser.add_argument("--output-md", type=Path, default=SCORED_MD)
    parser.add_argument("--causal-md", type=Path, default=CAUSAL_MD)
    parser.add_argument(
        "--positive-buckets",
        nargs="*",
        default=sorted(DEFAULT_POSITIVE_TRIGGER_BUCKETS),
    )
    parser.add_argument(
        "--stability-buckets",
        nargs="*",
        default=sorted(DEFAULT_STABILITY_BUCKETS),
    )
    parser.add_argument(
        "--negative-control-buckets",
        nargs="*",
        default=sorted(DEFAULT_NEGATIVE_CONTROL_BUCKETS),
    )
    return parser.parse_args()


def _bucket_role(
    bucket_id: str,
    *,
    positive_trigger_buckets: set[str],
    stability_buckets: set[str],
    negative_control_buckets: set[str],
) -> str:
    if bucket_id in positive_trigger_buckets:
        return "positive_trigger"
    if bucket_id in stability_buckets:
        return "stability_control"
    if bucket_id in negative_control_buckets:
        return "negative_control"
    return "unknown"


def _normalize_policy(step: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(step.get("policy_hint") or {})
    return {key: policy.get(key) for key in PUBLIC_POLICY_KEYS}


def _normalize_tendency(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = dict(step.get("response_tendency") or {})
    return {key: tendency.get(key) for key in RESPONSE_TENDENCY_KEYS}


def _decision_surface(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = _normalize_tendency(step)
    policy = _normalize_policy(step)
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


def _complete_corrective_trace(step: Dict[str, Any]) -> bool:
    trace = dict((step.get("memory_update") or {}).get("corrective_trace") or {})
    required = ("trigger", "actual_outcome", "adjustment_applied", "next_guard")
    return all(trace.get(key) not in (None, "", []) for key in required)


def _find_eval_indices(steps: list[Dict[str, Any]], bucket_role: str) -> list[int]:
    if bucket_role == "positive_trigger":
        for idx, step in enumerate(steps):
            if step.get("kind") == "tool_result":
                return list(range(idx, len(steps)))
        return [len(steps) - 1] if steps else []
    if bucket_role in {"stability_control", "negative_control"}:
        return list(range(len(steps)))
    return [len(steps) - 1] if steps else []


def _diff_fields(
    *,
    baseline: Dict[str, Any],
    variant: Dict[str, Any],
    keys: Iterable[str],
    category: str,
    step_id: str,
) -> list[Dict[str, Any]]:
    diffs: list[Dict[str, Any]] = []
    for key in keys:
        left = baseline.get(key)
        right = variant.get(key)
        if left != right:
            diffs.append(
                {
                    "category": category,
                    "field": key,
                    "step_id": step_id,
                    "baseline_value": left,
                    "variant_value": right,
                }
            )
    return diffs


def _score_case(
    *,
    variant_id: str,
    baseline_case: Dict[str, Any],
    variant_case: Dict[str, Any],
    positive_trigger_buckets: set[str],
    stability_buckets: set[str],
    negative_control_buckets: set[str],
) -> CaseScore:
    bucket_id = str(variant_case["bucket_id"])
    bucket_role = _bucket_role(
        bucket_id,
        positive_trigger_buckets=positive_trigger_buckets,
        stability_buckets=stability_buckets,
        negative_control_buckets=negative_control_buckets,
    )
    baseline_steps = list(baseline_case.get("steps") or [])
    variant_steps = list(variant_case.get("steps") or [])
    baseline_by_step = {str(step["step_id"]): step for step in baseline_steps}
    eval_indices = _find_eval_indices(variant_steps, bucket_role)
    evaluation_step_ids = [str(variant_steps[idx]["step_id"]) for idx in eval_indices]

    decision_changes = []
    tendency_ratios = []
    policy_ratios = []
    trace_shifts = []
    causal_fields: list[Dict[str, Any]] = []
    why_scored: list[str] = []

    for idx in eval_indices:
        variant_step = variant_steps[idx]
        step_id = str(variant_step["step_id"])
        baseline_step = baseline_by_step.get(step_id, {})
        baseline_decision = _decision_surface(baseline_step)
        variant_decision = _decision_surface(variant_step)
        if baseline_decision != variant_decision:
            decision_changes.append(1.0)
            causal_fields.append(
                {
                    "category": "downstream_decision_change",
                    "field": "decision_surface",
                    "step_id": step_id,
                    "baseline_value": baseline_decision,
                    "variant_value": variant_decision,
                }
            )
            why_scored.append(
                f"decision@{step_id}: {_decision_surface_label(baseline_decision)} -> "
                f"{_decision_surface_label(variant_decision)}"
            )
        else:
            decision_changes.append(0.0)

        tendency_diffs = _diff_fields(
            baseline=_normalize_tendency(baseline_step),
            variant=_normalize_tendency(variant_step),
            keys=RESPONSE_TENDENCY_KEYS,
            category="response_tendency_change",
            step_id=step_id,
        )
        tendency_ratios.append(len(tendency_diffs) / len(RESPONSE_TENDENCY_KEYS))
        if tendency_diffs:
            causal_fields.extend(tendency_diffs)
            changed = ", ".join(field["field"] for field in tendency_diffs)
            why_scored.append(f"tendency@{step_id}: {changed}")

        policy_diffs = _diff_fields(
            baseline=_normalize_policy(baseline_step),
            variant=_normalize_policy(variant_step),
            keys=PUBLIC_POLICY_KEYS,
            category="host_policy_change",
            step_id=step_id,
        )
        policy_ratios.append(len(policy_diffs) / len(PUBLIC_POLICY_KEYS))
        if policy_diffs:
            causal_fields.extend(policy_diffs)
            changed = ", ".join(field["field"] for field in policy_diffs)
            why_scored.append(f"policy@{step_id}: {changed}")

        baseline_trace = _complete_corrective_trace(baseline_step)
        variant_trace = _complete_corrective_trace(variant_step)
        trace_shift = 1.0 if variant_trace and not baseline_trace else 0.0
        trace_shifts.append(trace_shift)
        if trace_shift > 0.0:
            trace = dict((variant_step.get("memory_update") or {}).get("corrective_trace") or {})
            causal_fields.append(
                {
                    "category": "corrective_trace_presence",
                    "field": "corrective_trace",
                    "step_id": step_id,
                    "baseline_value": None,
                    "variant_value": trace,
                }
            )
            why_scored.append(f"trace@{step_id}: corrective_trace absent -> present")

    decision_score = max(decision_changes, default=0.0)
    tendency_score = max(tendency_ratios, default=0.0)
    policy_score = max(policy_ratios, default=0.0)
    trace_score = max(trace_shifts, default=0.0)
    weighted_public_score = (
        WEIGHTS["downstream_decision_change"] * decision_score
        + WEIGHTS["response_tendency_change"] * tendency_score
        + WEIGHTS["host_policy_change"] * policy_score
        + WEIGHTS["corrective_trace_presence"] * trace_score
    )

    negative_control_penalty = weighted_public_score if bucket_role == "negative_control" else 0.0
    stability_penalty = weighted_public_score if bucket_role == "stability_control" else 0.0
    any_shift = any(value > 0.0 for value in (decision_score, tendency_score, policy_score, trace_score))
    public_shift = any(value > 0.0 for value in (decision_score, tendency_score, policy_score))
    if not why_scored:
        why_scored.append("no scored public shift detected in evaluation window")

    return CaseScore(
        variant_id=variant_id,
        case_id=str(variant_case["case_id"]),
        bucket_id=bucket_id,
        bucket_role=bucket_role,
        evaluation_step_ids=evaluation_step_ids,
        downstream_decision_change=decision_score,
        response_tendency_change=tendency_score,
        host_policy_change=policy_score,
        corrective_trace_presence=trace_score,
        weighted_public_score=round(weighted_public_score, 4),
        negative_control_penalty=round(negative_control_penalty, 4),
        stability_penalty=round(stability_penalty, 4),
        any_shift=any_shift,
        public_shift=public_shift,
        why_scored=why_scored,
        causal_fields=causal_fields,
    )


def _score_variant(
    variant_id: str,
    report: Dict[str, Any],
    *,
    positive_trigger_buckets: set[str],
    stability_buckets: set[str],
    negative_control_buckets: set[str],
) -> Dict[str, Any]:
    baseline_cases = {
        case["case_id"]: case for case in report["results_by_variant"][report["contract"]["baseline_id"]]
    }
    variant_cases = list(report["results_by_variant"].get(variant_id) or [])
    case_scores = [
        _score_case(
            variant_id=variant_id,
            baseline_case=baseline_cases[str(case["case_id"])],
            variant_case=case,
            positive_trigger_buckets=positive_trigger_buckets,
            stability_buckets=stability_buckets,
            negative_control_buckets=negative_control_buckets,
        )
        for case in variant_cases
    ]
    positive_cases = [case for case in case_scores if case.bucket_role == "positive_trigger"]
    negative_cases = [case for case in case_scores if case.bucket_role == "negative_control"]
    stability_cases = [case for case in case_scores if case.bucket_role == "stability_control"]

    decision_mean = _mean(case.downstream_decision_change for case in positive_cases)
    tendency_mean = _mean(case.response_tendency_change for case in positive_cases)
    policy_mean = _mean(case.host_policy_change for case in positive_cases)
    trace_mean = _mean(case.corrective_trace_presence for case in positive_cases)
    weighted_support_score = _mean(case.weighted_public_score for case in positive_cases)
    negative_penalty = _mean(case.negative_control_penalty for case in negative_cases)
    stability_penalty = _mean(case.stability_penalty for case in stability_cases)

    any_shift_coverage = _mean(1.0 if case.any_shift else 0.0 for case in positive_cases)
    public_shift_coverage = _mean(1.0 if case.public_shift else 0.0 for case in positive_cases)
    decision_change_coverage = _mean(
        1.0 if case.downstream_decision_change > 0.0 else 0.0 for case in positive_cases
    )
    trace_shift_coverage = _mean(
        1.0 if case.corrective_trace_presence > 0.0 else 0.0 for case in positive_cases
    )
    trace_only_support = (
        trace_shift_coverage > 0.0
        and decision_change_coverage == 0.0
        and _mean(case.response_tendency_change for case in positive_cases) == 0.0
        and _mean(case.host_policy_change for case in positive_cases) == 0.0
    )

    admission_passed = (
        negative_penalty == 0.0
        and stability_penalty <= 0.05
        and (trace_shift_coverage >= 0.50 or weighted_support_score >= 0.10 or any_shift_coverage >= 0.50)
    )
    decision_adjacent_score = 0.60 * tendency_mean + 0.40 * policy_mean
    decision_adjacent_passed = (
        admission_passed
        and negative_penalty == 0.0
        and public_shift_coverage >= 0.50
        and decision_adjacent_score >= 0.10
    )

    return {
        "variant_id": variant_id,
        "component_means": {
            "downstream_decision_change": round(decision_mean, 4),
            "response_tendency_change": round(tendency_mean, 4),
            "host_policy_change": round(policy_mean, 4),
            "corrective_trace_presence": round(trace_mean, 4),
        },
        "coverage": {
            "any_shift": round(any_shift_coverage, 4),
            "public_shift": round(public_shift_coverage, 4),
            "decision_change": round(decision_change_coverage, 4),
            "trace_shift": round(trace_shift_coverage, 4),
        },
        "scores": {
            "weighted_support_score": round(weighted_support_score, 4),
            "decision_adjacent_score": round(decision_adjacent_score, 4),
            "negative_control_penalty": round(negative_penalty, 4),
            "stability_penalty": round(stability_penalty, 4),
        },
        "levels": {
            "admission_passed": admission_passed,
            "decision_adjacent_passed": decision_adjacent_passed,
            "replay_efficacy_passed": False,  # filled after ablation separation is known
        },
        "trace_only_support": trace_only_support,
        "per_case": [case.to_dict() for case in case_scores],
    }


def _compute_ablation_separation(
    *,
    candidate_variant_id: str,
    candidate_result: Dict[str, Any],
    scored_variants: Dict[str, Any],
) -> Dict[str, Any]:
    candidate_cases = {entry["case_id"]: entry for entry in candidate_result["per_case"]}
    separation: Dict[str, Any] = {}
    min_weighted_gap = None
    for variant_id, result in scored_variants.items():
        if variant_id == candidate_variant_id or "ablation" not in variant_id:
            continue
        gaps = []
        case_gaps = []
        for entry in result["per_case"]:
            if entry["bucket_role"] != "positive_trigger":
                continue
            candidate_case = candidate_cases[entry["case_id"]]
            weighted_gap = round(
                float(candidate_case["weighted_public_score"]) - float(entry["weighted_public_score"]),
                4,
            )
            case_gaps.append(
                {
                    "case_id": entry["case_id"],
                    "weighted_gap": weighted_gap,
                    "decision_gap": round(
                        float(candidate_case["downstream_decision_change"])
                        - float(entry["downstream_decision_change"]),
                        4,
                    ),
                    "response_gap": round(
                        float(candidate_case["response_tendency_change"])
                        - float(entry["response_tendency_change"]),
                        4,
                    ),
                    "policy_gap": round(
                        float(candidate_case["host_policy_change"]) - float(entry["host_policy_change"]),
                        4,
                    ),
                    "trace_gap": round(
                        float(candidate_case["corrective_trace_presence"])
                        - float(entry["corrective_trace_presence"]),
                        4,
                    ),
                }
            )
            gaps.append(weighted_gap)
        mean_gap = _mean(gaps)
        min_weighted_gap = mean_gap if min_weighted_gap is None else min(min_weighted_gap, mean_gap)
        separation[variant_id] = {
            "mean_weighted_gap": round(mean_gap, 4),
            "positive_gap_case_count": sum(1 for gap in gaps if gap > 0.0),
            "case_gaps": case_gaps,
        }
    return {
        "minimum_mean_weighted_gap": round(min_weighted_gap or 0.0, 4),
        "by_ablation": separation,
    }


def _finalize_levels(
    *,
    candidate_variant_id: str,
    scored_variants: Dict[str, Any],
    ablation_separation: Dict[str, Any],
) -> None:
    for variant_id, result in scored_variants.items():
        decision_mean = float(result["component_means"]["downstream_decision_change"])
        weighted_support_score = float(result["scores"]["weighted_support_score"])
        negative_penalty = float(result["scores"]["negative_control_penalty"])
        decision_coverage = float(result["coverage"]["decision_change"])
        if variant_id == candidate_variant_id:
            min_gap = float(ablation_separation["minimum_mean_weighted_gap"])
            result["levels"]["replay_efficacy_passed"] = (
                result["levels"]["decision_adjacent_passed"]
                and decision_mean >= 0.25
                and decision_coverage >= 0.50
                and weighted_support_score >= 0.25
                and negative_penalty == 0.0
                and min_gap >= 0.05
                and not result["trace_only_support"]
            )
        else:
            result["levels"]["replay_efficacy_passed"] = False


def _build_scored_report(
    raw_report: Dict[str, Any],
    *,
    input_json: Path,
    positive_trigger_buckets: set[str],
    stability_buckets: set[str],
    negative_control_buckets: set[str],
) -> Dict[str, Any]:
    baseline_id = raw_report["contract"]["baseline_id"]
    candidate_id = raw_report["contract"]["candidate_id"]
    scored_variants = {
        variant_id: _score_variant(
            variant_id,
            raw_report,
            positive_trigger_buckets=positive_trigger_buckets,
            stability_buckets=stability_buckets,
            negative_control_buckets=negative_control_buckets,
        )
        for variant_id in raw_report["variants_run"]
    }
    ablation_separation = _compute_ablation_separation(
        candidate_variant_id=candidate_id,
        candidate_result=scored_variants[candidate_id],
        scored_variants=scored_variants,
    )
    _finalize_levels(
        candidate_variant_id=candidate_id,
        scored_variants=scored_variants,
        ablation_separation=ablation_separation,
    )
    return {
        "generated_at": _now_iso(),
        "scorer_schema_version": "trial1.replay_score.v1",
        "source_artifact": str(input_json),
        "bucket_role_contract": {
            "positive_trigger_buckets": sorted(positive_trigger_buckets),
            "stability_buckets": sorted(stability_buckets),
            "negative_control_buckets": sorted(negative_control_buckets),
        },
        "representation_neutral_ontology": {
            "downstream_decision_change": "normalized host decision surface derived from public response_tendency + canonical policy fields",
            "response_tendency_change": list(RESPONSE_TENDENCY_KEYS),
            "host_policy_change": list(PUBLIC_POLICY_KEYS),
            "corrective_trace_presence": [
                "memory_update.corrective_trace.trigger",
                "memory_update.corrective_trace.actual_outcome",
                "memory_update.corrective_trace.adjustment_applied",
                "memory_update.corrective_trace.next_guard",
            ],
            "ignored_private_fields": [
                "state_snapshot",
                "self_model_delta",
                "drives_delta",
                "policy_hint.shadow_repair_bias",
                "policy_hint.shadow_counterfactual_guard",
                "policy_hint.shadow_tension_active",
            ],
        },
        "weights": WEIGHTS,
        "level_contract": {
            "admission_passed": {
                "rule": "trace-only support may pass admission if negative controls stay clean and stability controls do not regress",
            },
            "decision_adjacent_passed": {
                "rule": "requires representation-neutral public shift coverage plus policy/response score above threshold",
            },
            "replay_efficacy_passed": {
                "rule": "requires downstream decision change coverage and ablation separation; trace-only support is insufficient",
            },
        },
        "baseline_id": baseline_id,
        "candidate_id": candidate_id,
        "challenger_id": raw_report["challenger_id"],
        "challenger_status": raw_report.get("challenger_status"),
        "variant_scores": scored_variants,
        "ablation_separation": ablation_separation,
        "per_case_causal_table": [
            entry
            for variant in raw_report["variants_run"]
            if variant != baseline_id
            for entry in scored_variants[variant]["per_case"]
        ],
    }


def _render_report_md(scored: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Shadow Replay Scored Report",
        "",
        f"- generated_at: `{scored['generated_at']}`",
        f"- source_artifact: `{scored['source_artifact']}`",
        f"- candidate_id: `{scored['candidate_id']}`",
        f"- challenger_status: `{scored['challenger_status']}`",
        "",
        "## Level Summary",
        "",
    ]
    for variant_id, result in scored["variant_scores"].items():
        levels = result["levels"]
        scores = result["scores"]
        components = result["component_means"]
        lines.append(
            f"- `{variant_id}`: admission={levels['admission_passed']}, "
            f"decision_adjacent={levels['decision_adjacent_passed']}, "
            f"replay_efficacy={levels['replay_efficacy_passed']}, "
            f"weighted={scores['weighted_support_score']:.4f}, "
            f"decision={components['downstream_decision_change']:.4f}, "
            f"response={components['response_tendency_change']:.4f}, "
            f"policy={components['host_policy_change']:.4f}, "
            f"trace={components['corrective_trace_presence']:.4f}"
        )
    lines.extend(["", "## Ablation Separation", ""])
    for ablation_id, gap in scored["ablation_separation"]["by_ablation"].items():
        lines.append(
            f"- `{ablation_id}`: mean_weighted_gap={gap['mean_weighted_gap']:.4f}, "
            f"positive_gap_cases={gap['positive_gap_case_count']}"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- `admission_passed` can be supported by trace-only shift, but only when negative controls stay clean.",
            "- `decision_adjacent_passed` requires public-output movement on representation-neutral policy/response surfaces.",
            "- `replay_efficacy_passed` requires downstream decision-surface change and ablation separation. The current Trial-1 artifact does not meet that bar.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_causal_md(scored: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Replay Causal Table",
        "",
        "| Variant | Case | Bucket | Role | Decision | Tendency | Policy | Trace | Weighted | Why |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in scored["per_case_causal_table"]:
        why = "; ".join(entry["why_scored"])
        lines.append(
            f"| `{entry['variant_id']}` | `{entry['case_id']}` | `{entry['bucket_id']}` | `{entry['bucket_role']}` | "
            f"{entry['downstream_decision_change']:.2f} | {entry['response_tendency_change']:.2f} | "
            f"{entry['host_policy_change']:.2f} | {entry['corrective_trace_presence']:.2f} | "
            f"{entry['weighted_public_score']:.2f} | {why} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    positive_trigger_buckets = set(args.positive_buckets)
    stability_buckets = set(args.stability_buckets)
    negative_control_buckets = set(args.negative_control_buckets)
    raw_report = _load_report(args.input)
    scored = _build_scored_report(
        raw_report,
        input_json=args.input,
        positive_trigger_buckets=positive_trigger_buckets,
        stability_buckets=stability_buckets,
        negative_control_buckets=negative_control_buckets,
    )
    _write_json(args.output_json, scored)
    args.output_md.write_text(_render_report_md(scored), encoding="utf-8")
    args.causal_md.write_text(_render_causal_md(scored), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.causal_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
