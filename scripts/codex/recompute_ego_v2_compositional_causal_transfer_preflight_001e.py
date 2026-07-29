from __future__ import annotations

import copy
import base64
import hashlib
import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence


FORMAL_BLOCK = "FORMAL_EXECUTION_NOT_AUTHORIZED_001E_I1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = REPO_ROOT / "docs/codex/tasks/ego-v2-p1-compositional-causal-transfer-preflight-001e/FROZEN_DESIGN.json"
DESIGN_SHA256 = "8a60c0e8521b02d7423fa5320ba8013e29c128e27aaec1a4a3ee4674fac0027d"
COMPOSITIONS = tuple(f"{value:03b}" for value in range(8))
SECOND_QUERY_CANDIDATES = COMPOSITIONS[1:]
VERDICT_PRIORITY = (
    "CAOT_BOOL_V2_PRIVATE_TRUTH_LEAKAGE",
    "CAOT_BOOL_V2_INSTRUMENT_INVALID",
    "CAOT_BOOL_V2_QUERY_TIE_SENSITIVE",
    "CAOT_BOOL_V2_EQUAL_ACCESS_CONTROL_MATCH",
    "CAOT_BOOL_V2_NO_REFERENCE_HEADROOM",
    "CAOT_BOOL_V2_REFERENCE_HEADROOM_ADMITTED",
)
INTEGRITY_GATE_FIELDS = (
    "complete_population", "fresh_replay_equal", "independent_recompute_equal",
    "leakage_positive_controls_rejected",
)
POSITIVE_GATE_FIELDS = (
    "nominal_gain_pass", "exact_gain_pass", "local_gain_pass",
    "nonlocal_safety_pass", "scratch_heavy_gain_pass",
    "active_vs_best_fixed_pass", "unique_nonlexical_positive_forward_pass",
    "source_delete_pass", "local_delete_pass", "feedback_mask_pass",
    "active_delete_pass",
)
CONTROL_IDS = (
    "SCRATCH_SPIKE_SLAB_ACTIVE_BAYES",
    "EXACT_SOURCE_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK",
    "LOCAL_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK",
    "SOURCE_CONSISTENCY_WITH_SCRATCH_FALLBACK",
    "MARGINAL_MDL_MAP_HARD_FAMILY",
    "MINIMUM_HAMMING_NEAREST_SOURCE",
    "FIXED_QUERY_001", "FIXED_QUERY_010", "FIXED_QUERY_011",
    "FIXED_QUERY_100", "FIXED_QUERY_101", "FIXED_QUERY_110", "FIXED_QUERY_111",
    "PASSIVE_LEXICAL", "UNIFORM_FIXED_QUERY_MIXTURE",
    "OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN",
    "COUNT_TABLE_TARGET_MEAN", "GRAPH_LOOKUP_MIN_HAMMING_MEAN",
    "EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY",
    "CANDIDATE_RULE_AMORTIZED_LOOKUP",
    "TRANSITION_TABLE", "SUCCESSOR_MAP", "FSM_PLANNER",
)
INVALIDATING_CONTROL_IDS = tuple(
    control_id for control_id in CONTROL_IDS
    if control_id not in {
        "CANDIDATE_RULE_AMORTIZED_LOOKUP",
        "TRANSITION_TABLE", "SUCCESSOR_MAP", "FSM_PLANNER",
    }
)
LEAKAGE_CASE_IDS = (
    "CLEAN_LEGAL_INPUT",
    "HIDDEN_COEFFICIENT_DIRECT", "HIDDEN_RELATION_DIRECT",
    "HIDDEN_COEFFICIENT_ENCODED", "HIDDEN_RELATION_ENCODED",
)
EVIDENCE_RUN_ID = "I1_BOUNDED_FIXTURE_NOT_FORMAL"
FORBIDDEN_KEYS = {
    "source_coefficients", "target_coefficients", "source_program_id",
    "target_program_id", "relation", "stratum", "hamming_distance",
    "future_outcome", "scorer", "world_id", "layout_id", "policy_id",
    "run_id", "seed", "mapping", "cause", "objects_by_cause",
    "private_state", "global_state", "raw_trace", "artifact_path",
    "artifact_hash", "encoded_private_alias",
}


class FormalExecutionNotAuthorizedError(RuntimeError):
    pass


class PrivateTruthLeakageError(ValueError):
    pass


class DesignValidationError(ValueError):
    pass


def _compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_design() -> dict[str, Any]:
    if _compute_sha256(DESIGN_PATH) != DESIGN_SHA256:
        raise DesignValidationError("frozen design drift")
    value = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if value.get("task_id") != "EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E":
        raise DesignValidationError("task_id drift")
    if tuple(value.get("verdict_priority", ()))[:3] != (
        "CAOT_BOOL_V2_PRIVATE_TRUTH_LEAKAGE",
        "CAOT_BOOL_V2_INSTRUMENT_INVALID",
        "CAOT_BOOL_V2_QUERY_TIE_SENSITIVE",
    ):
        raise DesignValidationError("verdict priority drift")
    return value


def _scan_value(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            compact = "".join(character for character in lowered if character.isalnum())
            forbidden_compact = {"".join(character for character in item if character.isalnum()) for item in FORBIDDEN_KEYS}
            if lowered in FORBIDDEN_KEYS or compact in forbidden_compact:
                raise PrivateTruthLeakageError(f"forbidden field: {key}")
            _scan_value(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _scan_value(child)
    elif isinstance(value, str):
        lowered = value.lower()
        tokens = tuple(sorted(FORBIDDEN_KEYS)) + ("hidden_coefficient", "hidden_relation")
        if any(token in lowered for token in tokens):
            raise PrivateTruthLeakageError("encoded private alias")
        decoded_candidates: list[str] = []
        try:
            decoded_candidates.append(base64.b64decode(value, validate=True).decode("utf-8").lower())
        except Exception:
            pass
        try:
            decoded_candidates.append(bytes.fromhex(value).decode("utf-8").lower())
        except Exception:
            pass
        if any(any(token in decoded for token in tokens) for decoded in decoded_candidates):
            raise PrivateTruthLeakageError("encoded private alias")


def _canonical_rows(rows: Sequence[Mapping[str, Any]], *, complete: bool) -> tuple[tuple[str, int], ...]:
    canonical: dict[str, int] = {}
    for row in rows:
        if set(row) != {"composition", "outcome"}:
            raise PrivateTruthLeakageError("row schema contains non-public fields")
        composition = row["composition"]
        outcome = row["outcome"]
        if composition not in COMPOSITIONS or outcome not in (0, 1) or composition in canonical:
            raise ValueError("invalid or duplicate row")
        canonical[str(composition)] = int(outcome)
    if complete and set(canonical) != set(COMPOSITIONS):
        raise ValueError("incomplete source table")
    return tuple(sorted(canonical.items()))


def _scan_public_input(public_input: Mapping[str, Any]) -> None:
    required = {"source_truth_table", "target_history", "query_count", "query_budget", "arm_semantics", "serialized_state"}
    if set(public_input) != required:
        raise PrivateTruthLeakageError("public schema mismatch")
    _scan_value(public_input)
    history = _canonical_rows(public_input["target_history"], complete=False)
    _canonical_rows(public_input["source_truth_table"], complete=True)
    if not history or history[0][0] != "000":
        raise ValueError("history must begin at 000")
    if public_input["query_budget"] != 1 or public_input["query_count"] != len(history) - 1:
        raise ValueError("query count drift")


def _program_bits(program_id: int) -> tuple[int, ...]:
    if not isinstance(program_id, int) or not 0 <= program_id < 128:
        raise ValueError("program_id must be in 0..127")
    return tuple((program_id >> shift) & 1 for shift in range(6, -1, -1))


def _evaluate(program_id: int, composition: str) -> int:
    if composition not in COMPOSITIONS:
        raise ValueError("invalid composition")
    b0, b1, b2, b3, b12, b13, b23 = _program_bits(program_id)
    x1, x2, x3 = (int(bit) for bit in composition)
    return b0 ^ (b1 & x1) ^ (b2 & x2) ^ (b3 & x3) ^ (b12 & x1 & x2) ^ (b13 & x1 & x3) ^ (b23 & x2 & x3)


def _source_program(source_table: Sequence[Mapping[str, Any]]) -> int:
    canonical = _canonical_rows(source_table, complete=True)
    for program_id in range(128):
        table = tuple((composition, _evaluate(program_id, composition)) for composition in COMPOSITIONS)
        if table == canonical:
            return program_id
    raise DesignValidationError("source program not identified")


def _local_neighbors(source_program: int) -> tuple[int, ...]:
    return tuple(source_program ^ (1 << (6 - bit_index)) for bit_index in range(1, 7))


def _scratch_prior(program_id: int) -> Fraction:
    active_nonintercept = sum(_program_bits(program_id)[1:])
    return Fraction(3 ** (6 - active_nonintercept), 8192)


def _history(public_input: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    _scan_public_input(public_input)
    return _canonical_rows(public_input["target_history"], complete=False)


def _compatible(program_id: int, history: Sequence[tuple[str, int]]) -> bool:
    return all(_evaluate(program_id, composition) == outcome for composition, outcome in history)


def _unconditional_weights(source_program: int) -> dict[int, int]:
    neighbors = set(_local_neighbors(source_program))
    result: dict[int, int] = {}
    for program_id in range(128):
        active_nonintercept = sum(_program_bits(program_id)[1:])
        result[program_id] = 3 * (3 ** (6 - active_nonintercept)) + (24576 if program_id == source_program else 0) + (4096 if program_id in neighbors else 0)
    return result


def _posterior(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], mode: str) -> dict[str, Any]:
    if mode == "scratch":
        raw = {pid: _scratch_prior(pid) for pid in range(128) if _compatible(pid, history)}
        total = sum(raw.values(), Fraction(0, 1))
        if total <= 0:
            raise DesignValidationError("zero posterior")
        return {
            "weights": raw,
            "posterior_total_weight": total,
            "family_marginals": {
                "SCRATCH": total,
                "EXACT_SOURCE": Fraction(0, 1),
                "LOCAL_SHIFT": Fraction(0, 1),
            },
            "family_posteriors": {
                "SCRATCH": Fraction(1, 1),
                "EXACT_SOURCE": Fraction(0, 1),
                "LOCAL_SHIFT": Fraction(0, 1),
            },
        }
    if mode != "primary":
        raise ValueError("unsupported posterior mode")
    source_program = _source_program(public_input["source_truth_table"])
    local = set(_local_neighbors(source_program))
    raw = {pid: Fraction(weight, 73728) for pid, weight in _unconditional_weights(source_program).items() if _compatible(pid, history)}
    total = sum(raw.values(), Fraction(0, 1))
    if total <= 0:
        raise DesignValidationError("zero posterior")
    marginals = {
        "SCRATCH": sum((_scratch_prior(pid) for pid in range(128) if _compatible(pid, history)), Fraction(0, 1)),
        "EXACT_SOURCE": Fraction(int(_compatible(source_program, history)), 1),
        "LOCAL_SHIFT": Fraction(sum(_compatible(pid, history) for pid in local), 6),
    }
    marginal_total = sum(marginals.values(), Fraction(0, 1))
    family_posteriors = {family: value / marginal_total for family, value in marginals.items()}
    return {
        "weights": raw,
        "posterior_total_weight": total,
        "family_marginals": marginals,
        "family_posteriors": family_posteriors,
    }


def _predictive_probability(posterior: Mapping[str, Any], composition: str) -> Fraction:
    numerator = sum((weight for program_id, weight in posterior["weights"].items() if _evaluate(program_id, composition) == 1), Fraction(0, 1))
    return numerator / posterior["posterior_total_weight"]


def _query_score(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], query: str, mode: str) -> Fraction:
    base = _posterior(public_input, history, mode)
    probability_one = _predictive_probability(base, query)
    total = Fraction(0, 1)
    for outcome, probability in ((0, 1 - probability_one), (1, probability_one)):
        if probability == 0:
            continue
        updated_history = tuple(history) + ((query, outcome),)
        updated = _posterior(public_input, updated_history, mode)
        remaining = [composition for composition in COMPOSITIONS if composition not in {item[0] for item in updated_history}]
        total += probability * sum((_predictive_probability(updated, composition) * (1 - _predictive_probability(updated, composition)) for composition in remaining), Fraction(0, 1))
    return total


def _choose_query(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], mode: str) -> dict[str, Any]:
    scores = {query: _query_score(public_input, history, query, mode) for query in SECOND_QUERY_CANDIDATES if query not in {item[0] for item in history}}
    minimum = min(scores.values())
    minimizers = tuple(sorted(query for query, score in scores.items() if score == minimum))
    selected = minimizers[0]
    return {
        "selected_query": selected,
        "minimizers": minimizers,
        "query_scores": scores,
        "lexical_terminal_loss": scores[selected],
        "optimistic_terminal_loss": min(scores[query] for query in minimizers),
        "pessimistic_terminal_loss": max(scores[query] for query in minimizers),
    }


def _fraction_to_json(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _jsonify(value: Any) -> Any:
    if isinstance(value, Fraction):
        return _fraction_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonify(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonify(child) for child in value]
    return value


def public_state_signature(record: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "selected_query", "minimizers", "query_scores", "lexical_terminal_loss",
        "optimistic_terminal_loss", "pessimistic_terminal_loss",
    )
    return _jsonify({field: record[field] for field in fields if field in record})


def recompute_public_state(public_input: Mapping[str, Any]) -> dict[str, Any]:
    _load_design()
    _scan_public_input(public_input)
    history = _history(public_input)
    query = _choose_query(public_input, history, "primary")
    return {
        "status": "OK",
        "arm_id": "MIXTURE_BMA_ACTIVE_BRIER",
        "posterior_mode": "primary",
        "public_input": copy.deepcopy(dict(public_input)),
        "source_table_read_count": 1,
        **query,
    }


def _independent_digest(record: Mapping[str, Any]) -> str:
    payload = json.dumps(
        public_state_signature(record),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compare_against_primary(public_input: Mapping[str, Any], primary_record: Mapping[str, Any]) -> dict[str, Any]:
    recomputed = recompute_public_state(public_input)
    expected_digest = _independent_digest(recomputed)
    return {
        "match": public_state_signature(recomputed) == public_state_signature(primary_record),
        "recomputed": recomputed,
        "expected_digest": expected_digest,
    }


def recompute_posterior_receipt(public_input: Mapping[str, Any], *, mode: str = "primary") -> dict[str, Any]:
    _load_design()
    history = _history(public_input)
    posterior = _posterior(public_input, history, mode)
    return {
        "posterior_total_weight": posterior["posterior_total_weight"],
        "family_marginals": copy.deepcopy(posterior["family_marginals"]),
        "family_posteriors": copy.deepcopy(posterior["family_posteriors"]),
    }


def population_summary() -> dict[str, Any]:
    return {
        "source_program_count": 128,
        "target_program_count": 128,
        "pair_count_per_arm": 16384,
        "stratum_counts": {"EXACT": 128, "LOCAL": 768, "NONLOCAL": 15488},
    }


def classify_pair(source_program: int, target_program: int) -> str:
    source = _program_bits(source_program)
    target = _program_bits(target_program)
    if source_program == target_program:
        return "EXACT"
    if source[0] == target[0] and sum(a != b for a, b in zip(source[1:], target[1:])) == 1:
        return "LOCAL"
    return "NONLOCAL"


def common_unqueried_gain(candidate_pair: Mapping[str, Any], comparator_pair: Mapping[str, Any]) -> dict[str, Any]:
    candidate_predictions = candidate_pair.get("selected_predictions")
    comparator_predictions = comparator_pair.get("selected_predictions")
    candidate_truth = candidate_pair.get("selected_truth")
    comparator_truth = comparator_pair.get("selected_truth")
    if not all(isinstance(value, Mapping) for value in (candidate_predictions, comparator_predictions, candidate_truth, comparator_truth)):
        raise ValueError("pair records lack selected endpoint predictions")
    common = tuple(sorted(set(candidate_predictions).intersection(comparator_predictions)))
    if not common or any(candidate_truth[node] != comparator_truth[node] for node in common):
        raise ValueError("common-unqueried truth mismatch")
    candidate_loss = sum((candidate_predictions[node] - candidate_truth[node]) ** 2 for node in common) / len(common)
    comparator_loss = sum((comparator_predictions[node] - comparator_truth[node]) ** 2 for node in common) / len(common)
    return {
        "candidate_query": candidate_pair.get("selected_query"),
        "comparator_query": comparator_pair.get("selected_query"),
        "common_unqueried": common,
        "common_unqueried_count": len(common),
        "candidate_loss": candidate_loss,
        "comparator_loss": comparator_loss,
        "gain": comparator_loss - candidate_loss,
        "unique_nonlexical_query": (
            len(tuple(candidate_pair.get("minimizers", ()))) == 1
            and candidate_pair.get("selected_query") != "001"
        ),
    }


def nonlocal_target_weights(source_program: int) -> dict[int, Fraction]:
    excluded = {source_program, *_local_neighbors(source_program)}
    raw = {target: _scratch_prior(target) for target in range(128) if target not in excluded}
    total = sum(raw.values(), Fraction(0, 1))
    return {target: mass / total for target, mass in raw.items()}


@lru_cache(maxsize=None)
def population_case_weight(source_program: int, target_program: int) -> Fraction:
    stratum = classify_pair(source_program, target_program)
    if stratum == "EXACT":
        within_source = Fraction(1, 1)
    elif stratum == "LOCAL":
        within_source = Fraction(1, 6)
    else:
        within_source = nonlocal_target_weights(source_program)[target_program]
    return Fraction(1, 128) * within_source


def reduce_complete_population_rows(
    rows: Sequence[Mapping[str, Any]], *, expected_arm_id: str,
    loss_field: str = "lexical_loss",
) -> dict[str, Fraction]:
    if len(rows) != 16384:
        raise ValueError("complete population requires exactly 16,384 rows")
    by_pair: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in rows:
        if row.get("status") != "OK" or row.get("arm_id") != expected_arm_id:
            raise ValueError("population row status/arm mismatch")
        source = row.get("source_program")
        target = row.get("target_program")
        if not isinstance(source, int) or not isinstance(target, int):
            raise ValueError("row lacks verifier-only pair IDs")
        key = (source, target)
        if key in by_pair:
            raise ValueError("duplicate source-target pair")
        if row.get("stratum") != classify_pair(source, target):
            raise ValueError("stratum mismatch")
        if not isinstance(row.get(loss_field), Fraction) or row[loss_field] < 0:
            raise ValueError("loss must be an exact nonnegative Fraction")
        by_pair[key] = row
    expected = {(source, target) for source in range(128) for target in range(128)}
    if set(by_pair) != expected:
        raise ValueError("population pair coverage mismatch")
    result: dict[str, Fraction] = {}
    for stratum in ("NONLOCAL", "EXACT", "LOCAL"):
        risk = sum(
            row[loss_field] * population_case_weight(source, target)
            for (source, target), row in by_pair.items()
            if row["stratum"] == stratum
        )
        result[stratum] = risk
    result["NOMINAL"] = sum(result[stratum] for stratum in ("NONLOCAL", "EXACT", "LOCAL")) / 3
    result["SCRATCH_HEAVY"] = result["NONLOCAL"] / 2 + result["EXACT"] / 4 + result["LOCAL"] / 4
    return result


def relative_improvement(candidate: Fraction, baseline: Fraction) -> Fraction:
    if baseline <= 0:
        raise ValueError("relative metric baseline denominator must be positive")
    return (baseline - candidate) / baseline


def weighted_tail_disclosures(weighted_regrets: Sequence[tuple[Fraction, Fraction]]) -> dict[str, Fraction]:
    if not weighted_regrets or any(weight < 0 for _, weight in weighted_regrets):
        raise ValueError("invalid weighted regret population")
    total_weight = sum((weight for _, weight in weighted_regrets), Fraction(0, 1))
    if total_weight != 1:
        raise ValueError("tail weights must normalize to one")
    maximum = max(regret for regret, _ in weighted_regrets)
    negative_transfer_mass = sum((weight for regret, weight in weighted_regrets if regret > 0), Fraction(0, 1))
    remaining = Fraction(1, 10)
    weighted_sum = Fraction(0, 1)
    for regret, weight in sorted(weighted_regrets, key=lambda item: item[0], reverse=True):
        take = min(weight, remaining)
        weighted_sum += regret * take
        remaining -= take
        if remaining == 0:
            break
    if remaining != 0:
        raise ValueError("insufficient mass for worst-10-percent CVaR")
    return {
        "maximum_nonlocal_regret": maximum,
        "nonlocal_negative_transfer_weighted_mass": negative_transfer_mass,
        "worst_10_percent_mass_nonlocal_cvar": weighted_sum / Fraction(1, 10),
    }


def reduce_risk_summary(
    candidate_risks: Mapping[str, Fraction], baseline_risks: Mapping[str, Fraction],
) -> dict[str, Fraction]:
    required = {"NONLOCAL", "EXACT", "LOCAL", "NOMINAL", "SCRATCH_HEAVY"}
    if set(candidate_risks) != required or set(baseline_risks) != required:
        raise ValueError("risk summary schema mismatch")
    return {
        "nominal_relative_gain": relative_improvement(candidate_risks["NOMINAL"], baseline_risks["NOMINAL"]),
        "exact_relative_gain": relative_improvement(candidate_risks["EXACT"], baseline_risks["EXACT"]),
        "local_relative_gain": relative_improvement(candidate_risks["LOCAL"], baseline_risks["LOCAL"]),
        "nonlocal_relative_regret": -relative_improvement(candidate_risks["NONLOCAL"], baseline_risks["NONLOCAL"]),
        "scratch_heavy_relative_gain": relative_improvement(candidate_risks["SCRATCH_HEAVY"], baseline_risks["SCRATCH_HEAVY"]),
    }


def _evidence_sha256(value: Any) -> str:
    canonical = json.dumps(_jsonify(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_EVIDENCE_BASE_FIELDS = {
    "status", "producer_function", "run_id", "code_path_hash",
    "aggregation_rule", "input_sources", "coverage", "receipt_sha256",
}
_EVIDENCE_SCHEMAS: dict[str, dict[str, set[str]]] = {
    "reduce_reference_population": {
        "coverage": {"candidate_arm_id", "scratch_arm_id", "loss_field", "candidate_row_count", "scratch_row_count", "candidate_rows_sha256", "scratch_rows_sha256", "candidate_behavior_sha256", "scratch_behavior_sha256"},
        "payload": {"candidate_risks", "scratch_risks", "relative_metrics", "tail_disclosures"},
    },
    "reduce_active_necessity": {
        "coverage": {"candidate_arm_id", "fixed_query_panel_arm_id", "loss_field", "candidate_row_count", "fixed_query_panel_row_count", "candidate_rows_sha256", "fixed_query_panel_rows_sha256"},
        "payload": {"best_global_fixed_query", "best_global_fixed_query_minimizers", "active_vs_best_fixed_relative_gain", "unique_nonlexical_positive_forward", "first_witness"},
    },
    "reduce_ablation_evidence": {
        "coverage": {"source_delete_receipt_sha256", "local_delete_receipt_sha256", "feedback_mask_receipt_sha256", "active_delete_receipt_sha256", "scratch_rows_sha256", "fixed_query_panel_rows_sha256", "source_delete_behavior_sha256", "scratch_behavior_sha256"},
        "payload": {"source_delete_pass", "local_delete_pass", "feedback_mask_pass", "active_delete_pass", "source_delete_relative_metrics", "local_delete_relative_metrics", "feedback_mask_active_vs_best_fixed_relative_gain", "active_delete_active_vs_best_fixed_relative_gain"},
    },
    "reduce_query_tie_evidence": {
        "coverage": {"branch_count", "branch_receipt_sha256s", "branch_kinds"},
        "payload": {"lexical_verdict", "optimistic_verdict", "pessimistic_verdict", "query_tie_sensitive"},
    },
    "reduce_control_evidence": {
        "coverage": {"candidate_receipt_sha256", "control_receipt_sha256s", "control_count"},
        "payload": {"pareto_match_ids", "control_match"},
    },
    "reduce_formal_integrity_evidence": {
        "coverage": {"expected_arm_id", "expected_row_count", "primary_stream_sha256", "replay_stream_sha256", "independent_stream_sha256", "primary_rows_sha256", "replay_rows_sha256", "independent_rows_sha256", "leakage_cases_sha256"},
        "payload": {"expected_row_count", "primary_row_count", "replay_mismatch_count", "independent_mismatch_count", "positive_leakage_case_count", "clean_leakage_case_count", "complete_population", "fresh_replay_equal", "independent_recompute_equal", "leakage_positive_controls_rejected", "private_truth_leakage", "instrument_invalid"},
    },
    "compute_gate_flags_from_evidence": {
        "coverage": {"gate_phase", "branch_kind", "input_receipt_sha256s"},
        "payload": {"private_truth_leakage", "instrument_invalid", "query_tie_sensitive", "control_match", *INTEGRITY_GATE_FIELDS, *POSITIVE_GATE_FIELDS},
    },
    "dispatch_verdict_evidence": {
        "coverage": {"gate_phase", "branch_kind", "gate_receipt_sha256"},
        "payload": {"verdict"},
    },
    "produce_primary_population_stream": {
        "coverage": {"arm_id", "row_producer_function", "row_count", "rows_sha256"},
        "payload": {"rows"},
    },
    "produce_fresh_replay_stream": {
        "coverage": {"arm_id", "row_producer_function", "row_count", "rows_sha256"},
        "payload": {"rows"},
    },
    "produce_independent_recompute_stream": {
        "coverage": {"arm_id", "row_producer_function", "row_count", "rows_sha256"},
        "payload": {"rows"},
    },
    "produce_leakage_scan_stream": {
        "coverage": {"case_count", "cases_sha256"},
        "payload": {"cases"},
    },
}
_EVIDENCE_AGGREGATION_RULES = {
    "reduce_reference_population": "complete_128x128_fraction_weighted_reference_and_tail_reduction",
    "reduce_active_necessity": "complete_population_global_fixed_envelope_and_common_unqueried_witness",
    "reduce_ablation_evidence": "four_decisive_ablation_receipt_threshold_reduction",
    "reduce_query_tie_evidence": "three_distinct_labeled_pre_tie_branch_verdict_comparison",
    "reduce_control_evidence": "complete_required_control_pareto_scan",
    "reduce_formal_integrity_evidence": "three_complete_population_validation_then_byte_equality_and_leakage_scan",
    "compute_gate_flags_from_evidence": "frozen_exact_thresholds_over_validated_receipt_chain",
    "dispatch_verdict_evidence": "frozen_first_true_verdict_priority",
    "produce_primary_population_stream": "complete_primary_population_stream_capture",
    "produce_fresh_replay_stream": "fresh_process_replay_population_stream_capture",
    "produce_independent_recompute_stream": "independent_code_path_population_stream_capture",
    "produce_leakage_scan_stream": "closed_positive_and_clean_leakage_case_stream_capture",
}


def _make_evidence_receipt(
    producer_function: str,
    *,
    input_sources: Sequence[str],
    coverage: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if producer_function in {
        "compute_gate_flags_from_evidence",
        "dispatch_verdict_evidence",
    }:
        raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)
    receipt = {
        "status": "OK",
        "producer_function": producer_function,
        "run_id": EVIDENCE_RUN_ID,
        "code_path_hash": _compute_sha256(Path(__file__)),
        "aggregation_rule": _EVIDENCE_AGGREGATION_RULES[producer_function],
        "input_sources": tuple(input_sources),
        "coverage": copy.deepcopy(dict(coverage)),
        **copy.deepcopy(dict(payload)),
    }
    schema = _EVIDENCE_SCHEMAS.get(producer_function)
    if schema is None or set(coverage) != schema["coverage"] or set(payload) != schema["payload"]:
        raise ValueError("evidence receipt producer schema mismatch")
    receipt["receipt_sha256"] = _evidence_sha256(receipt)
    return receipt


def _validate_evidence_receipt(
    receipt: Mapping[str, Any],
    *,
    producer_function: str,
    input_sources: Sequence[str] | None = None,
    expected_code_path_hash: str | None = None,
) -> None:
    if receipt.get("status") != "OK":
        raise ValueError("gate receipt status is not OK")
    if receipt.get("producer_function") != producer_function:
        raise ValueError("gate receipt producer mismatch")
    if receipt.get("run_id") != EVIDENCE_RUN_ID:
        raise ValueError("gate receipt run_id mismatch")
    if receipt.get("code_path_hash") != (expected_code_path_hash or _compute_sha256(Path(__file__))):
        raise ValueError("gate receipt code path hash mismatch")
    if receipt.get("aggregation_rule") != _EVIDENCE_AGGREGATION_RULES.get(producer_function):
        raise ValueError("gate receipt aggregation rule mismatch")
    if input_sources is not None and tuple(receipt.get("input_sources", ())) != tuple(input_sources):
        raise ValueError("gate receipt input source mismatch")
    supplied = receipt.get("receipt_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise ValueError("gate receipt hash missing")
    unhashed = dict(receipt)
    unhashed.pop("receipt_sha256", None)
    if supplied != _evidence_sha256(unhashed):
        raise ValueError("gate receipt hash mismatch")
    schema = _EVIDENCE_SCHEMAS.get(producer_function)
    coverage = receipt.get("coverage")
    if schema is None or not isinstance(coverage, Mapping):
        raise ValueError("gate receipt producer schema missing")
    if set(coverage) != schema["coverage"] or set(receipt) - _EVIDENCE_BASE_FIELDS != schema["payload"]:
        raise ValueError("gate receipt producer schema mismatch")


def _population_rows_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        encoded = json.dumps(_jsonify(row), sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _population_behavior_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    normalized = []
    for row in rows:
        item = {
            key: value for key, value in row.items()
            if key not in {"arm_id", "ablation_id", "producer_function", "source_access_receipt"}
        }
        normalized.append(item)
    return _population_rows_sha256(normalized)


def reduce_reference_population(
    candidate_rows: Sequence[Mapping[str, Any]], scratch_rows: Sequence[Mapping[str, Any]],
    *, candidate_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER", loss_field: str = "lexical_loss",
) -> dict[str, Any]:
    if loss_field not in {"lexical_loss", "optimistic_loss", "pessimistic_loss"}:
        raise ValueError("unregistered query-tie loss field")
    candidate_by_pair = {(row.get("source_program"), row.get("target_program")): row for row in candidate_rows}
    scratch_by_pair = {(row.get("source_program"), row.get("target_program")): row for row in scratch_rows}
    if len(candidate_by_pair) != len(candidate_rows) or set(candidate_by_pair) != set(scratch_by_pair):
        raise ValueError("candidate/scratch pair alignment mismatch")
    candidate_risks = reduce_complete_population_rows(candidate_rows, expected_arm_id=candidate_arm_id, loss_field=loss_field)
    scratch_risks = reduce_complete_population_rows(scratch_rows, expected_arm_id="SCRATCH_SPIKE_SLAB_ACTIVE_BAYES", loss_field=loss_field)
    metrics = reduce_risk_summary(candidate_risks, scratch_risks)
    weighted_regrets = []
    for (source, target), candidate_row in candidate_by_pair.items():
        if candidate_row["stratum"] != "NONLOCAL":
            continue
        regret = candidate_row[loss_field] - scratch_by_pair[(source, target)][loss_field]
        weighted_regrets.append((regret, population_case_weight(source, target)))
    return _make_evidence_receipt(
        "reduce_reference_population",
        input_sources=("candidate_population_rows", "scratch_population_rows"),
        coverage={
            "candidate_arm_id": candidate_arm_id,
            "scratch_arm_id": "SCRATCH_SPIKE_SLAB_ACTIVE_BAYES",
            "loss_field": loss_field,
            "candidate_row_count": len(candidate_rows),
            "scratch_row_count": len(scratch_rows),
            "candidate_rows_sha256": _population_rows_sha256(candidate_rows),
            "scratch_rows_sha256": _population_rows_sha256(scratch_rows),
            "candidate_behavior_sha256": _population_behavior_sha256(candidate_rows),
            "scratch_behavior_sha256": _population_behavior_sha256(scratch_rows),
        },
        payload={
            "candidate_risks": candidate_risks,
            "scratch_risks": scratch_risks,
            "relative_metrics": metrics,
            "tail_disclosures": weighted_tail_disclosures(weighted_regrets),
        },
    )


def select_global_fixed_query(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) != 16384:
        raise ValueError("global fixed-query envelope requires complete rows")
    expected_pairs = {(source, target) for source in range(128) for target in range(128)}
    observed_pairs: set[tuple[int, int]] = set()
    for row in rows:
        if row.get("status") != "OK" or row.get("arm_id") != "FIXED_QUERY_PANEL_PRIMARY":
            raise ValueError("fixed-query panel row status/arm mismatch")
        source = row.get("source_program")
        target = row.get("target_program")
        if not isinstance(source, int) or not isinstance(target, int):
            raise ValueError("fixed-query panel row lacks pair IDs")
        pair = (source, target)
        if pair in observed_pairs or row.get("stratum") != classify_pair(source, target):
            raise ValueError("fixed-query panel pair coverage/stratum mismatch")
        observed_pairs.add(pair)
        losses = row.get("fixed_query_losses")
        endpoints = row.get("fixed_query_endpoints")
        if not isinstance(losses, Mapping) or set(losses) != set(SECOND_QUERY_CANDIDATES):
            raise ValueError("fixed-query loss panel mismatch")
        if not isinstance(endpoints, Mapping) or set(endpoints) != set(SECOND_QUERY_CANDIDATES):
            raise ValueError("fixed-query endpoint panel mismatch")
        if any(not isinstance(losses[query], Fraction) or losses[query] < 0 for query in SECOND_QUERY_CANDIDATES):
            raise ValueError("fixed-query loss must be an exact nonnegative Fraction")
    if observed_pairs != expected_pairs:
        raise ValueError("fixed-query panel pair coverage mismatch")
    query_risks: dict[str, dict[str, Fraction]] = {}
    for query in SECOND_QUERY_CANDIDATES:
        projected = [
            {
                "source_program": row["source_program"],
                "target_program": row["target_program"],
                "stratum": row["stratum"],
                "status": "OK",
                "arm_id": f"GLOBAL_FIXED_QUERY_{query}",
                "lexical_loss": row["fixed_query_losses"][query],
            }
            for row in rows
        ]
        query_risks[query] = reduce_complete_population_rows(projected, expected_arm_id=f"GLOBAL_FIXED_QUERY_{query}")
    minimum = min(risks["NOMINAL"] for risks in query_risks.values())
    minimizers = tuple(query for query in SECOND_QUERY_CANDIDATES if query_risks[query]["NOMINAL"] == minimum)
    return {"selected_query": minimizers[0], "minimizers": minimizers, "query_risks": query_risks}


def reduce_active_necessity(
    candidate_rows: Sequence[Mapping[str, Any]], fixed_query_panel_rows: Sequence[Mapping[str, Any]],
    *, candidate_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER", loss_field: str = "lexical_loss",
) -> dict[str, Any]:
    if loss_field not in {"lexical_loss", "optimistic_loss", "pessimistic_loss"}:
        raise ValueError("unregistered active query-tie loss field")
    if len(candidate_rows) != 16384 or len(fixed_query_panel_rows) != 16384:
        raise ValueError("active-necessity reducer requires complete populations")
    candidate_by_pair = {(row["source_program"], row["target_program"]): row for row in candidate_rows}
    fixed_by_pair = {(row["source_program"], row["target_program"]): row for row in fixed_query_panel_rows}
    if len(candidate_by_pair) != 16384 or set(candidate_by_pair) != set(fixed_by_pair):
        raise ValueError("active-necessity pair coverage mismatch")
    fixed_selection = select_global_fixed_query(fixed_query_panel_rows)
    fixed_query = fixed_selection["selected_query"]
    fixed_nominal_risk = fixed_selection["query_risks"][fixed_query]["NOMINAL"]
    candidate_risks = reduce_complete_population_rows(candidate_rows, expected_arm_id=candidate_arm_id, loss_field=loss_field)
    relative_gain = relative_improvement(candidate_risks["NOMINAL"], fixed_nominal_risk)
    witnesses = []
    for pair, candidate in candidate_by_pair.items():
        fixed_endpoint = fixed_by_pair[pair]["fixed_query_endpoints"][fixed_query]
        comparator = {
            "selected_query": fixed_query,
            "minimizers": (fixed_query,),
            "selected_predictions": fixed_endpoint["predictions"],
            "selected_truth": fixed_endpoint["truth"],
        }
        common = common_unqueried_gain(candidate, comparator)
        if common["unique_nonlexical_query"] and common["gain"] > 0:
            witnesses.append({"source_program": pair[0], "target_program": pair[1], **common})
    return _make_evidence_receipt(
        "reduce_active_necessity",
        input_sources=("candidate_population_rows", "fixed_query_panel_rows"),
        coverage={
            "candidate_arm_id": candidate_arm_id,
            "fixed_query_panel_arm_id": "FIXED_QUERY_PANEL_PRIMARY",
            "loss_field": loss_field,
            "candidate_row_count": len(candidate_rows),
            "fixed_query_panel_row_count": len(fixed_query_panel_rows),
            "candidate_rows_sha256": _population_rows_sha256(candidate_rows),
            "fixed_query_panel_rows_sha256": _population_rows_sha256(fixed_query_panel_rows),
        },
        payload={
            "best_global_fixed_query": fixed_query,
            "best_global_fixed_query_minimizers": fixed_selection["minimizers"],
            "active_vs_best_fixed_relative_gain": relative_gain,
            "unique_nonlexical_positive_forward": bool(witnesses),
            "first_witness": witnesses[0] if witnesses else None,
        },
    )


def control_pareto_matches(candidate_risks: Mapping[str, Fraction], control_risks: Mapping[str, Fraction]) -> bool:
    endpoints = ("NONLOCAL", "EXACT", "LOCAL", "NOMINAL", "SCRATCH_HEAVY")
    if any(endpoint not in candidate_risks or endpoint not in control_risks for endpoint in endpoints):
        raise ValueError("control Pareto endpoint missing")
    return all(control_risks[endpoint] <= candidate_risks[endpoint] for endpoint in endpoints)


def _compute_gate_flags_from_values(
    relative_metrics: Mapping[str, Fraction], *,
    active_vs_best_fixed_relative_gain: Fraction,
    unique_nonlexical_positive_forward: bool,
    source_delete_pass: bool, local_delete_pass: bool,
    feedback_mask_pass: bool, active_delete_pass: bool,
    complete_population: bool, fresh_replay_equal: bool,
    independent_recompute_equal: bool, leakage_positive_controls_rejected: bool,
    private_truth_leakage: bool = False, instrument_invalid: bool = False,
    query_tie_sensitive: bool = False, control_match: bool = False,
) -> dict[str, bool]:
    required_metrics = {
        "nominal_relative_gain", "exact_relative_gain", "local_relative_gain",
        "nonlocal_relative_regret", "scratch_heavy_relative_gain",
    }
    if set(relative_metrics) != required_metrics or any(not isinstance(value, Fraction) for value in relative_metrics.values()):
        raise ValueError("relative metric schema mismatch")
    return {
        "private_truth_leakage": private_truth_leakage,
        "instrument_invalid": instrument_invalid,
        "query_tie_sensitive": query_tie_sensitive,
        "control_match": control_match,
        "complete_population": complete_population,
        "fresh_replay_equal": fresh_replay_equal,
        "independent_recompute_equal": independent_recompute_equal,
        "leakage_positive_controls_rejected": leakage_positive_controls_rejected,
        "nominal_gain_pass": relative_metrics["nominal_relative_gain"] >= Fraction(1, 20),
        "exact_gain_pass": relative_metrics["exact_relative_gain"] >= Fraction(1, 20),
        "local_gain_pass": relative_metrics["local_relative_gain"] >= Fraction(1, 20),
        "nonlocal_safety_pass": relative_metrics["nonlocal_relative_regret"] <= Fraction(1, 20),
        "scratch_heavy_gain_pass": relative_metrics["scratch_heavy_relative_gain"] >= Fraction(1, 100),
        "active_vs_best_fixed_pass": active_vs_best_fixed_relative_gain >= Fraction(1, 100),
        "unique_nonlexical_positive_forward_pass": unique_nonlexical_positive_forward,
        "source_delete_pass": source_delete_pass,
        "local_delete_pass": local_delete_pass,
        "feedback_mask_pass": feedback_mask_pass,
        "active_delete_pass": active_delete_pass,
    }


def reduce_ablation_evidence(
    *, source_delete_reference_receipt: Mapping[str, Any],
    local_delete_reference_receipt: Mapping[str, Any],
    feedback_mask_active_receipt: Mapping[str, Any],
    active_delete_active_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    reference_sources = ("candidate_population_rows", "scratch_population_rows")
    active_sources = ("candidate_population_rows", "fixed_query_panel_rows")
    _validate_evidence_receipt(source_delete_reference_receipt, producer_function="reduce_reference_population", input_sources=reference_sources)
    _validate_evidence_receipt(local_delete_reference_receipt, producer_function="reduce_reference_population", input_sources=reference_sources)
    _validate_evidence_receipt(feedback_mask_active_receipt, producer_function="reduce_active_necessity", input_sources=active_sources)
    _validate_evidence_receipt(active_delete_active_receipt, producer_function="reduce_active_necessity", input_sources=active_sources)
    expected_arms = (
        (source_delete_reference_receipt, "SOURCE_DELETE"),
        (local_delete_reference_receipt, "LOCAL_DELETE"),
        (feedback_mask_active_receipt, "FEEDBACK_MASK"),
        (active_delete_active_receipt, "ACTIVE_DELETE"),
    )
    for receipt, expected_arm in expected_arms:
        coverage = receipt.get("coverage")
        if not isinstance(coverage, Mapping) or coverage.get("candidate_arm_id") != expected_arm or coverage.get("candidate_row_count") != 16384:
            raise ValueError("ablation receipt arm/coverage mismatch")
    source_coverage = source_delete_reference_receipt["coverage"]
    local_coverage = local_delete_reference_receipt["coverage"]
    feedback_coverage = feedback_mask_active_receipt["coverage"]
    active_delete_coverage = active_delete_active_receipt["coverage"]
    if source_coverage.get("loss_field") != "lexical_loss" or local_coverage.get("loss_field") != "lexical_loss":
        raise ValueError("ablation reference loss-field mismatch")
    if feedback_coverage.get("loss_field") != "lexical_loss" or active_delete_coverage.get("loss_field") != "lexical_loss":
        raise ValueError("ablation active loss-field mismatch")
    if source_coverage["scratch_rows_sha256"] != local_coverage["scratch_rows_sha256"]:
        raise ValueError("ablation scratch population lineage mismatch")
    if feedback_coverage["fixed_query_panel_rows_sha256"] != active_delete_coverage["fixed_query_panel_rows_sha256"]:
        raise ValueError("ablation fixed-query population lineage mismatch")
    source_delete_byte_equal = source_coverage["candidate_behavior_sha256"] == source_coverage["scratch_behavior_sha256"]
    source_delete_relative_metrics = source_delete_reference_receipt["relative_metrics"]
    local_delete_relative_metrics = local_delete_reference_receipt["relative_metrics"]
    feedback_rule_survives = (
        feedback_mask_active_receipt["active_vs_best_fixed_relative_gain"] >= Fraction(1, 100)
        and feedback_mask_active_receipt["unique_nonlexical_positive_forward"] is True
    )
    active_delete_rule_survives = (
        active_delete_active_receipt["active_vs_best_fixed_relative_gain"] >= Fraction(1, 100)
        and active_delete_active_receipt["unique_nonlexical_positive_forward"] is True
    )
    payload = {
        "source_delete_pass": (
            source_delete_byte_equal
            and
            source_delete_relative_metrics["nominal_relative_gain"] < Fraction(1, 20)
            and source_delete_relative_metrics["exact_relative_gain"] < Fraction(1, 20)
        ),
        "local_delete_pass": local_delete_relative_metrics["local_relative_gain"] < Fraction(1, 20),
        "feedback_mask_pass": not feedback_rule_survives,
        "active_delete_pass": not active_delete_rule_survives,
        "source_delete_relative_metrics": source_delete_relative_metrics,
        "local_delete_relative_metrics": local_delete_relative_metrics,
        "feedback_mask_active_vs_best_fixed_relative_gain": feedback_mask_active_receipt["active_vs_best_fixed_relative_gain"],
        "active_delete_active_vs_best_fixed_relative_gain": active_delete_active_receipt["active_vs_best_fixed_relative_gain"],
    }
    return _make_evidence_receipt(
        "reduce_ablation_evidence",
        input_sources=(
            "source_delete_reference_receipt", "local_delete_reference_receipt",
            "feedback_mask_active_receipt", "active_delete_active_receipt",
        ),
        coverage={
            "source_delete_receipt_sha256": source_delete_reference_receipt["receipt_sha256"],
            "local_delete_receipt_sha256": local_delete_reference_receipt["receipt_sha256"],
            "feedback_mask_receipt_sha256": feedback_mask_active_receipt["receipt_sha256"],
            "active_delete_receipt_sha256": active_delete_active_receipt["receipt_sha256"],
            "scratch_rows_sha256": source_coverage["scratch_rows_sha256"],
            "fixed_query_panel_rows_sha256": feedback_coverage["fixed_query_panel_rows_sha256"],
            "source_delete_behavior_sha256": source_coverage["candidate_behavior_sha256"],
            "scratch_behavior_sha256": source_coverage["scratch_behavior_sha256"],
        },
        payload=payload,
    )


def reduce_query_tie_evidence(
    *, lexical_verdict_receipt: Mapping[str, Any],
    optimistic_verdict_receipt: Mapping[str, Any],
    pessimistic_verdict_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    branches = (lexical_verdict_receipt, optimistic_verdict_receipt, pessimistic_verdict_receipt)
    for receipt in branches:
        _validate_evidence_receipt(receipt, producer_function="dispatch_verdict_evidence", input_sources=("computed_gate_receipt",))
        coverage = receipt.get("coverage")
        if not isinstance(coverage, Mapping) or coverage.get("gate_phase") != "PRE_TIE":
            raise ValueError("query-tie branch receipt phase mismatch")
    branch_kinds = tuple(receipt["coverage"].get("branch_kind") for receipt in branches)
    if branch_kinds != ("LEXICAL", "OPTIMISTIC", "PESSIMISTIC"):
        raise ValueError("query-tie branch labels mismatch")
    branch_hashes = tuple(receipt["receipt_sha256"] for receipt in branches)
    if len(set(branch_hashes)) != 3:
        raise ValueError("query-tie branch receipts must be distinct")
    verdicts = tuple(receipt["verdict"] for receipt in branches)
    if any(verdict not in VERDICT_PRIORITY for verdict in verdicts):
        raise ValueError("unregistered query-tie verdict")
    payload = {
        "lexical_verdict": verdicts[0],
        "optimistic_verdict": verdicts[1],
        "pessimistic_verdict": verdicts[2],
        "query_tie_sensitive": len(set(verdicts)) != 1,
    }
    return _make_evidence_receipt(
        "reduce_query_tie_evidence",
        input_sources=("lexical_verdict_receipt", "optimistic_verdict_receipt", "pessimistic_verdict_receipt"),
        coverage={
            "branch_count": 3,
            "branch_receipt_sha256s": branch_hashes,
            "branch_kinds": branch_kinds,
        },
        payload=payload,
    )


def reduce_control_evidence(
    candidate_reference_receipt: Mapping[str, Any],
    control_reference_receipts_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if set(control_reference_receipts_by_id) != set(INVALIDATING_CONTROL_IDS):
        raise ValueError("control receipt set mismatch")
    sources = ("candidate_population_rows", "scratch_population_rows")
    _validate_evidence_receipt(candidate_reference_receipt, producer_function="reduce_reference_population", input_sources=sources)
    candidate_coverage = candidate_reference_receipt.get("coverage")
    if not isinstance(candidate_coverage, Mapping) or candidate_coverage.get("candidate_arm_id") != "MIXTURE_BMA_ACTIVE_BRIER" or candidate_coverage.get("candidate_row_count") != 16384:
        raise ValueError("candidate control receipt coverage mismatch")
    if candidate_coverage.get("loss_field") not in {"lexical_loss", "optimistic_loss", "pessimistic_loss"}:
        raise ValueError("candidate control receipt loss-field mismatch")
    for control_id, receipt in control_reference_receipts_by_id.items():
        _validate_evidence_receipt(receipt, producer_function="reduce_reference_population", input_sources=sources)
        coverage = receipt.get("coverage")
        if not isinstance(coverage, Mapping) or coverage.get("candidate_arm_id") != control_id or coverage.get("candidate_row_count") != 16384:
            raise ValueError("control receipt arm/coverage mismatch")
        if coverage.get("loss_field") != candidate_coverage.get("loss_field") or coverage.get("scratch_rows_sha256") != candidate_coverage.get("scratch_rows_sha256"):
            raise ValueError("control receipt scratch/loss lineage mismatch")
    candidate_risks = candidate_reference_receipt["candidate_risks"]
    matches = tuple(sorted(
        control_id for control_id, receipt in control_reference_receipts_by_id.items()
        if control_pareto_matches(candidate_risks, receipt["candidate_risks"])
    ))
    return _make_evidence_receipt(
        "reduce_control_evidence",
        input_sources=("candidate_reference_receipt", "control_reference_receipts"),
        coverage={
            "candidate_receipt_sha256": candidate_reference_receipt["receipt_sha256"],
            "control_receipt_sha256s": {
                control_id: receipt["receipt_sha256"]
                for control_id, receipt in sorted(control_reference_receipts_by_id.items())
            },
            "control_count": len(control_reference_receipts_by_id),
        },
        payload={
        "pareto_match_ids": matches,
        "control_match": bool(matches),
        },
    )


def _canonical_row_bytes(row: Mapping[str, Any]) -> bytes:
    return json.dumps(_jsonify(row), sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_behavior_row_bytes(row: Mapping[str, Any]) -> bytes:
    normalized = {key: value for key, value in row.items() if key != "producer_function"}
    return _canonical_row_bytes(normalized)


def _produce_population_stream_receipt(
    rows: Sequence[Mapping[str, Any]], *, producer_function: str, input_source: str,
    expected_arm_id: str, expected_row_producer_function: str,
) -> dict[str, Any]:
    observed_pairs: set[tuple[int, int]] = set()
    for row in rows:
        source = row.get("source_program")
        target = row.get("target_program")
        pair = (source, target)
        if (
            row.get("status") != "OK" or row.get("arm_id") != expected_arm_id
            or not isinstance(source, int) or isinstance(source, bool)
            or not isinstance(target, int) or isinstance(target, bool)
            or source < 0 or source >= 128 or target < 0 or target >= 128
            or pair in observed_pairs or row.get("stratum") != classify_pair(source, target)
            or not isinstance(row.get("lexical_loss"), Fraction) or row["lexical_loss"] < 0
        ):
            raise ValueError("population stream row schema/coverage mismatch")
        observed_pairs.add(pair)
    if any(row.get("producer_function") != expected_row_producer_function for row in rows):
        raise ValueError("population stream row producer mismatch")
    return _make_evidence_receipt(
        producer_function,
        input_sources=(input_source,),
        coverage={
            "arm_id": expected_arm_id,
            "row_producer_function": expected_row_producer_function,
            "row_count": len(rows),
            "rows_sha256": _population_rows_sha256(rows),
        },
        payload={"rows": tuple(copy.deepcopy(list(rows)))},
    )


def produce_primary_population_stream(
    rows: Sequence[Mapping[str, Any]], *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    return _produce_population_stream_receipt(
        rows, producer_function="produce_primary_population_stream",
        input_source="primary_population_rows", expected_arm_id=expected_arm_id,
        expected_row_producer_function="evaluate_pair",
    )


def produce_fresh_replay_stream(
    rows: Sequence[Mapping[str, Any]], *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    return _produce_population_stream_receipt(
        rows, producer_function="produce_fresh_replay_stream",
        input_source="fresh_process_replay_rows", expected_arm_id=expected_arm_id,
        expected_row_producer_function="replay_pair",
    )


def produce_independent_recompute_stream(
    case_pairs: Sequence[tuple[int, int]], *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    pairs = tuple(case_pairs)
    for pair in pairs:
        if (
            not isinstance(pair, tuple) or len(pair) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 128 for value in pair)
        ):
            raise ValueError("population stream invalid case pair")
    if len(set(pairs)) != len(pairs):
        raise ValueError("population stream duplicate case pair")
    rows = tuple(recompute_pair(source, target, mode="primary") for source, target in pairs)
    return _produce_population_stream_receipt(
        rows, producer_function="produce_independent_recompute_stream",
        input_source="case_pairs", expected_arm_id=expected_arm_id,
        expected_row_producer_function="recompute_pair",
    )


def produce_leakage_scan_stream(leakage_cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return _make_evidence_receipt(
        "produce_leakage_scan_stream",
        input_sources=("leakage_scan_receipts",),
        coverage={"case_count": len(leakage_cases), "cases_sha256": _evidence_sha256(leakage_cases)},
        payload={"cases": tuple(copy.deepcopy(list(leakage_cases)))},
    )


def reduce_formal_integrity_evidence(
    primary_stream_receipt: Mapping[str, Any],
    replay_stream_receipt: Mapping[str, Any],
    independent_stream_receipt: Mapping[str, Any],
    leakage_stream_receipt: Mapping[str, Any],
    *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    expected_count = 16384
    primary_code_hash = _compute_sha256(REPO_ROOT / "scripts/codex/check_ego_v2_compositional_causal_transfer_preflight_001e.py")
    independent_code_hash = _compute_sha256(Path(__file__))
    _validate_evidence_receipt(
        primary_stream_receipt, producer_function="produce_primary_population_stream",
        input_sources=("case_pairs",), expected_code_path_hash=primary_code_hash,
    )
    _validate_evidence_receipt(
        replay_stream_receipt, producer_function="produce_fresh_replay_stream",
        input_sources=("primary_population_stream_receipt",), expected_code_path_hash=primary_code_hash,
    )
    _validate_evidence_receipt(
        independent_stream_receipt, producer_function="produce_independent_recompute_stream",
        input_sources=("case_pairs",), expected_code_path_hash=independent_code_hash,
    )
    _validate_evidence_receipt(
        leakage_stream_receipt, producer_function="produce_leakage_scan_stream",
        input_sources=("leakage_scan_receipts",), expected_code_path_hash=primary_code_hash,
    )
    primary_rows = primary_stream_receipt["rows"]
    replay_rows = replay_stream_receipt["rows"]
    independent_rows = independent_stream_receipt["rows"]
    leakage_cases = leakage_stream_receipt["cases"]
    expected_row_producers = ("evaluate_pair", "replay_pair", "recompute_pair")
    for stream, expected_row_producer in zip(
        (primary_stream_receipt, replay_stream_receipt, independent_stream_receipt),
        expected_row_producers,
    ):
        coverage = stream["coverage"]
        if coverage["arm_id"] != expected_arm_id or coverage["row_producer_function"] != expected_row_producer or coverage["row_count"] != expected_count or coverage["rows_sha256"] != _population_rows_sha256(stream["rows"]):
            raise ValueError("population stream arm/count/hash mismatch")
    if leakage_stream_receipt["coverage"]["case_count"] != len(leakage_cases) or leakage_stream_receipt["coverage"]["cases_sha256"] != _evidence_sha256(leakage_cases):
        raise ValueError("leakage stream count/hash mismatch")
    reduce_complete_population_rows(primary_rows, expected_arm_id=expected_arm_id)
    reduce_complete_population_rows(replay_rows, expected_arm_id=expected_arm_id)
    reduce_complete_population_rows(independent_rows, expected_arm_id=expected_arm_id)
    primary_bytes = tuple(_canonical_behavior_row_bytes(row) for row in primary_rows)
    replay_bytes = tuple(_canonical_behavior_row_bytes(row) for row in replay_rows)
    independent_bytes = tuple(_canonical_behavior_row_bytes(row) for row in independent_rows)
    replay_mismatch_count = sum(left != right for left, right in zip(primary_bytes, replay_bytes)) + abs(len(primary_bytes) - len(replay_bytes))
    independent_mismatch_count = sum(left != right for left, right in zip(primary_bytes, independent_bytes)) + abs(len(primary_bytes) - len(independent_bytes))
    for case in leakage_cases:
        if (
            case.get("status") != "OK"
            or case.get("producer_function") != "scan_public_input"
            or not isinstance(case.get("positive_control"), bool)
            or not isinstance(case.get("accepted"), bool)
        ):
            raise ValueError("leakage scan receipt status/producer/schema mismatch")
    case_ids = tuple(case.get("case_id") for case in leakage_cases)
    if len(set(case_ids)) != len(case_ids) or set(case_ids) != set(LEAKAGE_CASE_IDS):
        raise ValueError("leakage scan case coverage mismatch")
    positive = [case for case in leakage_cases if case["positive_control"] is True]
    clean = [case for case in leakage_cases if case["positive_control"] is False]
    leakage_ok = (
        bool(positive) and bool(clean)
        and all(case.get("accepted") is False for case in positive)
        and all(case.get("accepted") is True for case in clean)
    )
    return _make_evidence_receipt(
        "reduce_formal_integrity_evidence",
        input_sources=("primary_stream_receipt", "replay_stream_receipt", "independent_stream_receipt", "leakage_stream_receipt"),
        coverage={
            "expected_arm_id": expected_arm_id,
            "expected_row_count": expected_count,
            "primary_stream_sha256": primary_stream_receipt["receipt_sha256"],
            "replay_stream_sha256": replay_stream_receipt["receipt_sha256"],
            "independent_stream_sha256": independent_stream_receipt["receipt_sha256"],
            "primary_rows_sha256": _population_rows_sha256(primary_rows),
            "replay_rows_sha256": _population_rows_sha256(replay_rows),
            "independent_rows_sha256": _population_rows_sha256(independent_rows),
            "leakage_cases_sha256": _evidence_sha256(leakage_cases),
        },
        payload={
        "expected_row_count": expected_count,
        "primary_row_count": len(primary_rows),
        "replay_mismatch_count": replay_mismatch_count,
        "independent_mismatch_count": independent_mismatch_count,
        "positive_leakage_case_count": len(positive),
        "clean_leakage_case_count": len(clean),
        "complete_population": len(primary_rows) == expected_count,
        "fresh_replay_equal": len(replay_rows) == expected_count and replay_mismatch_count == 0,
        "independent_recompute_equal": len(independent_rows) == expected_count and independent_mismatch_count == 0,
        "leakage_positive_controls_rejected": leakage_ok,
        "private_truth_leakage": any(case.get("observed_private_truth") is True and case["accepted"] is True for case in leakage_cases),
        "instrument_invalid": False,
        },
    )


def compute_gate_flags_from_evidence(*args: Any, **kwargs: Any) -> dict[str, Any]:
    del args, kwargs
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


def dispatch_verdict_evidence(*args: Any, **kwargs: Any) -> dict[str, Any]:
    del args, kwargs
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


def _source_table(program_id: int) -> list[dict[str, Any]]:
    return [{"composition": composition, "outcome": _evaluate(program_id, composition)} for composition in COMPOSITIONS]


def recompute_pair(source_program: int, target_program: int, *, mode: str = "primary") -> dict[str, Any]:
    if mode not in {"primary", "scratch"}:
        raise ValueError("independent pair recomputation supports primary or scratch")
    public_input = {
        "source_truth_table": _source_table(source_program),
        "target_history": [{"composition": "000", "outcome": _evaluate(target_program, "000")}],
        "query_count": 0,
        "query_budget": 1,
        "arm_semantics": "MIXTURE_BMA_ACTIVE_BRIER" if mode == "primary" else "SCRATCH_SPIKE_SLAB_ACTIVE_BAYES",
        "serialized_state": {"schema": "caot_bool_v2_stateless_v1"},
    }
    history = _history(public_input)
    query_record = _choose_query(public_input, history, mode)
    losses: dict[str, Fraction] = {}
    for query in query_record["minimizers"]:
        updated_history = tuple(history) + ((query, _evaluate(target_program, query)),)
        posterior = _posterior(public_input, updated_history, mode)
        remaining = [composition for composition in COMPOSITIONS if composition not in dict(updated_history)]
        losses[query] = sum(
            (_predictive_probability(posterior, composition) - _evaluate(target_program, composition)) ** 2
            for composition in remaining
        ) / len(remaining)
    return {
        "source_program": source_program,
        "target_program": target_program,
        "stratum": classify_pair(source_program, target_program),
        "arm_id": public_input["arm_semantics"],
        "status": "OK",
        "producer_function": "recompute_pair",
        "selected_query": query_record["selected_query"],
        "minimizers": query_record["minimizers"],
        "minimizer_losses": losses,
        "lexical_loss": losses[query_record["selected_query"]],
        "optimistic_loss": min(losses.values()),
        "pessimistic_loss": max(losses.values()),
    }


def _dispatch_verdict_values(aggregate: Mapping[str, Any]) -> str:
    if aggregate.get("private_truth_leakage"):
        return VERDICT_PRIORITY[0]
    required = {
        "private_truth_leakage", "instrument_invalid", "query_tie_sensitive",
        "control_match", *INTEGRITY_GATE_FIELDS, *POSITIVE_GATE_FIELDS,
    }
    if set(aggregate).issuperset(required) is False:
        return VERDICT_PRIORITY[1]
    if aggregate.get("instrument_invalid") or any(aggregate.get(field) is not True for field in INTEGRITY_GATE_FIELDS):
        return VERDICT_PRIORITY[1]
    if aggregate.get("query_tie_sensitive"):
        return VERDICT_PRIORITY[2]
    if aggregate.get("control_match"):
        return VERDICT_PRIORITY[3]
    if any(aggregate.get(field) is not True for field in POSITIVE_GATE_FIELDS):
        return VERDICT_PRIORITY[4]
    return VERDICT_PRIORITY[5]


def dispatch_verdict(aggregate: Mapping[str, Any]) -> str:
    if aggregate.get("producer_function") in {
        "compute_gate_flags_from_evidence",
        "dispatch_verdict_evidence",
    }:
        raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)
    return _dispatch_verdict_values(aggregate)

def run_formal_population(*, output_dir: Path) -> None:
    del output_dir
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


def main() -> int:
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


if __name__ == "__main__":
    main()
