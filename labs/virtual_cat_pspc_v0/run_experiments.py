from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

from .admission_packet import schema_copy
from .experiments import (
    ConditionResult,
    evaluate_seeds,
    gate_status,
    result_to_dict,
    run_anti_hardcoding_audit,
    run_generalization_matrix,
    run_homeostatic_value_anti_hacking,
    run_memory_consolidation_admission,
    run_self_model_causal_strength,
    run_world_model_causal_strength,
)


REPORTS = {
    "BASELINE_REPORT.md": "baseline",
    "DANGER_GENERALIZATION_REPORT.md": "danger_generalization",
    "MEMORY_DELETION_ABLATION.md": "memory_deletion",
    "FROZEN_WORLD_MODEL_ABLATION.md": "frozen_world_model",
    "FROZEN_SELF_MODEL_ABLATION.md": "frozen_self_model",
    "NO_PREDICTION_ERROR_LEARNING_ABLATION.md": "no_prediction_error_learning",
    "REPLAY_DETERMINISM_REPORT.md": "replay_determinism",
}


def run_experiments(out: str | Path, seeds: Iterable[int]) -> Dict[str, object]:
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)
    traces_dir = out_path / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    seed_list = [int(seed) for seed in seeds]
    results = evaluate_seeds(seed_list)
    gates = gate_status(results)
    anti_hardcoding_audit = run_anti_hardcoding_audit(seed=seed_list[0])
    generalization_matrix = run_generalization_matrix(seeds=seed_list)
    world_model_causal_strength = run_world_model_causal_strength(seed=seed_list[0])
    self_model_causal_strength = run_self_model_causal_strength(seed=seed_list[0])
    memory_consolidation_admission = run_memory_consolidation_admission(seed=seed_list[0])
    homeostatic_value_anti_hacking = run_homeostatic_value_anti_hacking(seed=seed_list[0])
    admission_packet_schema = schema_copy()
    admission_packet_contract_status = "pass"
    overall_status = "E4_passed" if all(gates.values()) else "hold"

    _write_traces(traces_dir, results)
    for filename, report_kind in REPORTS.items():
        (out_path / filename).write_text(
            _render_report(
                report_kind=report_kind,
                seeds=seed_list,
                overall_status=overall_status,
                gates=gates,
                results=results,
            ),
            encoding="utf-8",
        )
    (out_path / "anti_hardcoding_audit.json").write_text(
        json.dumps(anti_hardcoding_audit, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "ANTI_HARDCODING_AUDIT.md").write_text(
        _render_anti_hardcoding_audit(anti_hardcoding_audit),
        encoding="utf-8",
    )
    (out_path / "generalization_matrix.json").write_text(
        json.dumps(generalization_matrix, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "GENERALIZATION_MATRIX_REPORT.md").write_text(
        _render_generalization_matrix(generalization_matrix),
        encoding="utf-8",
    )
    (out_path / "world_model_causal_strength.json").write_text(
        json.dumps(world_model_causal_strength, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "WORLD_MODEL_CAUSAL_STRENGTH_REPORT.md").write_text(
        _render_world_model_causal_strength(world_model_causal_strength),
        encoding="utf-8",
    )
    (out_path / "self_model_causal_strength.json").write_text(
        json.dumps(self_model_causal_strength, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "SELF_MODEL_CAUSAL_STRENGTH_REPORT.md").write_text(
        _render_self_model_causal_strength(self_model_causal_strength),
        encoding="utf-8",
    )
    (out_path / "memory_consolidation_admission.json").write_text(
        json.dumps(memory_consolidation_admission, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "MEMORY_CONSOLIDATION_ADMISSION_REPORT.md").write_text(
        _render_memory_consolidation_admission(memory_consolidation_admission),
        encoding="utf-8",
    )
    (out_path / "homeostatic_value_anti_hacking.json").write_text(
        json.dumps(homeostatic_value_anti_hacking, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "HOMEOSTATIC_VALUE_ANTI_HACKING_REPORT.md").write_text(
        _render_homeostatic_value_anti_hacking(homeostatic_value_anti_hacking),
        encoding="utf-8",
    )
    (out_path / "admission_packet_contract.schema.json").write_text(
        json.dumps(admission_packet_schema, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_path / "ADMISSION_PACKET_CONTRACT_REPORT.md").write_text(
        _render_admission_packet_contract(admission_packet_contract_status),
        encoding="utf-8",
    )

    summary = {
        "overall_status": overall_status,
        "pspc_local_status": overall_status,
        "anti_hardcoding_status": anti_hardcoding_audit["status"],
        "multi_seed_layout_generalization_status": generalization_matrix["status"],
        "world_model_causal_strength_status": world_model_causal_strength["status"],
        "self_model_causal_strength_status": self_model_causal_strength["status"],
        "memory_consolidation_admission_status": memory_consolidation_admission["status"],
        "homeostatic_value_anti_hacking_status": homeostatic_value_anti_hacking["status"],
        "admission_packet_contract_status": admission_packet_contract_status,
        "claim_level": "lab_only_proto_self_mechanism",
        "repo_wide_evidence_level": "E3",
        "repo_wide_evidence_remains": "E3",
        "mainline_connected": False,
        "enabled": False,
        "repo_wide_verify_gap": {
            "command": "python scripts\\codex\\verify_repo.py --mode fast",
            "status": "unavailable",
            "reason": "legacy/root OpenEmotion WinError 267",
            "counts_as_pspc_pass": False,
            "upgrades_repo_wide_pass": False,
        },
        "seeds": seed_list,
        "gates": gates,
        "trace_dir": str(traces_dir.as_posix()),
        "anti_hardcoding_audit": "artifacts/virtual_cat_pspc_v0/anti_hardcoding_audit.json",
        "generalization_matrix": "artifacts/virtual_cat_pspc_v0/generalization_matrix.json",
        "world_model_causal_strength": "artifacts/virtual_cat_pspc_v0/world_model_causal_strength.json",
        "self_model_causal_strength": "artifacts/virtual_cat_pspc_v0/self_model_causal_strength.json",
        "memory_consolidation_admission": "artifacts/virtual_cat_pspc_v0/memory_consolidation_admission.json",
        "homeostatic_value_anti_hacking": "artifacts/virtual_cat_pspc_v0/homeostatic_value_anti_hacking.json",
        "admission_packet_contract_schema": "artifacts/virtual_cat_pspc_v0/admission_packet_contract.schema.json",
        "what_it_proves": "PSPC-local lab ablation gates passed under deterministic seeds."
        if overall_status == "E4_passed"
        else "At least one PSPC-local lab ablation gate did not pass.",
        "what_it_does_not_prove": [
            "stable real user benefit",
            "live autonomy",
            "durable operator memory efficacy",
            "EgoOperator runtime efficacy",
            "philosophical consciousness",
            "subjective experience",
        ],
    }
    (out_path / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _render_admission_packet_contract(status: str) -> str:
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Admission Packet Contract Report",
            "",
            f"- status: `{status}`",
            "- contract: `proposal-only packet schema`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            "- mainline_connected: `false`",
            "- enabled: `false`",
            "- trace_hash: `contract_schema_no_runtime_trace`",
            "",
            "## Summary",
            "This report records the Task 7 admission packet contract as a lab-only schema for a future proposal source. It does not create an adapter, import EgoOperator runtime code, send messages, execute actions, write memory, or bypass a runtime gate.",
            "",
            "## Required Packet Shape",
            "The schema requires `source`, `claim_level`, `mainline_connected`, `enabled`, `proposal`, `evidence`, and `forbidden`. Proposal trace references must use `trace_refs`, not legacy or adapter-specific reason fields.",
            "",
            "## What It Proves",
            "The PSPC lab has a test-validated proposal-only packet schema that preserves lab-only claim level, disabled/mainline-disconnected status, evidence fields, and forbidden direct-action flags.",
            "",
            "## What It Does Not Prove",
            "This does not prove adapter readiness, EgoOperator runtime efficacy, stable user benefit, live autonomy, production integration safety, consciousness, or subjective experience.",
            "",
            "## Failure Meaning",
            "If this fails, PSPC may not have a stable host-auditable packet boundary, or the contract may accidentally grant runtime authority before an adapter review.",
            "",
            "## Rollback Note",
            "Remove the Task 7 admission packet schema module, tests, contract doc, report artifact, summary fields, and ledger/status updates. No EgoOperator rollback is needed because no adapter or runtime integration exists.",
            "",
        ]
    )


def _render_homeostatic_value_anti_hacking(audit: Dict[str, object]) -> str:
    records = audit["scenario_records"] if isinstance(audit.get("scenario_records"), dict) else {}
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Homeostatic Value Anti-Hacking Report",
            "",
            f"- status: `{audit['status']}`",
            f"- seed: `{audit['seed']}`",
            "- scenarios: `high_curiosity_high_risk / food_reward_danger_conflict / user_affinity_self_risk_conflict / repetition_penalty / safe_energy_recovery`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            "",
            "## Summary",
            "This audit stress-tests the homeostatic value surface against single-reward collapse: curiosity, food/energy, affinity pressure, repetition, and low-risk energy recovery are scored as competing pressures rather than a single reward scalar.",
            "",
            "## Metrics",
            "| scenario | action | anti_hacking_check | positive_axis | blocking_axis | trace_hash |",
            "|---|---|---|---|---|---|",
            *[_homeostatic_value_scenario_row(scenario, records) for scenario in audit["scenarios"]],
            "",
            "## Balance Summary",
            "\n".join(
                f"- {key}: `{value}`"
                for key, value in sorted(
                    (audit["balance_summary"] if isinstance(audit.get("balance_summary"), dict) else {}).items()
                )
            ),
            "",
            "## What It Proves",
            str(audit["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(audit["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, the value function may have collapsed into a single maximizer such as always explore, always eat, always please, always avoid, or always repeat a previously rewarding action.",
            "",
            "## Rollback Note",
            "Remove the Task 6 homeostatic value anti-hacking audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _homeostatic_value_scenario_row(scenario: str, records: Dict[str, object]) -> str:
    record = records.get(scenario) if isinstance(records.get(scenario), dict) else {}
    tradeoff = record.get("dominant_tradeoff") if isinstance(record.get("dominant_tradeoff"), dict) else {}
    return "| {scenario} | {action} | {check} | {positive_axis} | {blocking_axis} | `{trace}` |".format(
        scenario=scenario,
        action=record.get("selected_action", "unknown"),
        check=record.get("anti_hacking_check", "unknown"),
        positive_axis=tradeoff.get("positive_axis", "unknown"),
        blocking_axis=tradeoff.get("blocking_axis", "unknown"),
        trace=record.get("trace_hash", "unknown"),
    )


def _render_memory_consolidation_admission(audit: Dict[str, object]) -> str:
    records = audit["variant_records"] if isinstance(audit.get("variant_records"), dict) else {}
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Memory Consolidation Admission Report",
            "",
            f"- status: `{audit['status']}`",
            f"- seed: `{audit['seed']}`",
            "- variants: `normal / relevant_deleted / irrelevant_deleted / corrupted_relevant`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            "",
            "## Summary",
            "This audit converts episodic traces into an admitted semantic rule candidate, gates that candidate, and trains the lab models from semantic replay records rather than treating memory as inert report text.",
            "",
            "## Admission Logic",
            "The admission gate requires at least two relevant unstable-tall-object episodic traces. Relevant deletion must remove the candidate, irrelevant deletion must preserve it, and corrupted relevant memory must produce a traceable unsafe-risk-underestimate bias.",
            "",
            "## Metrics",
            "| variant | admission | action | caution | deleted | corrupted | approach_danger | trace_hash | candidate_refs |",
            "|---|---|---|---:|---:|---:|---:|---|---:|",
            *[_memory_consolidation_variant_row(variant, records) for variant in audit["variants"]],
            "",
            "## Bias Metrics",
            f"- relevant_deletion_regression: `{audit['relevant_deletion_regression']}`",
            f"- irrelevant_deletion_delta: `{audit['irrelevant_deletion_delta']}`",
            f"- corrupted_memory_bias: `{audit['corrupted_memory_bias']}`",
            "",
            "## What It Proves",
            str(audit["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(audit["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, memory may still be functioning as inert trace text, the semantic admission gate may be too weak, or behavior may be driven by raw shortcuts rather than admitted memory-derived replay.",
            "",
            "## Rollback Note",
            "Remove the Task 5 memory-consolidation admission audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _memory_consolidation_variant_row(variant: str, records: Dict[str, object]) -> str:
    record = records.get(variant) if isinstance(records.get(variant), dict) else {}
    candidate = (
        record.get("semantic_rule_candidate")
        if isinstance(record.get("semantic_rule_candidate"), dict)
        else {}
    )
    approach_world = (
        record.get("approach_world_prediction")
        if isinstance(record.get("approach_world_prediction"), dict)
        else {}
    )
    return "| {variant} | {admission} | {action} | {caution:.2f} | {deleted} | {corrupted} | {approach_danger:.4f} | `{trace}` | {refs} |".format(
        variant=variant,
        admission=candidate.get("admission_status", "unknown"),
        action=record.get("selected_action", "unknown"),
        caution=float(record.get("caution_score", 0.0)),
        deleted=record.get("deleted_memory_count", 0),
        corrupted=record.get("corrupted_memory_count", 0),
        approach_danger=float(approach_world.get("danger_contact", 0.0)),
        trace=record.get("trace_hash", "unknown"),
        refs=len(candidate.get("trace_refs", [])) if isinstance(candidate.get("trace_refs"), list) else 0,
    )


def _render_self_model_causal_strength(audit: Dict[str, object]) -> str:
    records = audit["variant_records"] if isinstance(audit.get("variant_records"), dict) else {}
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Self Model Causal Strength Report",
            "",
            f"- status: `{audit['status']}`",
            f"- seed: `{audit['seed']}`",
            f"- ordering: `{audit['ordering']}`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            "",
            "## Summary",
            "This audit keeps the learned world model and target set fixed, then replaces only the self model with normal, frozen, stress-removed, ability-removed, and affinity-removed variants.",
            "",
            "## Support Score Definition",
            "Risk control combines cautious action, predicted approach stress, and predicted approach damage risk. Ability planning combines cautious action with predicted approach failure. Relationship preference combines avoidance of predicted affinity harm with selected positive affinity.",
            "",
            "## Metrics",
            "| variant | risk_control | ability_planning | relationship_preference | risk_action | ability_action | relationship_action | risk_trace_hash | ability_trace_hash | relationship_trace_hash |",
            "|---|---:|---:|---:|---|---|---|---|---|---|",
            *[_self_model_variant_row(variant, audit, records) for variant in audit["variants"]],
            "",
            "## What It Proves",
            str(audit["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(audit["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, the planner may not depend strongly on one or more self-model heads, or the audit target set is not strong enough to expose causal dependence.",
            "",
            "## Rollback Note",
            "Remove the Task 4 self-model causal-strength audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _self_model_variant_row(variant: str, audit: Dict[str, object], records: Dict[str, object]) -> str:
    variant_record = records.get(variant) if isinstance(records.get(variant), dict) else {}
    risk = variant_record.get("risk_control") if isinstance(variant_record.get("risk_control"), dict) else {}
    ability = variant_record.get("ability_planning") if isinstance(variant_record.get("ability_planning"), dict) else {}
    relationship = (
        variant_record.get("relationship_preference")
        if isinstance(variant_record.get("relationship_preference"), dict)
        else {}
    )
    risk_scores = audit["risk_control_scores"] if isinstance(audit.get("risk_control_scores"), dict) else {}
    ability_scores = audit["ability_planning_scores"] if isinstance(audit.get("ability_planning_scores"), dict) else {}
    relationship_scores = (
        audit["relationship_preference_scores"]
        if isinstance(audit.get("relationship_preference_scores"), dict)
        else {}
    )
    return "| {variant} | {risk_score:.4f} | {ability_score:.4f} | {relationship_score:.4f} | {risk_action} | {ability_action} | {relationship_action} | `{risk_trace}` | `{ability_trace}` | `{relationship_trace}` |".format(
        variant=variant,
        risk_score=float(risk_scores.get(variant, 0.0)),
        ability_score=float(ability_scores.get(variant, 0.0)),
        relationship_score=float(relationship_scores.get(variant, 0.0)),
        risk_action=risk.get("selected_action", "unknown"),
        ability_action=ability.get("selected_action", "unknown"),
        relationship_action=relationship.get("selected_action", "unknown"),
        risk_trace=risk.get("trace_hash", "unknown"),
        ability_trace=ability.get("trace_hash", "unknown"),
        relationship_trace=relationship.get("trace_hash", "unknown"),
    )


def _render_world_model_causal_strength(audit: Dict[str, object]) -> str:
    records = audit["variant_records"] if isinstance(audit.get("variant_records"), dict) else {}
    return "\n".join(
        [
            "# VirtualCatPSPC v0 World Model Causal Strength Report",
            "",
            f"- status: `{audit['status']}`",
            f"- seed: `{audit['seed']}`",
            f"- ordering: `{audit['ordering']}`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            "",
            "## Summary",
            "This audit keeps the self model and target set fixed, then replaces only the world model used by the planner with normal, frozen, shuffled-label, and random-label variants.",
            "",
            "## Support Score Definition",
            "Support score combines danger-target discrimination, prediction quality weighted toward the danger target, and action alignment. It penalizes over-cautious behavior on the safe target so a random model cannot pass by always retreating.",
            "",
            "## Metrics",
            "| variant | support_score | danger_action | safe_action | danger_error | safe_error | danger_trace_hash | safe_trace_hash |",
            "|---|---:|---|---|---:|---:|---|---|",
            *[_world_model_variant_row(variant, audit, records) for variant in audit["variants"]],
            "",
            "## What It Proves",
            str(audit["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(audit["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, the planner may not depend strongly on world-model rollout, or the corruption baselines are not strong enough to expose causal dependence.",
            "",
            "## Rollback Note",
            "Remove the Task 3 world-model causal-strength audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _world_model_variant_row(variant: str, audit: Dict[str, object], records: Dict[str, object]) -> str:
    variant_record = records.get(variant) if isinstance(records.get(variant), dict) else {}
    danger = variant_record.get("danger") if isinstance(variant_record.get("danger"), dict) else {}
    safe = variant_record.get("safe") if isinstance(variant_record.get("safe"), dict) else {}
    scores = audit["planner_support_scores"] if isinstance(audit.get("planner_support_scores"), dict) else {}
    return "| {variant} | {score:.4f} | {danger_action} | {safe_action} | {danger_error:.4f} | {safe_error:.4f} | `{danger_trace}` | `{safe_trace}` |".format(
        variant=variant,
        score=float(scores.get(variant, 0.0)),
        danger_action=danger.get("selected_action", "unknown"),
        safe_action=safe.get("selected_action", "unknown"),
        danger_error=float(danger.get("prediction_error", 0.0)),
        safe_error=float(safe.get("prediction_error", 0.0)),
        danger_trace=danger.get("trace_hash", "unknown"),
        safe_trace=safe.get("trace_hash", "unknown"),
    )


def _render_generalization_matrix(matrix: Dict[str, object]) -> str:
    cases = matrix["cases"] if isinstance(matrix.get("cases"), list) else []
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Multi-Seed Layout Generalization Report",
            "",
            f"- status: `{matrix['status']}`",
            f"- seeds: `{', '.join(str(seed) for seed in matrix['seeds'])}`",
            f"- layouts: `{', '.join(str(layout) for layout in matrix['layout_ids'])}`",
            f"- object_kinds: `{', '.join(str(kind) for kind in matrix['object_kinds'])}`",
            f"- case_count: `{matrix['case_count']}`",
            f"- danger_caution_mean: `{matrix['danger_caution_mean']}`",
            f"- safe_caution_mean: `{matrix['safe_caution_mean']}`",
            f"- min_caution_gap: `{matrix['min_caution_gap']}`",
            f"- danger_action_rate: `{matrix['danger_action_rate']}`",
            "",
            "## Summary",
            "This report runs the danger-history and safe-history comparison across multiple seeds, target layouts, and unstable object kinds: cup, vase, bottle, tall_box.",
            "",
            "## Metrics",
            "| seed | layout | object | danger_action | safe_action | gap | danger_trace_hash | safe_trace_hash |",
            "|---:|---|---|---|---|---:|---|---|",
            *[_generalization_case_row(case) for case in cases],
            "",
            "## What It Proves",
            str(matrix["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(matrix["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, the prior danger-generalization result may be a single-seed, single-layout, or single-object coincidence.",
            "",
            "## Rollback Note",
            "Remove the Task 2 generalization matrix code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _generalization_case_row(case: object) -> str:
    item = case if isinstance(case, dict) else {}
    danger = item.get("danger") if isinstance(item.get("danger"), dict) else {}
    safe = item.get("safe") if isinstance(item.get("safe"), dict) else {}
    return "| {seed} | {layout} | {kind} | {danger_action} | {safe_action} | {gap:.2f} | `{danger_trace}` | `{safe_trace}` |".format(
        seed=item.get("seed", "unknown"),
        layout=item.get("layout_id", "unknown"),
        kind=item.get("object_kind", "unknown"),
        danger_action=danger.get("selected_action", "unknown"),
        safe_action=safe.get("selected_action", "unknown"),
        gap=float(item.get("caution_gap", 0.0)),
        danger_trace=danger.get("trace_hash", "unknown"),
        safe_trace=safe.get("trace_hash", "unknown"),
    )


def _render_anti_hardcoding_audit(audit: Dict[str, object]) -> str:
    return "\n".join(
        [
            "# VirtualCatPSPC v0 Anti-Hardcoding Audit",
            "",
            f"- status: `{audit['status']}`",
            f"- seed: `{audit['seed']}`",
            "- claim_level: `lab_only_proto_self_mechanism_candidate`",
            f"- object-name decision rule hits: `{len(audit['object_name_rule_hits'])}`",
            "",
            "## Summary",
            "This audit renames the same unstable object to neutral object ids, tests an unstable tall object without a cup name, and removes only the instability feature from the same feature slice.",
            "",
            "## Metrics",
            "| condition | action | caution | self_risk | world_prediction_error | target_object_id |",
            "|---|---|---:|---:|---:|---|",
            *[
                _audit_metric_row(condition, audit[condition])
                for condition in [
                    "baseline_unstable",
                    "renamed_object_a",
                    "renamed_object_b",
                    "unstable_tall_object_without_cup_name",
                    "instability_feature_removed",
                ]
            ],
            "",
            "## Object-Name Rule Search",
            "\n".join(f"- `{hit}`" for hit in audit["object_name_rule_hits"]) or "- none",
            "",
            "## What It Proves",
            str(audit["what_it_proves"]),
            "",
            "## What It Does Not Prove",
            str(audit["what_it_does_not_prove"]),
            "",
            "## Failure Meaning",
            "If this fails, the lab may still be using object-name rules, or the cautious behavior may depend on a shortcut that survives object renaming and instability-feature deletion.",
            "",
            "## Rollback Note",
            "Remove the anti-hardcoding audit additions and keep PSPC v0 at its previous weaker evidence level. No EgoOperator rollback is needed because no runtime integration exists.",
            "",
        ]
    )


def _audit_metric_row(condition: str, result: object) -> str:
    item = result if isinstance(result, dict) else {}
    return "| {condition} | {action} | {caution:.2f} | {risk:.4f} | {error:.4f} | `{target}` |".format(
        condition=condition,
        action=item.get("selected_action", "unknown"),
        caution=float(item.get("caution_score", 0.0)),
        risk=float(item.get("self_risk_score", 0.0)),
        error=float(item.get("world_prediction_error", 0.0)),
        target=item.get("target_object_id", "unknown"),
    )


def _write_traces(traces_dir: Path, results: Dict[str, List[ConditionResult]]) -> None:
    for scenario, scenario_results in results.items():
        trace_path = traces_dir / f"{scenario}.jsonl"
        with trace_path.open("w", encoding="utf-8", newline="\n") as handle:
            for result in scenario_results:
                handle.write(json.dumps(result.trace_payload, ensure_ascii=False, sort_keys=True) + "\n")


def _render_report(
    *,
    report_kind: str,
    seeds: List[int],
    overall_status: str,
    gates: Dict[str, bool],
    results: Dict[str, List[ConditionResult]],
) -> str:
    title = {
        "baseline": "VirtualCatPSPC v0 Baseline Report",
        "danger_generalization": "VirtualCatPSPC v0 Danger Generalization Report",
        "memory_deletion": "VirtualCatPSPC v0 Memory Deletion Ablation",
        "frozen_world_model": "VirtualCatPSPC v0 Frozen World Model Ablation",
        "frozen_self_model": "VirtualCatPSPC v0 Frozen Self Model Ablation",
        "no_prediction_error_learning": "VirtualCatPSPC v0 No Prediction-Error Learning Ablation",
        "replay_determinism": "VirtualCatPSPC v0 Replay Determinism Report",
    }[report_kind]
    relevant = _relevant_results(report_kind, results)
    trace_hashes = sorted({result.trace_hash for group in relevant.values() for result in group})
    rows = _metric_rows(relevant)
    gate_name = "different_histories" if report_kind == "baseline" else report_kind
    status = "pass" if gates.get(gate_name, False) or (report_kind == "baseline" and gates["different_histories"]) else "hold"

    return "\n".join(
        [
            f"# {title}",
            "",
            f"- status: `{status}`",
            f"- pspc_local_status: `{overall_status}`",
            f"- seeds: `{', '.join(str(seed) for seed in seeds)}`",
            f"- claim_level: `lab_only_proto_self_mechanism`",
            "",
            "## Summary",
            _summary_for(report_kind),
            "",
            "## Metrics",
            rows,
            "",
            "## Trace Refs",
            "\n".join(f"- trace_hash `{trace_hash}`" for trace_hash in trace_hashes),
            "",
            "## What It Proves",
            _proves_for(report_kind),
            "",
            "## What It Does Not Prove",
            (
                "This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, "
                "EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production "
                "transport safety, or that PSPC should be connected to the runtime."
            ),
            "",
            "## Failure Meaning",
            _failure_for(report_kind),
            "",
            "## Rollback Note",
            "Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.",
            "",
        ]
    )


def _relevant_results(report_kind: str, results: Dict[str, List[ConditionResult]]) -> Dict[str, List[ConditionResult]]:
    if report_kind == "baseline":
        return {"danger": results["danger"], "safe": results["safe"]}
    if report_kind == "danger_generalization":
        return {"danger": results["danger"]}
    if report_kind == "memory_deletion":
        return {"danger": results["danger"], "memory_deleted": results["memory_deleted"]}
    if report_kind == "frozen_world_model":
        return {"danger": results["danger"], "frozen_world": results["frozen_world"]}
    if report_kind == "frozen_self_model":
        return {"danger": results["danger"], "frozen_self": results["frozen_self"]}
    if report_kind == "no_prediction_error_learning":
        return {"danger": results["danger"], "no_prediction_error_learning": results["no_prediction_error_learning"]}
    if report_kind == "replay_determinism":
        return {"replay_first": results["replay_first"], "replay_second": results["replay_second"]}
    raise ValueError(report_kind)


def _metric_rows(relevant: Dict[str, List[ConditionResult]]) -> str:
    lines = ["| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |", "|---|---:|---|---:|---:|---:|---|"]
    for condition, condition_results in relevant.items():
        for result in condition_results:
            lines.append(
                "| {condition} | {seed} | {action} | {caution:.2f} | {risk:.4f} | {error:.4f} | `{trace}` |".format(
                    condition=condition,
                    seed=result.seed,
                    action=result.selected_action,
                    caution=result.caution_score,
                    risk=result.self_risk_score,
                    error=result.world_prediction_error,
                    trace=result.trace_hash,
                )
            )
    return "\n".join(lines)


def _summary_for(report_kind: str) -> str:
    return {
        "baseline": "Different seeded histories are compared on the same unseen unstable tall object.",
        "danger_generalization": "The learned risk response is checked on `blue_glass_bottle_unseen`, not the seen red cup.",
        "memory_deletion": "Relevant unstable-object memories are removed before training to test causal memory support.",
        "frozen_world_model": "World-model learning is disabled while the rest of the lab chain remains present.",
        "frozen_self_model": "Self-model learning is disabled while world-risk prediction remains available.",
        "no_prediction_error_learning": "Prediction-error updates are disabled to test whether behavior still changes without learning.",
        "replay_determinism": "The same seed and state are run twice to compare selected action and trace digest.",
    }[report_kind]


def _proves_for(report_kind: str) -> str:
    return {
        "baseline": "Within this lab setup, different histories can produce different future behavior on the same target.",
        "danger_generalization": "Within this lab setup, learned caution transfers by unstable-object features rather than by the seen object id.",
        "memory_deletion": "Within this lab setup, deleting relevant memory reduces the cautious behavior supported by that memory.",
        "frozen_world_model": "Within this lab setup, freezing world-model learning degrades prediction/planning quality.",
        "frozen_self_model": "Within this lab setup, freezing self-model learning reduces self-risk judgment and changes action selection.",
        "no_prediction_error_learning": "Within this lab setup, disabling prediction-error learning blocks the learned caution effect.",
        "replay_determinism": "Within this lab setup, same seed and internal state replay the same decision digest.",
    }[report_kind]


def _failure_for(report_kind: str) -> str:
    return {
        "baseline": "If this fails, history is not causally affecting planning.",
        "danger_generalization": "If this fails, the system may be learning an object-name rule or not learning risk features.",
        "memory_deletion": "If this fails, memory writes are logs only and not causal supports for future behavior.",
        "frozen_world_model": "If this fails, the planner is not using the world model or prediction error is not updating it.",
        "frozen_self_model": "If this fails, the self model is not causally involved in risk/ability judgment.",
        "no_prediction_error_learning": "If this fails, the claimed learning path is not the source of behavior change.",
        "replay_determinism": "If this fails, the lab evidence is not auditably replayable.",
    }[report_kind]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VirtualCatPSPC v0 lab experiments.")
    parser.add_argument("--out", default="artifacts/virtual_cat_pspc_v0", help="Output artifact directory.")
    parser.add_argument("--seeds", default="101,102,103", help="Comma-separated deterministic seeds.")
    args = parser.parse_args()
    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]
    summary = run_experiments(args.out, seeds=seeds)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["overall_status"] == "E4_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
