#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
SCORED_JSON = ARTIFACT_ROOT / "TRIAL1_HARD_SET_RERUN_SCORED_CURRENT.json"
CAUSAL_JSON = ARTIFACT_ROOT / "TRIAL1_HARD_SET_CAUSAL_SEPARATION_CURRENT.json"
OUTPUT_JSON = ARTIFACT_ROOT / "TRIAL1_REDESIGNED_ABLATION_EVALUATION_CURRENT.json"
OUTPUT_MD = ARTIFACT_ROOT / "TRIAL1_REDESIGNED_ABLATION_EVALUATION_CURRENT.md"

PUBLIC_PATH_SEVER_ID = "trial1_ablation_counterfactual_public_path_sever"
ALTERNATIVE_ISOLATION_ID = "trial1_ablation_alternative_explanation_isolation"
POSITIVE_BUCKET_IDS = {"counterfactual_isolation", "restart_restore_boundary_cases"}

GT_MEAN_WEIGHTED_GAP = 0.10
GT_PUBLIC_GAP_CASE_RATE = 0.50
APPROX_ABS_MEAN_WEIGHTED_GAP = 0.05
APPROX_PUBLIC_GAP_CASE_RATE = 0.25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply frozen thresholds to the Trial-1 redesigned-ablation rerun")
    parser.add_argument("--scored-report", type=Path, default=SCORED_JSON)
    parser.add_argument("--causal-report", type=Path, default=CAUSAL_JSON)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUTPUT_MD)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _select_strongest_ablation(scored: Dict[str, Any]) -> str:
    candidates = [PUBLIC_PATH_SEVER_ID, ALTERNATIVE_ISOLATION_ID]
    ranked = sorted(
        candidates,
        key=lambda variant_id: (
            float(scored["variant_scores"][variant_id]["scores"]["weighted_support_score"]),
            float(scored["variant_scores"][variant_id]["coverage"]["public_shift"]),
            float(scored["variant_scores"][variant_id]["scores"]["decision_adjacent_score"]),
        ),
        reverse=True,
    )
    return ranked[0]


def _pair_cases(causal: Dict[str, Any], variant_id: str) -> list[Dict[str, Any]]:
    current = causal["current_diagnosis"]
    if current["strongest_ablation_id"] == variant_id:
        return list(current["candidate_vs_counterfactual_ablation"]["cases"])
    if current["neighboring_ablation_id"] == variant_id:
        return list(current["candidate_vs_neighboring_ablation"]["cases"])
    raise KeyError(f"variant_id not present in causal diagnosis: {variant_id}")


def _evaluate_relation(scored: Dict[str, Any], causal: Dict[str, Any], variant_id: str) -> Dict[str, Any]:
    separation = scored["ablation_separation"]["by_ablation"][variant_id]
    cases = _pair_cases(causal, variant_id)
    positive_cases = [case for case in cases if str(case["bucket_id"]) in POSITIVE_BUCKET_IDS]
    positive_case_count = len(positive_cases)
    public_gap_case_count = sum(1 for case in positive_cases if case["verdict"] == "gap")
    trace_only_case_count = sum(1 for case in positive_cases if case["verdict"] == "trace_only_no_gap")
    private_only_case_count = sum(1 for case in positive_cases if case["verdict"] == "private_only_no_gap")
    public_gap_case_rate = (public_gap_case_count / positive_case_count) if positive_case_count else 0.0
    mean_weighted_gap = float(separation["mean_weighted_gap"])

    if mean_weighted_gap >= GT_MEAN_WEIGHTED_GAP and public_gap_case_rate >= GT_PUBLIC_GAP_CASE_RATE:
        relation = "candidate_gt_ablation"
    elif abs(mean_weighted_gap) < APPROX_ABS_MEAN_WEIGHTED_GAP and public_gap_case_rate < APPROX_PUBLIC_GAP_CASE_RATE:
        relation = "candidate_approx_ablation"
    elif mean_weighted_gap <= -APPROX_ABS_MEAN_WEIGHTED_GAP:
        relation = "candidate_lt_ablation"
    else:
        relation = "indeterminate"

    return {
        "variant_id": variant_id,
        "mean_weighted_gap": round(mean_weighted_gap, 4),
        "positive_gap_case_count": int(separation["positive_gap_case_count"]),
        "positive_case_count": positive_case_count,
        "public_gap_case_count": public_gap_case_count,
        "public_gap_case_rate": round(public_gap_case_rate, 4),
        "trace_only_case_count": trace_only_case_count,
        "private_only_case_count": private_only_case_count,
        "relation": relation,
    }


def build_report(scored: Dict[str, Any], causal: Dict[str, Any]) -> Dict[str, Any]:
    strongest_ablation_id = _select_strongest_ablation(scored)
    public_path_relation = _evaluate_relation(scored, causal, PUBLIC_PATH_SEVER_ID)
    alternative_relation = _evaluate_relation(scored, causal, ALTERNATIVE_ISOLATION_ID)
    strongest_relation = public_path_relation if strongest_ablation_id == PUBLIC_PATH_SEVER_ID else alternative_relation
    candidate_penalty = float(scored["variant_scores"][scored["candidate_id"]]["scores"]["negative_control_penalty"])

    if strongest_relation["relation"] != "candidate_gt_ablation":
        final_decision = "demote_current_claim"
        why = "candidate does not beat the redesigned strongest ablation on frozen public thresholds"
    elif public_path_relation["relation"] != "candidate_gt_ablation":
        final_decision = "demote_current_claim"
        why = "candidate does not beat the public-path-sever ablation, so counterfactual-specific public contribution remains unproven"
    elif candidate_penalty != 0.0:
        final_decision = "demote_current_claim"
        why = "negative controls are not clean"
    else:
        final_decision = "keep_claim_provisional"
        why = "candidate beats the redesigned strongest ablation and specifically beats the public-path-sever ablation on frozen public thresholds"

    return {
        "generated_at": _now_iso(),
        "source_scored_report": "",
        "source_causal_report": "",
        "thresholds": {
            "candidate_gt_ablation": {
                "mean_weighted_gap_gte": GT_MEAN_WEIGHTED_GAP,
                "public_gap_case_rate_gte": GT_PUBLIC_GAP_CASE_RATE,
            },
            "candidate_approx_ablation": {
                "abs_mean_weighted_gap_lt": APPROX_ABS_MEAN_WEIGHTED_GAP,
                "public_gap_case_rate_lt": APPROX_PUBLIC_GAP_CASE_RATE,
            },
        },
        "strongest_ablation_id": strongest_ablation_id,
        "candidate_negative_control_penalty": round(candidate_penalty, 4),
        "relations": {
            PUBLIC_PATH_SEVER_ID: public_path_relation,
            ALTERNATIVE_ISOLATION_ID: alternative_relation,
        },
        "final_decision": {
            "decision": final_decision,
            "why": why,
        },
    }


def _render_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Redesigned Ablation Evaluation",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- strongest_ablation_id: `{report['strongest_ablation_id']}`",
        f"- final_decision: `{report['final_decision']['decision']}`",
        f"- why: {report['final_decision']['why']}",
        "",
        "## Frozen Thresholds",
        "",
        f"- `candidate > ablation`: mean_weighted_gap >= `{GT_MEAN_WEIGHTED_GAP:.2f}` and public_gap_case_rate >= `{GT_PUBLIC_GAP_CASE_RATE:.2f}`",
        f"- `candidate ≈ ablation`: abs(mean_weighted_gap) < `{APPROX_ABS_MEAN_WEIGHTED_GAP:.2f}` and public_gap_case_rate < `{APPROX_PUBLIC_GAP_CASE_RATE:.2f}`",
        "",
        "## Per-Ablation Relation",
        "",
        "| Ablation | Relation | Mean Gap | Public Gap Cases | Positive Cases | Public Gap Rate | Trace-Only Cases | Private-Only Cases |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant_id, relation in report["relations"].items():
        lines.append(
            f"| `{variant_id}` | `{relation['relation']}` | {relation['mean_weighted_gap']:.4f} | "
            f"{relation['public_gap_case_count']} | {relation['positive_case_count']} | "
            f"{relation['public_gap_case_rate']:.4f} | {relation['trace_only_case_count']} | "
            f"{relation['private_only_case_count']} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- This report uses the frozen representation-neutral scorer outputs only.",
            "- Trace-only differences can support admission, but they do not satisfy the `candidate > ablation` threshold.",
            "- No repo-level state upgrade is implied by this diagnostic report.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parsed = parse_args()
    scored = _load_json(parsed.scored_report)
    causal = _load_json(parsed.causal_report)
    report = build_report(scored, causal)
    report["source_scored_report"] = str(parsed.scored_report)
    report["source_causal_report"] = str(parsed.causal_report)
    _write_json(parsed.output_json, report)
    parsed.output_md.write_text(_render_md(report), encoding="utf-8")
    print(f"Wrote {parsed.output_json}")
    print(f"Wrote {parsed.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
