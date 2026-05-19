#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
DEFAULT_INPUT = ARTIFACT_ROOT / "TRIAL2_PUBLIC_DRIVER_RERUN_SCORED_CURRENT.json"
DEFAULT_OUTPUT_JSON = ARTIFACT_ROOT / "TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json"
DEFAULT_OUTPUT_MD = ARTIFACT_ROOT / "TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.md"

COUNTERFACTUAL_SEVER_ID = "trial1_ablation_counterfactual_public_path_sever"
CORRECTION_SEVER_ID = "trial2_ablation_correction_public_path_sever"
VIABILITY_SEVER_ID = "trial2_ablation_viability_public_path_sever"

SEVER_TO_HYPOTHESIS = {
    COUNTERFACTUAL_SEVER_ID: "H1 counterfactual low-success guard",
    CORRECTION_SEVER_ID: "H2 correction-pressure public guard",
    VIABILITY_SEVER_ID: "H3 viability-pressure public guard",
}

TOP_GAP_MIN = 0.0
MIN_POSITIVE_GAP_CASE_COUNT = 2
NON_TOP_GAP_MAX = 0.01
TIE_GAP_DELTA = 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Trial-2 public-driver rerun under frozen decision rules")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_ranking(scored: Dict[str, Any]) -> list[Dict[str, Any]]:
    separation = dict(scored.get("ablation_separation", {}).get("by_ablation", {}))
    ranking: list[Dict[str, Any]] = []
    for variant_id in (
        COUNTERFACTUAL_SEVER_ID,
        CORRECTION_SEVER_ID,
        VIABILITY_SEVER_ID,
    ):
        payload = dict(separation.get(variant_id) or {})
        if not payload:
            raise ValueError(f"missing ablation separation for {variant_id}")
        ranking.append(
            {
                "variant_id": variant_id,
                "hypothesis": SEVER_TO_HYPOTHESIS[variant_id],
                "mean_weighted_gap": float(payload.get("mean_weighted_gap", 0.0)),
                "positive_gap_case_count": int(payload.get("positive_gap_case_count", 0)),
                "case_gaps": list(payload.get("case_gaps") or []),
            }
        )
    ranking.sort(
        key=lambda item: (
            item["mean_weighted_gap"],
            item["positive_gap_case_count"],
        ),
        reverse=True,
    )
    return ranking


def evaluate(scored: Dict[str, Any]) -> Dict[str, Any]:
    ranking = build_ranking(scored)
    top = ranking[0]
    second = ranking[1]
    others = ranking[1:]

    top_gap = float(top["mean_weighted_gap"])
    top_cases = int(top["positive_gap_case_count"])
    second_gap = float(second["mean_weighted_gap"])

    unique_top = (top_gap - second_gap) >= TIE_GAP_DELTA
    non_top_small = all(float(item["mean_weighted_gap"]) <= NON_TOP_GAP_MAX for item in others)
    identified = (
        top_gap > TOP_GAP_MIN
        and top_cases >= MIN_POSITIVE_GAP_CASE_COUNT
        and non_top_small
        and unique_top
    )

    if identified:
        decision = "close"
        rationale = (
            "A single sever ablation uniquely carries the non-zero public gap while the "
            "other sever ablations remain near candidate. Under the frozen hard set and scorer, "
            "this is enough to identify the current bounded active public driver and close Trial-2."
        )
    else:
        decision = "close"
        rationale = (
            "The frozen rerun did not produce a uniquely dominant sever ablation under the "
            "pre-registered thresholds. Trial-2 closes as underdefined rather than expanding the suite."
        )

    return {
        "generated_at": now_iso(),
        "source_scored_report": str(scored.get("source_artifact") or ""),
        "thresholds": {
            "top_gap_min": TOP_GAP_MIN,
            "min_positive_gap_case_count": MIN_POSITIVE_GAP_CASE_COUNT,
            "non_top_gap_max": NON_TOP_GAP_MAX,
            "tie_gap_delta": TIE_GAP_DELTA,
        },
        "ranking": ranking,
        "top_hypothesis": top["hypothesis"],
        "identified_active_public_driver": top["hypothesis"] if identified else None,
        "identified_variant_id": top["variant_id"] if identified else None,
        "bounded_claim": (
            f"Under the existing scorer and hard set, {top['hypothesis']} is the current bounded active public driver."
            if identified
            else "No single bounded active public driver was identified under the frozen scorer and hard set."
        ),
        "non_claims": [
            "This does not identify a universal MVS causal core.",
            "This does not restore any prior public-efficacy claim.",
            "This does not upgrade repo-level state or runtime evidence.",
        ],
        "milestone_decision": decision,
        "identified": identified,
        "rationale": rationale,
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# Trial-2 Public Driver Decision",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- milestone_decision: `{payload['milestone_decision']}`",
        f"- identified: `{str(payload['identified']).lower()}`",
        "",
        "## Ranking",
        "",
    ]
    for item in payload["ranking"]:
        lines.extend(
            [
                f"- `{item['hypothesis']}`",
                f"  - variant_id: `{item['variant_id']}`",
                f"  - mean_weighted_gap: `{item['mean_weighted_gap']:.4f}`",
                f"  - positive_gap_case_count: `{item['positive_gap_case_count']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            f"- bounded_claim: {payload['bounded_claim']}",
        ]
    )
    for line in payload["non_claims"]:
        lines.append(f"- non_claim: {line}")
    lines.extend(
        [
            "",
            "## Rationale",
            "",
            payload["rationale"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    scored = load_json(args.input)
    payload = evaluate(scored)
    write_json(args.output_json, payload)
    write_md(args.output_md, render_markdown(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
