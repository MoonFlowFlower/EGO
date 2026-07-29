from __future__ import annotations

import copy
import base64
import hashlib
import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_ID = "EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E"
FORMAL_BLOCK = "FORMAL_EXECUTION_NOT_AUTHORIZED_001E_I1"
REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_CARD_PATH = REPO_ROOT / "docs/codex/tasks/EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E.md"
COLLISION_PATH = REPO_ROOT / "docs/codex/tasks/ego-v2-p1-compositional-causal-transfer-preflight-001e/COLLISION_RECORD.md"
FROZEN_DESIGN_PATH = REPO_ROOT / "docs/codex/tasks/ego-v2-p1-compositional-causal-transfer-preflight-001e/FROZEN_DESIGN.json"
I1_CARD_PATH = REPO_ROOT / "docs/codex/tasks/EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-IMPLEMENTATION-001E-I1.md"

AUTHORITY_SHA256 = {
    "001e_card": "83fb2a5b7e2a26f5dc9408962768f4329f3c5932405b82142394804c7e9a3619",
    "001e_collision": "265d530c584bd38cf76b11c374475cb9678b37ec889484c35a4cbc25c23659b4",
    "001e_design": "8a60c0e8521b02d7423fa5320ba8013e29c128e27aaec1a4a3ee4674fac0027d",
    "001e_i1_card": "59e43ac6168f4da7288474b269f4f7474f77c631a5ad6f04ae6d24d463c6575a",
}

COMPOSITIONS = tuple(f"{value:03b}" for value in range(8))
SECOND_QUERY_CANDIDATES = COMPOSITIONS[1:]
COEFFICIENT_ORDER = ("b0", "b1", "b2", "b3", "b12", "b13", "b23")
FAMILY_ORDER = ("SCRATCH", "EXACT_SOURCE", "LOCAL_SHIFT")
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
CONTROL_REGISTRY = {name: name for name in CONTROL_IDS}
INVALIDATING_CONTROL_IDS = tuple(
    control_id for control_id in CONTROL_IDS
    if control_id not in {
        "CANDIDATE_RULE_AMORTIZED_LOOKUP",
        "TRANSITION_TABLE", "SUCCESSOR_MAP", "FSM_PLANNER",
    }
)

ABLATION_IDS = (
    "SOURCE_DELETE", "LOCAL_DELETE", "FEEDBACK_MASK", "ACTIVE_DELETE",
    "UNIFORM_SCRATCH_PRIOR", "SOURCE_TABLE_ROW_PERMUTE", "VARIABLE_RELABEL",
    "SERIALIZED_STATE_RESET", "SERIALIZED_STATE_SWAP",
    "HIDDEN_COEFFICIENT_POSITIVE_CONTROL", "HIDDEN_RELATION_POSITIVE_CONTROL",
)
ABLATION_REGISTRY = {name: name for name in ABLATION_IDS}

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


class DesignValidationError(ValueError):
    pass


class PrivateTruthLeakageError(ValueError):
    pass


class ArtifactValidationError(ValueError):
    pass


class FormalExecutionNotAuthorizedError(RuntimeError):
    pass


class InferenceSourceAccessError(RuntimeError):
    pass


class _InferenceSourceGuard(Mapping[str, Any]):
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = payload
        self.source_access_count = 0

    def __getitem__(self, key: str) -> Any:
        if key == "source_truth_table":
            self.source_access_count += 1
            raise InferenceSourceAccessError("scratch inference accessed source_truth_table")
        return self._payload[key]

    def __iter__(self):
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_design() -> dict[str, Any]:
    design = json.loads(FROZEN_DESIGN_PATH.read_text(encoding="utf-8"))
    validate_design_schema(design)
    return design


def validate_design_schema(design: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "task_id", "program_grammar", "scratch_prior",
        "family_prior", "public_history", "inference", "population", "arms",
        "ablations", "ablation_semantics", "gates", "verdict_priority",
        "product_firewall", "authorization", "claim_ceiling",
    }
    missing = sorted(required.difference(design))
    if missing:
        raise DesignValidationError(f"missing design fields: {missing}")
    if design["task_id"] != TASK_ID:
        raise DesignValidationError("task_id drift")
    if design["program_grammar"].get("program_count") != 128:
        raise DesignValidationError("program_count drift")
    if tuple(design["verdict_priority"]) != VERDICT_PRIORITY:
        raise DesignValidationError("verdict priority drift")
    if design["authorization"].get("formal_run") is not False:
        raise DesignValidationError("formal-run authority drift")


def validate_authorities() -> dict[str, str]:
    actual = {
        "001e_card": compute_sha256(AUTHORITY_CARD_PATH),
        "001e_collision": compute_sha256(COLLISION_PATH),
        "001e_design": compute_sha256(FROZEN_DESIGN_PATH),
        "001e_i1_card": compute_sha256(I1_CARD_PATH),
    }
    if actual != AUTHORITY_SHA256:
        raise DesignValidationError(f"authority drift: {actual}")
    load_frozen_design()
    return actual


def iter_compositions() -> tuple[str, ...]:
    return COMPOSITIONS


def program_bits(program_id: int) -> tuple[int, ...]:
    if not isinstance(program_id, int) or not 0 <= program_id < 128:
        raise ValueError("program_id must be in 0..127")
    return tuple((program_id >> shift) & 1 for shift in range(6, -1, -1))


def _composition_bits(composition: str) -> tuple[int, int, int]:
    if composition not in COMPOSITIONS:
        raise ValueError(f"invalid composition: {composition}")
    return tuple(int(bit) for bit in composition)  # type: ignore[return-value]


def evaluate_program(program_id: int, composition: str) -> dict[str, Any]:
    coefficients = program_bits(program_id)
    x1, x2, x3 = _composition_bits(composition)
    factors = (1, x1, x2, x3, x1 * x2, x1 * x3, x2 * x3)
    term_trace: list[dict[str, Any]] = []
    cumulative = 0
    for name, coefficient, factor in zip(COEFFICIENT_ORDER, coefficients, factors):
        term = coefficient * factor
        cumulative ^= term
        term_trace.append({
            "coefficient": name,
            "coefficient_value": coefficient,
            "factor": factor,
            "term": term,
            "cumulative_xor": cumulative,
        })
    return {
        "program_id": program_id,
        "composition": composition,
        "outcome": cumulative,
        "term_trace": term_trace,
        "cumulative_xor": tuple(item["cumulative_xor"] for item in term_trace),
    }


@lru_cache(maxsize=1024)
def _program_outcome(program_id: int, composition: str) -> int:
    coefficients = program_bits(program_id)
    x1, x2, x3 = _composition_bits(composition)
    factors = (1, x1, x2, x3, x1 * x2, x1 * x3, x2 * x3)
    value = 0
    for coefficient, factor in zip(coefficients, factors):
        value ^= coefficient * factor
    return value


def build_source_truth_table(program_id: int) -> list[dict[str, Any]]:
    return [
        {"composition": composition, "outcome": _program_outcome(program_id, composition)}
        for composition in COMPOSITIONS
    ]


def scratch_prior_mass(program_id: int) -> Fraction:
    k = sum(program_bits(program_id)[1:])
    return Fraction(3 ** (6 - k), 8192)


def local_neighbors(source_program: int) -> tuple[int, ...]:
    result = []
    for bit_index in range(1, 7):
        shift = 6 - bit_index
        result.append(source_program ^ (1 << shift))
    return tuple(result)


def unconditional_program_weights(source_program: int) -> dict[int, int]:
    local = set(local_neighbors(source_program))
    result: dict[int, int] = {}
    for program_id in range(128):
        k = sum(program_bits(program_id)[1:])
        result[program_id] = (
            3 * (3 ** (6 - k))
            + (24576 if program_id == source_program else 0)
            + (4096 if program_id in local else 0)
        )
    return result


def _canonical_rows(rows: Sequence[Mapping[str, Any]], *, complete: bool) -> tuple[tuple[str, int], ...]:
    allowed = set(COMPOSITIONS)
    canonical: dict[str, int] = {}
    for row in rows:
        if set(row) != {"composition", "outcome"}:
            raise PrivateTruthLeakageError("row schema contains non-public fields")
        composition = row["composition"]
        outcome = row["outcome"]
        if composition not in allowed or outcome not in (0, 1) or composition in canonical:
            raise ValueError("invalid or duplicate public row")
        canonical[str(composition)] = int(outcome)
    if complete and set(canonical) != allowed:
        raise ValueError("source truth table must contain all eight rows")
    return tuple(sorted(canonical.items()))


def _infer_source_program(source_table: Sequence[Mapping[str, Any]]) -> int:
    canonical = _canonical_rows(source_table, complete=True)
    matches = [pid for pid in range(128) if tuple((r["composition"], r["outcome"]) for r in build_source_truth_table(pid)) == canonical]
    if len(matches) != 1:
        raise DesignValidationError("source truth table does not identify exactly one frozen program")
    return matches[0]


def _scan_value(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            compact = "".join(character for character in normalized if character.isalnum())
            forbidden_compact = {"".join(character for character in item if character.isalnum()) for item in FORBIDDEN_KEYS}
            if normalized in FORBIDDEN_KEYS or compact in forbidden_compact:
                raise PrivateTruthLeakageError(f"forbidden field at {'.'.join(path + (str(key),))}")
            _scan_value(child, path + (str(key),))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_value(child, path + (str(index),))
    elif isinstance(value, str):
        lowered = value.lower()
        aliases = tuple(sorted(FORBIDDEN_KEYS)) + ("hidden_coefficient", "hidden_relation")
        if any(alias in lowered for alias in aliases):
            raise PrivateTruthLeakageError(f"encoded private alias at {'.'.join(path)}")
        decoded_candidates: list[str] = []
        try:
            decoded_candidates.append(base64.b64decode(value, validate=True).decode("utf-8").lower())
        except Exception:
            pass
        try:
            decoded_candidates.append(bytes.fromhex(value).decode("utf-8").lower())
        except Exception:
            pass
        if any(any(alias in decoded for alias in aliases) for decoded in decoded_candidates):
            raise PrivateTruthLeakageError(f"encoded private alias at {'.'.join(path)}")


def scan_public_input(public_input: Mapping[str, Any]) -> dict[str, Any]:
    required = {"source_truth_table", "target_history", "query_count", "query_budget", "arm_semantics", "serialized_state"}
    if set(public_input) != required:
        extras = sorted(set(public_input).difference(required))
        missing = sorted(required.difference(public_input))
        if extras and any(str(item).lower() in FORBIDDEN_KEYS for item in extras):
            raise PrivateTruthLeakageError(f"forbidden public fields: {extras}")
        raise PrivateTruthLeakageError(f"public schema mismatch extras={extras} missing={missing}")
    _scan_value(public_input)
    _canonical_rows(public_input["source_truth_table"], complete=True)
    history = _canonical_rows(public_input["target_history"], complete=False)
    if not history or history[0][0] != "000":
        raise ValueError("target history must begin at 000")
    if public_input["query_budget"] != 1 or public_input["query_count"] != len(history) - 1:
        raise ValueError("query budget/count drift")
    return {"accepted": True, "legal_field_count": len(required)}


def build_public_input(
    *, source_table: Sequence[Mapping[str, Any]], target_history: Sequence[Mapping[str, Any]],
    query_budget: int, arm_id: str, serialized_state: Mapping[str, Any],
) -> dict[str, Any]:
    result = {
        "source_truth_table": copy.deepcopy(list(source_table)),
        "target_history": copy.deepcopy(list(target_history)),
        "query_count": max(0, len(target_history) - 1),
        "query_budget": query_budget,
        "arm_semantics": str(arm_id),
        "serialized_state": copy.deepcopy(dict(serialized_state)),
    }
    scan_public_input(result)
    return result


def history_from_public_input(public_input: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    scan_public_input(public_input)
    return _canonical_rows(public_input["target_history"], complete=False)


def _compatible(program_id: int, history: Sequence[tuple[str, int]]) -> bool:
    return all(_program_outcome(program_id, composition) == outcome for composition, outcome in history)


def _normalize_weights(weights: Mapping[int, Fraction | int]) -> tuple[dict[int, Fraction], Fraction]:
    exact = {pid: Fraction(value) for pid, value in weights.items() if value > 0}
    total = sum(exact.values(), Fraction(0, 1))
    if total <= 0:
        raise DesignValidationError("zero posterior mass")
    return exact, total


def _family_marginals(source_program: int, history: Sequence[tuple[str, int]]) -> dict[str, Fraction]:
    scratch = sum((scratch_prior_mass(pid) for pid in range(128) if _compatible(pid, history)), Fraction(0, 1))
    exact = Fraction(int(_compatible(source_program, history)), 1)
    local = Fraction(sum(_compatible(pid, history) for pid in local_neighbors(source_program)), 6)
    return {"SCRATCH": scratch, "EXACT_SOURCE": exact, "LOCAL_SHIFT": local}


def _posterior(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], mode: str) -> dict[str, Any]:
    source_program: int | None = None
    family_posteriors: dict[str, Fraction] = {}
    reported_marginals: dict[str, Fraction] = {}
    if mode == "scratch":
        weights = {pid: scratch_prior_mass(pid) for pid in range(128) if _compatible(pid, history)}
        reported_marginals = {
            "SCRATCH": sum(weights.values(), Fraction(0, 1)),
            "EXACT_SOURCE": Fraction(0, 1),
            "LOCAL_SHIFT": Fraction(0, 1),
        }
    else:
        source_program = _infer_source_program(public_input["source_truth_table"])
        local = set(local_neighbors(source_program))
        if mode == "primary":
            weights = {pid: Fraction(weight, 73728) for pid, weight in unconditional_program_weights(source_program).items() if _compatible(pid, history)}
            reported_marginals = _family_marginals(source_program, history)
        elif mode == "uniform_scratch_primary":
            weights = {
                pid: Fraction(1, 384) + (Fraction(1, 3) if pid == source_program else 0) + (Fraction(1, 18) if pid in local else 0)
                for pid in range(128) if _compatible(pid, history)
            }
            reported_marginals = {
                "SCRATCH": Fraction(sum(_compatible(pid, history) for pid in range(128)), 128),
                "EXACT_SOURCE": Fraction(int(_compatible(source_program, history)), 1),
                "LOCAL_SHIFT": Fraction(sum(_compatible(pid, history) for pid in local), 6),
            }
        elif mode in {"exact", "source_consistency"}:
            if _compatible(source_program, history):
                weights = {source_program: Fraction(1, 1)}
                reported_marginals = {"EXACT_SOURCE": Fraction(1, 1)}
            else:
                return _posterior(public_input, history, "scratch")
        elif mode == "local":
            weights = {pid: Fraction(1, 6) for pid in local if _compatible(pid, history)}
            if not weights:
                return _posterior(public_input, history, "scratch")
            reported_marginals = {"LOCAL_SHIFT": sum(weights.values(), Fraction(0, 1))}
        elif mode == "local_delete":
            weights = {
                pid: Fraction(scratch_prior_mass(pid), 2) + (Fraction(1, 2) if pid == source_program else 0)
                for pid in range(128) if _compatible(pid, history)
            }
            original = _family_marginals(source_program, history)
            reported_marginals = {
                "SCRATCH": original["SCRATCH"],
                "EXACT_SOURCE": original["EXACT_SOURCE"],
                "LOCAL_SHIFT": Fraction(0, 1),
            }
        elif mode == "hard_family":
            marginals = _family_marginals(source_program, history)
            maximum = max(marginals.values())
            selected = next(family for family in FAMILY_ORDER if marginals[family] == maximum)
            submode = {"SCRATCH": "scratch", "EXACT_SOURCE": "exact", "LOCAL_SHIFT": "local"}[selected]
            result = _posterior(public_input, history, submode)
            result["selected_family"] = selected
            result["tied_families"] = tuple(f for f in FAMILY_ORDER if marginals[f] == maximum)
            result["hard_family_marginals"] = marginals
            return result
        elif mode == "nearest":
            candidates = [pid for pid in range(128) if _compatible(pid, history)]
            minimum = min(sum(a != b for a, b in zip(program_bits(pid), program_bits(source_program))) for pid in candidates)
            nearest = [pid for pid in candidates if sum(a != b for a, b in zip(program_bits(pid), program_bits(source_program))) == minimum]
            weights = {pid: Fraction(1, len(nearest)) for pid in nearest}
            reported_marginals = {"NEAREST_SOURCE": Fraction(1, 1)}
        else:
            raise ValueError(f"unknown posterior mode: {mode}")
        marginal_total = sum(reported_marginals.values(), Fraction(0, 1))
        family_posteriors = {family: value / marginal_total for family, value in reported_marginals.items()}
    normalized, total = _normalize_weights(weights)
    if not family_posteriors:
        family_posteriors = {"SCRATCH": Fraction(1, 1), "EXACT_SOURCE": Fraction(0), "LOCAL_SHIFT": Fraction(0)}
    return {
        "weights": normalized,
        "posterior_total_weight": total,
        "family_marginals": reported_marginals,
        "family_posteriors": family_posteriors,
        "mode": mode,
    }


def compute_primary_posterior(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]]) -> dict[str, Any]:
    scan_public_input(public_input)
    return _posterior(public_input, history, "primary")


def compute_posterior_receipt(public_input: Mapping[str, Any], *, mode: str = "primary") -> dict[str, Any]:
    scan_public_input(public_input)
    posterior = _posterior(public_input, history_from_public_input(public_input), mode)
    return {
        "posterior_total_weight": posterior["posterior_total_weight"],
        "family_marginals": copy.deepcopy(posterior["family_marginals"]),
        "family_posteriors": copy.deepcopy(posterior["family_posteriors"]),
    }


def predictive_probability(posterior: Mapping[str, Any], composition: str) -> Fraction:
    weights: Mapping[int, Fraction] = posterior["weights"]
    total = posterior["posterior_total_weight"]
    numerator = sum((weight for pid, weight in weights.items() if _program_outcome(pid, composition) == 1), Fraction(0, 1))
    return numerator / total


def _query_score(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], query: str, mode: str) -> Fraction:
    base = _posterior(public_input, history, mode)
    probability_one = predictive_probability(base, query)
    score = Fraction(0, 1)
    for outcome, probability in ((0, 1 - probability_one), (1, probability_one)):
        if probability == 0:
            continue
        updated_history = tuple(history) + ((query, outcome),)
        updated = _posterior(public_input, updated_history, mode)
        remaining = [composition for composition in COMPOSITIONS if composition not in {item[0] for item in updated_history}]
        terminal = sum((lambda p: p * (1 - p))(predictive_probability(updated, composition)) for composition in remaining)
        score += probability * terminal
    return score


def choose_query(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], *, mode: str = "primary") -> dict[str, Any]:
    scores = {query: _query_score(public_input, history, query, mode) for query in SECOND_QUERY_CANDIDATES if query not in {item[0] for item in history}}
    minimum = min(scores.values())
    minimizers = tuple(sorted(query for query, score in scores.items() if score == minimum))
    selected = minimizers[0]
    return {
        "selected_query": selected,
        "minimizers": minimizers,
        "query_scores": scores,
        "lexical_terminal_loss": scores[selected],
        "optimistic_terminal_loss": min(scores[q] for q in minimizers),
        "pessimistic_terminal_loss": max(scores[q] for q in minimizers),
    }


def endpoint_brier_risk(public_input: Mapping[str, Any], history: Sequence[tuple[str, int]], *, fixed_query: str) -> Fraction:
    return _query_score(public_input, history, fixed_query, "primary")


def _record_for_mode(arm_id: str, public_input: Mapping[str, Any], mode: str, *, fixed_query: str | None = None, source_reads: int = 1) -> dict[str, Any]:
    scan_public_input(public_input)
    history = history_from_public_input(public_input)
    if fixed_query is None:
        query = choose_query(public_input, history, mode=mode)
    else:
        score = _query_score(public_input, history, fixed_query, mode)
        query = {
            "selected_query": fixed_query,
            "minimizers": (fixed_query,),
            "query_scores": {fixed_query: score},
            "lexical_terminal_loss": score,
            "optimistic_terminal_loss": score,
            "pessimistic_terminal_loss": score,
        }
    return {
        "status": "OK",
        "arm_id": arm_id,
        "posterior_mode": mode,
        "public_input": copy.deepcopy(dict(public_input)),
        "source_table_read_count": source_reads,
        **query,
    }


def verify_scratch_source_isolation(public_input: Mapping[str, Any]) -> dict[str, Any]:
    scan_public_input(public_input)
    history = history_from_public_input(public_input)
    guarded = _InferenceSourceGuard(public_input)
    posterior = _posterior(guarded, history, "scratch")
    query = choose_query(guarded, history, mode="scratch")
    if guarded.source_access_count != 0:
        raise InferenceSourceAccessError("scratch inferential source access was not zero")
    positive_control_detected = False
    try:
        _ = guarded["source_truth_table"]
    except InferenceSourceAccessError:
        positive_control_detected = True
    return {
        "schema_validation_source_read_allowed": True,
        "inference_source_access_count": 0,
        "positive_control_detected": positive_control_detected,
        "posterior_total_weight": posterior["posterior_total_weight"],
        "selected_query": query["selected_query"],
    }


def hard_family_tie_audit(public_input: Mapping[str, Any]) -> dict[str, Any]:
    history = history_from_public_input(public_input)
    source_program = _infer_source_program(public_input["source_truth_table"])
    marginals = _family_marginals(source_program, history)
    maximum = max(marginals.values())
    tied = tuple(family for family in FAMILY_ORDER if marginals[family] == maximum)
    mode_by_family = {"SCRATCH": "scratch", "EXACT_SOURCE": "exact", "LOCAL_SHIFT": "local"}
    branches = {
        family: public_state_signature(_record_for_mode(
            f"HARD_FAMILY_BRANCH_{family}", public_input, mode_by_family[family],
            source_reads=int(family != "SCRATCH"),
        ))
        for family in tied
    }
    return {
        "family_marginals": marginals,
        "tied_families": tied,
        "lexical_family": tied[0],
        "branch_public_state_signatures": branches,
        "control_match_reducer": "reduce_hard_family_tie_sensitivity",
    }


def reduce_hard_family_tie_sensitivity(
    tied_families: Sequence[str], branch_control_match: Mapping[str, bool],
) -> dict[str, Any]:
    tied = tuple(tied_families)
    if not tied or any(family not in FAMILY_ORDER for family in tied):
        raise ArtifactValidationError("invalid tied-family set")
    normative = tuple(family for family in FAMILY_ORDER if family in tied)
    if tied != normative or set(branch_control_match) != set(tied):
        raise ArtifactValidationError("hard-family tie branch coverage/order mismatch")
    if any(not isinstance(value, bool) for value in branch_control_match.values()):
        raise ArtifactValidationError("control-match branch values must be bool")
    lexical_match = branch_control_match[tied[0]]
    invariant = all(value == lexical_match for value in branch_control_match.values())
    return {
        "lexical_family": tied[0],
        "lexical_control_match": lexical_match,
        "all_tied_branch_control_match_equal": invariant,
        "instrument_invalid": not invariant,
    }


def shortcut_prediction(
    shortcut_id: str, public_input: Mapping[str, Any],
    history: Sequence[tuple[str, int]], composition: str,
) -> Fraction:
    if composition not in COMPOSITIONS:
        raise ValueError("invalid shortcut composition")
    observed = dict(history)
    if composition in observed:
        return Fraction(observed[composition], 1)
    if shortcut_id == "OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN":
        source = dict(_canonical_rows(public_input["source_truth_table"], complete=True))
        return Fraction(source[composition], 1)
    if shortcut_id == "COUNT_TABLE_TARGET_MEAN":
        return Fraction(sum(observed.values()), len(observed)) if observed else Fraction(1, 2)
    if shortcut_id in {"GRAPH_LOOKUP_MIN_HAMMING_MEAN", "EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY"}:
        def distance(left: str, right: str) -> int:
            return sum(a != b for a, b in zip(left, right))
        minimum = min(distance(composition, node) for node in observed)
        nearest = sorted(node for node in observed if distance(composition, node) == minimum)
        if shortcut_id == "GRAPH_LOOKUP_MIN_HAMMING_MEAN":
            return Fraction(sum(observed[node] for node in nearest), len(nearest))
        return Fraction(observed[nearest[0]], 1)
    raise ValueError(f"not a public-history shortcut: {shortcut_id}")


def shortcut_fixed_query_endpoint(
    shortcut_id: str, public_input: Mapping[str, Any], *, fixed_query: str,
    query_outcome: int,
) -> dict[str, Any]:
    history = history_from_public_input(public_input)
    if fixed_query not in SECOND_QUERY_CANDIDATES or fixed_query in dict(history):
        raise ValueError("invalid fixed shortcut query")
    if query_outcome not in (0, 1):
        raise ValueError("query outcome must be binary")
    updated = tuple(history) + ((fixed_query, query_outcome),)
    predictions = {
        composition: shortcut_prediction(shortcut_id, public_input, updated, composition)
        for composition in COMPOSITIONS if composition not in dict(updated)
    }
    return {
        "shortcut_id": shortcut_id,
        "fixed_query": fixed_query,
        "query_outcome": query_outcome,
        "history": updated,
        "predictions": predictions,
    }


def _shortcut_record(arm_id: str, public_input: Mapping[str, Any]) -> dict[str, Any]:
    history = history_from_public_input(public_input)
    scores: dict[str, Fraction] = {}
    for query in SECOND_QUERY_CANDIDATES:
        probability_one = shortcut_prediction(arm_id, public_input, history, query)
        expected = Fraction(0, 1)
        for outcome, probability in ((0, 1 - probability_one), (1, probability_one)):
            if probability == 0:
                continue
            endpoint = shortcut_fixed_query_endpoint(arm_id, public_input, fixed_query=query, query_outcome=outcome)
            self_risk = sum((prediction * (1 - prediction) for prediction in endpoint["predictions"].values()), Fraction(0, 1))
            expected += probability * self_risk
        scores[query] = expected
    minimum = min(scores.values())
    minimizers = tuple(query for query in SECOND_QUERY_CANDIDATES if scores[query] == minimum)
    selected = minimizers[0]
    return {
        "status": "OK", "arm_id": arm_id, "posterior_mode": "public_history_shortcut",
        "public_input": copy.deepcopy(dict(public_input)),
        "source_table_read_count": int(arm_id == "OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN"),
        "selected_query": selected, "minimizers": minimizers, "query_scores": scores,
        "lexical_terminal_loss": scores[selected],
        "optimistic_terminal_loss": min(scores[q] for q in minimizers),
        "pessimistic_terminal_loss": max(scores[q] for q in minimizers),
        "formal_selection_scope": "future_population_global_fixed_query_envelope_not_adjudicated_in_I1",
    }


_CANDIDATE_LOOKUP_TABLE: dict[str, dict[str, Any]] | None = None
_CANDIDATE_LOOKUP_RECEIPT: dict[str, Any] | None = None


def _input_signature(public_input: Mapping[str, Any]) -> str:
    payload = fraction_jsonify({
        "source_truth_table": public_input["source_truth_table"],
        "target_history": public_input["target_history"],
        "query_count": public_input["query_count"],
        "query_budget": public_input["query_budget"],
    })
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _candidate_lookup_key(operation: str, public_input: Mapping[str, Any]) -> str:
    if operation not in {"QUERY", "PREDICT"}:
        raise ValueError("invalid lookup operation")
    return f"{operation}:{_input_signature(public_input)}"


def materialize_candidate_rule_lookup() -> dict[str, Any]:
    global _CANDIDATE_LOOKUP_TABLE, _CANDIDATE_LOOKUP_RECEIPT
    if _CANDIDATE_LOOKUP_TABLE is not None and _CANDIDATE_LOOKUP_RECEIPT is not None:
        return copy.deepcopy(_CANDIDATE_LOOKUP_RECEIPT)
    table: dict[str, dict[str, Any]] = {}
    query_state_count = 0
    prediction_state_count = 0
    for source_program in range(128):
        source_table = build_source_truth_table(source_program)
        for first_outcome in (0, 1):
            h1_input = build_public_input(
                source_table=source_table,
                target_history=[{"composition": "000", "outcome": first_outcome}],
                query_budget=1,
                arm_id="MIXTURE_BMA_ACTIVE_BRIER",
                serialized_state={"schema": "caot_bool_v2_stateless_v1"},
            )
            query_record = _record_for_mode("MIXTURE_BMA_ACTIVE_BRIER", h1_input, "primary")
            table[_candidate_lookup_key("QUERY", h1_input)] = {
                "operation": "QUERY",
                "behavior": {field: copy.deepcopy(query_record[field]) for field in (
                    "selected_query", "minimizers", "query_scores",
                    "lexical_terminal_loss", "optimistic_terminal_loss",
                    "pessimistic_terminal_loss",
                )},
            }
            query_state_count += 1
            for query in SECOND_QUERY_CANDIDATES:
                for query_outcome in (0, 1):
                    h2_input = build_public_input(
                        source_table=source_table,
                        target_history=[
                            {"composition": "000", "outcome": first_outcome},
                            {"composition": query, "outcome": query_outcome},
                        ],
                        query_budget=1,
                        arm_id="MIXTURE_BMA_ACTIVE_BRIER",
                        serialized_state={"schema": "caot_bool_v2_stateless_v1"},
                    )
                    h2_history = history_from_public_input(h2_input)
                    posterior = _posterior(h2_input, h2_history, "primary")
                    predictions = {
                        composition: predictive_probability(posterior, composition)
                        for composition in COMPOSITIONS if composition not in dict(h2_history)
                    }
                    table[_candidate_lookup_key("PREDICT", h2_input)] = {
                        "operation": "PREDICT",
                        "predictions": predictions,
                    }
                    prediction_state_count += 1
    canonical = json.dumps(fraction_jsonify(table), sort_keys=True, separators=(",", ":")).encode("utf-8")
    _CANDIDATE_LOOKUP_TABLE = table
    _CANDIDATE_LOOKUP_RECEIPT = {
        "state_count": len(table),
        "query_state_count": query_state_count,
        "prediction_state_count": prediction_state_count,
        "expected_state_count": 3840,
        "complete": len(table) == 3840 and query_state_count == 256 and prediction_state_count == 3584,
        "table_sha256": hashlib.sha256(canonical).hexdigest(),
        "retrieval_calls_primary": False,
    }
    if not _CANDIDATE_LOOKUP_RECEIPT["complete"]:
        raise DesignValidationError(f"candidate lookup public-state domain incomplete: {_CANDIDATE_LOOKUP_RECEIPT}")
    return copy.deepcopy(_CANDIDATE_LOOKUP_RECEIPT)


def candidate_lookup_predictions(public_input: Mapping[str, Any]) -> dict[str, Fraction]:
    receipt = materialize_candidate_rule_lookup()
    del receipt
    assert _CANDIDATE_LOOKUP_TABLE is not None
    entry = _CANDIDATE_LOOKUP_TABLE.get(_candidate_lookup_key("PREDICT", public_input))
    if entry is None or entry.get("operation") != "PREDICT":
        raise DesignValidationError("prediction public state absent from materialized lookup")
    return copy.deepcopy(entry["predictions"])


def run_arm(arm_id: str, public_input: Mapping[str, Any]) -> dict[str, Any]:
    scan_public_input(public_input)
    if arm_id == "MIXTURE_BMA_ACTIVE_BRIER":
        return _record_for_mode(arm_id, public_input, "primary")
    if arm_id == "SCRATCH_SPIKE_SLAB_ACTIVE_BAYES":
        record = _record_for_mode(arm_id, public_input, "scratch", source_reads=0)
        record["source_access_receipt"] = verify_scratch_source_isolation(public_input)
        return record
    mode_map = {
        "EXACT_SOURCE_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK": "exact",
        "LOCAL_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK": "local",
        "SOURCE_CONSISTENCY_WITH_SCRATCH_FALLBACK": "source_consistency",
        "MARGINAL_MDL_MAP_HARD_FAMILY": "hard_family",
        "MINIMUM_HAMMING_NEAREST_SOURCE": "nearest",
    }
    if arm_id in mode_map:
        record = _record_for_mode(arm_id, public_input, mode_map[arm_id])
        if arm_id == "MARGINAL_MDL_MAP_HARD_FAMILY":
            record["hard_family_tie_audit"] = hard_family_tie_audit(public_input)
        return record
    if arm_id.startswith("FIXED_QUERY_"):
        query = arm_id.removeprefix("FIXED_QUERY_")
        return _record_for_mode(arm_id, public_input, "primary", fixed_query=query)
    if arm_id == "PASSIVE_LEXICAL":
        return _record_for_mode(arm_id, public_input, "primary", fixed_query="001")
    if arm_id == "UNIFORM_FIXED_QUERY_MIXTURE":
        records = [_record_for_mode(f"FIXED_QUERY_{q}", public_input, "primary", fixed_query=q) for q in SECOND_QUERY_CANDIDATES]
        mean = sum((record["lexical_terminal_loss"] for record in records), Fraction(0, 1)) / len(records)
        result = copy.deepcopy(records[0])
        result.update({"arm_id": arm_id, "selected_query": "UNIFORM_MIXTURE", "minimizers": tuple(SECOND_QUERY_CANDIDATES), "lexical_terminal_loss": mean, "optimistic_terminal_loss": min(r["lexical_terminal_loss"] for r in records), "pessimistic_terminal_loss": max(r["lexical_terminal_loss"] for r in records)})
        return result
    if arm_id in {
        "OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN",
        "COUNT_TABLE_TARGET_MEAN", "GRAPH_LOOKUP_MIN_HAMMING_MEAN",
        "EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY",
    }:
        return _shortcut_record(arm_id, public_input)
    if arm_id == "CANDIDATE_RULE_AMORTIZED_LOOKUP":
        receipt = materialize_candidate_rule_lookup()
        assert _CANDIDATE_LOOKUP_TABLE is not None
        key = _candidate_lookup_key("QUERY", public_input)
        entry = _CANDIDATE_LOOKUP_TABLE.get(key)
        if entry is None or entry.get("operation") != "QUERY":
            raise DesignValidationError("query public state absent from materialized lookup")
        return {
            "status": "OK", "arm_id": arm_id, "posterior_mode": "materialized_lookup",
            "public_input": copy.deepcopy(dict(public_input)), "source_table_read_count": 0,
            "lookup_key": key, "lookup_table_sha256": receipt["table_sha256"],
            **copy.deepcopy(entry["behavior"]),
        }
    if arm_id in {"TRANSITION_TABLE", "SUCCESSOR_MAP", "FSM_PLANNER"}:
        return {"status": "NOT_APPLICABLE", "arm_id": arm_id, "schema_witness": "no_public_transition_successor_or_reward_field"}
    raise ValueError(f"unregistered arm: {arm_id}")


def _swap_x1_x2(composition: str) -> str:
    return composition[1] + composition[0] + composition[2]


def _relabel_public_input(public_input: Mapping[str, Any]) -> dict[str, Any]:
    transformed = copy.deepcopy(dict(public_input))
    for row in transformed["source_truth_table"]:
        row["composition"] = _swap_x1_x2(row["composition"])
    for row in transformed["target_history"]:
        row["composition"] = _swap_x1_x2(row["composition"])
    return transformed


def _unrelabel_record(record: dict[str, Any], original_input: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    if result.get("selected_query") in COMPOSITIONS:
        result["selected_query"] = _swap_x1_x2(result["selected_query"])
    result["minimizers"] = tuple(sorted(_swap_x1_x2(q) if q in COMPOSITIONS else q for q in result.get("minimizers", ())))
    if "query_scores" in result:
        result["query_scores"] = {_swap_x1_x2(q) if q in COMPOSITIONS else q: value for q, value in result["query_scores"].items()}
    result["public_input"] = copy.deepcopy(dict(original_input))
    return result


def run_ablation(ablation_id: str, public_input: Mapping[str, Any]) -> dict[str, Any]:
    if ablation_id not in ABLATION_REGISTRY:
        raise ValueError(f"unregistered ablation: {ablation_id}")
    if ablation_id == "SOURCE_DELETE":
        return {"status": "OK", "ablation_id": ablation_id, "result": run_arm("SCRATCH_SPIKE_SLAB_ACTIVE_BAYES", public_input)}
    if ablation_id == "LOCAL_DELETE":
        return {"status": "OK", "ablation_id": ablation_id, "result": _record_for_mode(ablation_id, public_input, "local_delete")}
    if ablation_id == "FEEDBACK_MASK":
        primary = run_arm("MIXTURE_BMA_ACTIVE_BRIER", public_input)
        history = history_from_public_input(public_input)
        posterior_h1 = _posterior(public_input, history, "primary")
        query = primary["selected_query"]
        remaining = [composition for composition in COMPOSITIONS if composition not in {*dict(history), query}]
        masked_predictions = {
            composition: predictive_probability(posterior_h1, composition)
            for composition in remaining
        }
        masked = copy.deepcopy(primary)
        masked.update({
            "feedback_used": False,
            "masked_history": history,
            "masked_predictions_by_query_outcome": {
                "0": copy.deepcopy(masked_predictions),
                "1": copy.deepcopy(masked_predictions),
            },
            "mask_semantics": "same_H1_query_second_outcome_not_added_to_posterior",
        })
        return {"status": "OK", "ablation_id": ablation_id, "result": masked}
    if ablation_id == "ACTIVE_DELETE":
        return {"status": "OK", "ablation_id": ablation_id, "result": run_arm("UNIFORM_FIXED_QUERY_MIXTURE", public_input)}
    if ablation_id == "UNIFORM_SCRATCH_PRIOR":
        return {"status": "OK", "ablation_id": ablation_id, "result": _record_for_mode(ablation_id, public_input, "uniform_scratch_primary")}
    if ablation_id == "SOURCE_TABLE_ROW_PERMUTE":
        transformed = copy.deepcopy(dict(public_input))
        transformed["source_truth_table"] = list(reversed(transformed["source_truth_table"]))
        return {"status": "OK", "ablation_id": ablation_id, "result": run_arm("MIXTURE_BMA_ACTIVE_BRIER", transformed)}
    if ablation_id == "VARIABLE_RELABEL":
        transformed = _relabel_public_input(public_input)
        record = run_arm("MIXTURE_BMA_ACTIVE_BRIER", transformed)
        return {"status": "OK", "ablation_id": ablation_id, "result": _unrelabel_record(record, public_input)}
    if ablation_id in {"SERIALIZED_STATE_RESET", "SERIALIZED_STATE_SWAP"}:
        baseline = run_arm("MIXTURE_BMA_ACTIVE_BRIER", public_input)
        transformed = copy.deepcopy(dict(public_input))
        original = json.dumps(transformed["serialized_state"], sort_keys=True)
        transformed["serialized_state"] = {} if ablation_id.endswith("RESET") else {"swapped": "bounded-fixture"}
        changed = json.dumps(transformed["serialized_state"], sort_keys=True) != original
        ablated = run_arm("MIXTURE_BMA_ACTIVE_BRIER", transformed)
        behavior_changed = public_state_signature(baseline) != public_state_signature(ablated)
        return {
            "status": "OK", "ablation_id": ablation_id,
            "state_bytes_changed": changed,
            "behavior_changed": behavior_changed,
            "state_dependency_detected": behavior_changed,
            "reference_state_semantics": "stateless_exact_reference_serialized_state_is_not_an_inference_input",
            "claim_ceiling": "state_mutation_test_only_no_state_history_dependence_claim",
            "baseline_result": baseline,
            "result": ablated,
        }
    planted = copy.deepcopy(dict(public_input))
    if ablation_id == "HIDDEN_COEFFICIENT_POSITIVE_CONTROL":
        planted["source_coefficients"] = [0] * 7
    else:
        planted["relation"] = "EXACT"
    try:
        scan_public_input(planted)
    except PrivateTruthLeakageError:
        return {"status": "REJECTED_PRIVATE_TRUTH", "ablation_id": ablation_id}
    raise PrivateTruthLeakageError("positive control escaped leakage scanner")


def public_state_signature(record: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "selected_query", "minimizers", "query_scores", "lexical_terminal_loss",
        "optimistic_terminal_loss", "pessimistic_terminal_loss",
    )
    return fraction_jsonify({field: record[field] for field in fields if field in record})


def population_summary() -> dict[str, Any]:
    return {
        "source_program_count": 128,
        "target_program_count": 128,
        "pair_count_per_arm": 16384,
        "stratum_counts": {"EXACT": 128, "LOCAL": 768, "NONLOCAL": 15488},
    }


def classify_pair(source_program: int, target_program: int) -> str:
    program_bits(source_program)
    program_bits(target_program)
    if source_program == target_program:
        return "EXACT"
    source = program_bits(source_program)
    target = program_bits(target_program)
    if source[0] == target[0] and sum(a != b for a, b in zip(source[1:], target[1:])) == 1:
        return "LOCAL"
    return "NONLOCAL"


def _realized_endpoint_loss(
    public_input: Mapping[str, Any], target_program: int, *, query: str, mode: str,
) -> Fraction:
    history = history_from_public_input(public_input)
    outcome = _program_outcome(target_program, query)
    updated = tuple(history) + ((query, outcome),)
    posterior = _posterior(public_input, updated, mode)
    remaining = [composition for composition in COMPOSITIONS if composition not in dict(updated)]
    total = Fraction(0, 1)
    for composition in remaining:
        prediction = predictive_probability(posterior, composition)
        truth = _program_outcome(target_program, composition)
        total += (prediction - truth) ** 2
    return total / len(remaining)


def _realized_endpoint_payload(
    public_input: Mapping[str, Any], target_program: int, *, query: str, mode: str,
) -> dict[str, Any]:
    history = history_from_public_input(public_input)
    updated = tuple(history) + ((query, _program_outcome(target_program, query)),)
    posterior = _posterior(public_input, updated, mode)
    predictions = {
        composition: predictive_probability(posterior, composition)
        for composition in COMPOSITIONS if composition not in dict(updated)
    }
    truth = {composition: _program_outcome(target_program, composition) for composition in predictions}
    loss = sum((predictions[composition] - truth[composition]) ** 2 for composition in predictions) / len(predictions)
    return {"query": query, "predictions": predictions, "truth": truth, "loss": loss}


def evaluate_pair(source_program: int, target_program: int, *, arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER") -> dict[str, Any]:
    source_table = build_source_truth_table(source_program)
    target_history = [{"composition": "000", "outcome": _program_outcome(target_program, "000")}]
    public_input = build_public_input(
        source_table=source_table, target_history=target_history, query_budget=1,
        arm_id=arm_id, serialized_state={"schema": "caot_bool_v2_stateless_v1"},
    )
    record = run_arm(arm_id, public_input)
    if record.get("status") != "OK":
        return {
            "source_program": source_program, "target_program": target_program,
            "stratum": classify_pair(source_program, target_program),
            "arm_id": arm_id, "status": record.get("status"), "producer_function": "evaluate_pair",
        }
    if arm_id in {
        "OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN",
        "COUNT_TABLE_TARGET_MEAN", "GRAPH_LOOKUP_MIN_HAMMING_MEAN",
        "EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY",
    }:
        losses: dict[str, Fraction] = {}
        for query in SECOND_QUERY_CANDIDATES:
            endpoint = shortcut_fixed_query_endpoint(
                arm_id, public_input, fixed_query=query,
                query_outcome=_program_outcome(target_program, query),
            )
            losses[query] = sum(
                (prediction - _program_outcome(target_program, composition)) ** 2
                for composition, prediction in endpoint["predictions"].items()
            ) / len(endpoint["predictions"])
        return {
            "source_program": source_program, "target_program": target_program,
            "stratum": classify_pair(source_program, target_program), "arm_id": arm_id,
            "status": "OK", "producer_function": "evaluate_pair", "fixed_query_losses": losses,
            "selection_scope": "global_population_envelope_required",
        }
    if arm_id == "UNIFORM_FIXED_QUERY_MIXTURE":
        losses = {query: _realized_endpoint_loss(public_input, target_program, query=query, mode="primary") for query in SECOND_QUERY_CANDIDATES}
        mean = sum(losses.values(), Fraction(0, 1)) / len(losses)
        return {
            "source_program": source_program, "target_program": target_program,
            "stratum": classify_pair(source_program, target_program), "arm_id": arm_id,
            "status": "OK", "producer_function": "evaluate_pair", "fixed_query_losses": losses,
            "lexical_loss": mean, "optimistic_loss": mean, "pessimistic_loss": mean,
        }
    mode = record["posterior_mode"]
    minimizers = tuple(record["minimizers"])
    endpoints = {query: _realized_endpoint_payload(public_input, target_program, query=query, mode=mode) for query in minimizers}
    losses = {query: endpoint["loss"] for query, endpoint in endpoints.items()}
    selected_endpoint = endpoints[record["selected_query"]]
    return {
        "source_program": source_program, "target_program": target_program,
        "stratum": classify_pair(source_program, target_program), "arm_id": arm_id,
        "status": "OK", "producer_function": "evaluate_pair", "selected_query": record["selected_query"],
        "minimizers": minimizers, "minimizer_losses": losses,
        "minimizer_endpoints": endpoints,
        "selected_predictions": selected_endpoint["predictions"],
        "selected_truth": selected_endpoint["truth"],
        "lexical_loss": losses[record["selected_query"]],
        "optimistic_loss": min(losses.values()),
        "pessimistic_loss": max(losses.values()),
    }


def evaluate_feedback_mask_pair(source_program: int, target_program: int) -> dict[str, Any]:
    source_table = build_source_truth_table(source_program)
    public_input = build_public_input(
        source_table=source_table,
        target_history=[{"composition": "000", "outcome": _program_outcome(target_program, "000")}],
        query_budget=1,
        arm_id="FEEDBACK_MASK",
        serialized_state={"schema": "caot_bool_v2_stateless_v1"},
    )
    history = history_from_public_input(public_input)
    query_receipt = choose_query(public_input, history, mode="primary")
    primary_query = query_receipt["selected_query"]
    posterior_h1 = _posterior(public_input, history, "primary")
    predictions = {
        composition: predictive_probability(posterior_h1, composition)
        for composition in COMPOSITIONS if composition not in {*dict(history), primary_query}
    }
    truth = {composition: _program_outcome(target_program, composition) for composition in predictions}
    loss = sum((predictions[composition] - truth[composition]) ** 2 for composition in predictions) / len(predictions)
    return {
        "source_program": source_program,
        "target_program": target_program,
        "stratum": classify_pair(source_program, target_program),
        "status": "OK",
        "arm_id": "FEEDBACK_MASK",
        "ablation_id": "FEEDBACK_MASK",
        "selected_query": primary_query,
        "minimizers": tuple(query_receipt["minimizers"]),
        "masked_query_outcome": _program_outcome(target_program, primary_query),
        "masked_history": history,
        "selected_predictions": predictions,
        "selected_truth": truth,
        "lexical_loss": loss,
        "feedback_used": False,
    }


def replay_pair(record: Mapping[str, Any]) -> dict[str, Any]:
    if record.get("status") != "OK" or record.get("arm_id") != "MIXTURE_BMA_ACTIVE_BRIER":
        raise ArtifactValidationError("fresh replay source row status/arm mismatch")
    source = record.get("source_program")
    target = record.get("target_program")
    if not isinstance(source, int) or not isinstance(target, int):
        raise ArtifactValidationError("fresh replay source row lacks pair IDs")
    replayed = evaluate_pair(source, target, arm_id="MIXTURE_BMA_ACTIVE_BRIER")
    replayed["producer_function"] = "replay_pair"
    return replayed


def evaluate_all_fixed_queries(source_program: int, target_program: int, *, mode: str = "primary") -> dict[str, Any]:
    if mode not in {"primary", "scratch"}:
        raise ValueError("fixed-query panel supports primary or scratch")
    public_input = build_public_input(
        source_table=build_source_truth_table(source_program),
        target_history=[{"composition": "000", "outcome": _program_outcome(target_program, "000")}],
        query_budget=1,
        arm_id=f"FIXED_QUERY_PANEL_{mode.upper()}",
        serialized_state={"schema": "caot_bool_v2_stateless_v1"},
    )
    endpoints = {
        query: _realized_endpoint_payload(public_input, target_program, query=query, mode=mode)
        for query in SECOND_QUERY_CANDIDATES
    }
    return {
        "source_program": source_program,
        "target_program": target_program,
        "stratum": classify_pair(source_program, target_program),
        "status": "OK",
        "arm_id": f"FIXED_QUERY_PANEL_{mode.upper()}",
        "fixed_query_losses": {query: endpoint["loss"] for query, endpoint in endpoints.items()},
        "fixed_query_endpoints": endpoints,
    }


def evaluate_ablation_pair(source_program: int, target_program: int, *, ablation_id: str) -> dict[str, Any]:
    if ablation_id == "SOURCE_DELETE":
        result = evaluate_pair(source_program, target_program, arm_id="SCRATCH_SPIKE_SLAB_ACTIVE_BAYES")
        return {**result, "arm_id": "SOURCE_DELETE", "ablation_id": "SOURCE_DELETE"}
    if ablation_id == "FEEDBACK_MASK":
        return evaluate_feedback_mask_pair(source_program, target_program)
    if ablation_id == "ACTIVE_DELETE":
        result = evaluate_pair(source_program, target_program, arm_id="UNIFORM_FIXED_QUERY_MIXTURE")
        return {**result, "arm_id": "ACTIVE_DELETE", "ablation_id": "ACTIVE_DELETE"}
    if ablation_id != "LOCAL_DELETE":
        raise ValueError(f"population pair evaluator unavailable for ablation: {ablation_id}")
    public_input = build_public_input(
        source_table=build_source_truth_table(source_program),
        target_history=[{"composition": "000", "outcome": _program_outcome(target_program, "000")}],
        query_budget=1,
        arm_id="LOCAL_DELETE",
        serialized_state={"schema": "caot_bool_v2_stateless_v1"},
    )
    record = _record_for_mode("LOCAL_DELETE", public_input, "local_delete")
    minimizers = tuple(record["minimizers"])
    endpoints = {
        query: _realized_endpoint_payload(public_input, target_program, query=query, mode="local_delete")
        for query in minimizers
    }
    losses = {query: endpoint["loss"] for query, endpoint in endpoints.items()}
    selected_endpoint = endpoints[record["selected_query"]]
    return {
        "source_program": source_program,
        "target_program": target_program,
        "stratum": classify_pair(source_program, target_program),
        "status": "OK",
        "arm_id": "LOCAL_DELETE",
        "ablation_id": "LOCAL_DELETE",
        "selected_query": record["selected_query"],
        "minimizers": minimizers,
        "minimizer_losses": losses,
        "minimizer_endpoints": endpoints,
        "selected_predictions": selected_endpoint["predictions"],
        "selected_truth": selected_endpoint["truth"],
        "lexical_loss": losses[record["selected_query"]],
        "optimistic_loss": min(losses.values()),
        "pessimistic_loss": max(losses.values()),
    }
def common_unqueried_gain(candidate_pair: Mapping[str, Any], comparator_pair: Mapping[str, Any]) -> dict[str, Any]:
    candidate_predictions = candidate_pair.get("selected_predictions")
    comparator_predictions = comparator_pair.get("selected_predictions")
    candidate_truth = candidate_pair.get("selected_truth")
    comparator_truth = comparator_pair.get("selected_truth")
    if not all(isinstance(value, Mapping) for value in (candidate_predictions, comparator_predictions, candidate_truth, comparator_truth)):
        raise ArtifactValidationError("pair records lack selected endpoint predictions")
    common = tuple(sorted(set(candidate_predictions).intersection(comparator_predictions)))
    if not common or any(candidate_truth[node] != comparator_truth[node] for node in common):
        raise ArtifactValidationError("common-unqueried truth mismatch")
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
    excluded = {source_program, *local_neighbors(source_program)}
    raw = {target: scratch_prior_mass(target) for target in range(128) if target not in excluded}
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
        raise ArtifactValidationError("complete population requires exactly 16,384 rows")
    by_pair: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in rows:
        if row.get("status") != "OK" or row.get("arm_id") != expected_arm_id:
            raise ArtifactValidationError("population row status/arm mismatch")
        source = row.get("source_program")
        target = row.get("target_program")
        if not isinstance(source, int) or not isinstance(target, int):
            raise ArtifactValidationError("row lacks verifier-only pair IDs")
        key = (source, target)
        if key in by_pair:
            raise ArtifactValidationError("duplicate source-target pair")
        if row.get("stratum") != classify_pair(source, target):
            raise ArtifactValidationError("stratum mismatch")
        if not isinstance(row.get(loss_field), Fraction) or row[loss_field] < 0:
            raise ArtifactValidationError("loss must be an exact nonnegative Fraction")
        by_pair[key] = row
    expected = {(source, target) for source in range(128) for target in range(128)}
    if set(by_pair) != expected:
        raise ArtifactValidationError("population pair coverage mismatch")
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
        raise ArtifactValidationError("relative metric baseline denominator must be positive")
    return (baseline - candidate) / baseline


def weighted_tail_disclosures(weighted_regrets: Sequence[tuple[Fraction, Fraction]]) -> dict[str, Fraction]:
    if not weighted_regrets or any(weight < 0 for _, weight in weighted_regrets):
        raise ArtifactValidationError("invalid weighted regret population")
    total_weight = sum((weight for _, weight in weighted_regrets), Fraction(0, 1))
    if total_weight != 1:
        raise ArtifactValidationError("tail weights must normalize to one")
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
        raise ArtifactValidationError("insufficient mass for worst-10-percent CVaR")
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
        raise ArtifactValidationError("risk summary schema mismatch")
    return {
        "nominal_relative_gain": relative_improvement(candidate_risks["NOMINAL"], baseline_risks["NOMINAL"]),
        "exact_relative_gain": relative_improvement(candidate_risks["EXACT"], baseline_risks["EXACT"]),
        "local_relative_gain": relative_improvement(candidate_risks["LOCAL"], baseline_risks["LOCAL"]),
        "nonlocal_relative_regret": -relative_improvement(candidate_risks["NONLOCAL"], baseline_risks["NONLOCAL"]),
        "scratch_heavy_relative_gain": relative_improvement(candidate_risks["SCRATCH_HEAVY"], baseline_risks["SCRATCH_HEAVY"]),
    }


def _evidence_sha256(value: Any) -> str:
    canonical = json.dumps(fraction_jsonify(value), sort_keys=True, separators=(",", ":"))
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
        "code_path_hash": compute_sha256(Path(__file__)),
        "aggregation_rule": _EVIDENCE_AGGREGATION_RULES[producer_function],
        "input_sources": tuple(input_sources),
        "coverage": copy.deepcopy(dict(coverage)),
        **copy.deepcopy(dict(payload)),
    }
    schema = _EVIDENCE_SCHEMAS.get(producer_function)
    if schema is None or set(coverage) != schema["coverage"] or set(payload) != schema["payload"]:
        raise ArtifactValidationError("evidence receipt producer schema mismatch")
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
        raise ArtifactValidationError("gate receipt status is not OK")
    if receipt.get("producer_function") != producer_function:
        raise ArtifactValidationError("gate receipt producer mismatch")
    if receipt.get("run_id") != EVIDENCE_RUN_ID:
        raise ArtifactValidationError("gate receipt run_id mismatch")
    if receipt.get("code_path_hash") != (expected_code_path_hash or compute_sha256(Path(__file__))):
        raise ArtifactValidationError("gate receipt code path hash mismatch")
    if receipt.get("aggregation_rule") != _EVIDENCE_AGGREGATION_RULES.get(producer_function):
        raise ArtifactValidationError("gate receipt aggregation rule mismatch")
    if input_sources is not None and tuple(receipt.get("input_sources", ())) != tuple(input_sources):
        raise ArtifactValidationError("gate receipt input source mismatch")
    supplied = receipt.get("receipt_sha256")
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise ArtifactValidationError("gate receipt hash missing")
    unhashed = dict(receipt)
    unhashed.pop("receipt_sha256", None)
    if supplied != _evidence_sha256(unhashed):
        raise ArtifactValidationError("gate receipt hash mismatch")
    schema = _EVIDENCE_SCHEMAS.get(producer_function)
    coverage = receipt.get("coverage")
    if schema is None or not isinstance(coverage, Mapping):
        raise ArtifactValidationError("gate receipt producer schema missing")
    if set(coverage) != schema["coverage"] or set(receipt) - _EVIDENCE_BASE_FIELDS != schema["payload"]:
        raise ArtifactValidationError("gate receipt producer schema mismatch")


def _population_rows_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        encoded = json.dumps(fraction_jsonify(row), sort_keys=True, separators=(",", ":")).encode("utf-8")
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
        raise ArtifactValidationError("unregistered query-tie loss field")
    candidate_by_pair = {(row.get("source_program"), row.get("target_program")): row for row in candidate_rows}
    scratch_by_pair = {(row.get("source_program"), row.get("target_program")): row for row in scratch_rows}
    if len(candidate_by_pair) != len(candidate_rows) or set(candidate_by_pair) != set(scratch_by_pair):
        raise ArtifactValidationError("candidate/scratch pair alignment mismatch")
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
        raise ArtifactValidationError("global fixed-query envelope requires complete rows")
    expected_pairs = {(source, target) for source in range(128) for target in range(128)}
    observed_pairs: set[tuple[int, int]] = set()
    for row in rows:
        if row.get("status") != "OK" or row.get("arm_id") != "FIXED_QUERY_PANEL_PRIMARY":
            raise ArtifactValidationError("fixed-query panel row status/arm mismatch")
        source = row.get("source_program")
        target = row.get("target_program")
        if not isinstance(source, int) or not isinstance(target, int):
            raise ArtifactValidationError("fixed-query panel row lacks pair IDs")
        pair = (source, target)
        if pair in observed_pairs or row.get("stratum") != classify_pair(source, target):
            raise ArtifactValidationError("fixed-query panel pair coverage/stratum mismatch")
        observed_pairs.add(pair)
        losses = row.get("fixed_query_losses")
        endpoints = row.get("fixed_query_endpoints")
        if not isinstance(losses, Mapping) or set(losses) != set(SECOND_QUERY_CANDIDATES):
            raise ArtifactValidationError("fixed-query loss panel mismatch")
        if not isinstance(endpoints, Mapping) or set(endpoints) != set(SECOND_QUERY_CANDIDATES):
            raise ArtifactValidationError("fixed-query endpoint panel mismatch")
        if any(not isinstance(losses[query], Fraction) or losses[query] < 0 for query in SECOND_QUERY_CANDIDATES):
            raise ArtifactValidationError("fixed-query loss must be an exact nonnegative Fraction")
    if observed_pairs != expected_pairs:
        raise ArtifactValidationError("fixed-query panel pair coverage mismatch")
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
        raise ArtifactValidationError("unregistered active query-tie loss field")
    if len(candidate_rows) != 16384 or len(fixed_query_panel_rows) != 16384:
        raise ArtifactValidationError("active-necessity reducer requires complete populations")
    candidate_by_pair = {(row["source_program"], row["target_program"]): row for row in candidate_rows}
    fixed_by_pair = {(row["source_program"], row["target_program"]): row for row in fixed_query_panel_rows}
    if len(candidate_by_pair) != 16384 or set(candidate_by_pair) != set(fixed_by_pair):
        raise ArtifactValidationError("active-necessity pair coverage mismatch")
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
        raise ArtifactValidationError("control Pareto endpoint missing")
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
        raise ArtifactValidationError("relative metric schema mismatch")
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
            raise ArtifactValidationError("ablation receipt arm/coverage mismatch")
    source_coverage = source_delete_reference_receipt["coverage"]
    local_coverage = local_delete_reference_receipt["coverage"]
    feedback_coverage = feedback_mask_active_receipt["coverage"]
    active_delete_coverage = active_delete_active_receipt["coverage"]
    if source_coverage.get("loss_field") != "lexical_loss" or local_coverage.get("loss_field") != "lexical_loss":
        raise ArtifactValidationError("ablation reference loss-field mismatch")
    if feedback_coverage.get("loss_field") != "lexical_loss" or active_delete_coverage.get("loss_field") != "lexical_loss":
        raise ArtifactValidationError("ablation active loss-field mismatch")
    if source_coverage["scratch_rows_sha256"] != local_coverage["scratch_rows_sha256"]:
        raise ArtifactValidationError("ablation scratch population lineage mismatch")
    if feedback_coverage["fixed_query_panel_rows_sha256"] != active_delete_coverage["fixed_query_panel_rows_sha256"]:
        raise ArtifactValidationError("ablation fixed-query population lineage mismatch")
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
            raise ArtifactValidationError("query-tie branch receipt phase mismatch")
    branch_kinds = tuple(receipt["coverage"].get("branch_kind") for receipt in branches)
    if branch_kinds != ("LEXICAL", "OPTIMISTIC", "PESSIMISTIC"):
        raise ArtifactValidationError("query-tie branch labels mismatch")
    branch_hashes = tuple(receipt["receipt_sha256"] for receipt in branches)
    if len(set(branch_hashes)) != 3:
        raise ArtifactValidationError("query-tie branch receipts must be distinct")
    verdicts = tuple(receipt["verdict"] for receipt in branches)
    if any(verdict not in VERDICT_PRIORITY for verdict in verdicts):
        raise ArtifactValidationError("unregistered query-tie verdict")
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
        raise ArtifactValidationError("control receipt set mismatch")
    sources = ("candidate_population_rows", "scratch_population_rows")
    _validate_evidence_receipt(candidate_reference_receipt, producer_function="reduce_reference_population", input_sources=sources)
    candidate_coverage = candidate_reference_receipt.get("coverage")
    if not isinstance(candidate_coverage, Mapping) or candidate_coverage.get("candidate_arm_id") != "MIXTURE_BMA_ACTIVE_BRIER" or candidate_coverage.get("candidate_row_count") != 16384:
        raise ArtifactValidationError("candidate control receipt coverage mismatch")
    if candidate_coverage.get("loss_field") not in {"lexical_loss", "optimistic_loss", "pessimistic_loss"}:
        raise ArtifactValidationError("candidate control receipt loss-field mismatch")
    for control_id, receipt in control_reference_receipts_by_id.items():
        _validate_evidence_receipt(receipt, producer_function="reduce_reference_population", input_sources=sources)
        coverage = receipt.get("coverage")
        if not isinstance(coverage, Mapping) or coverage.get("candidate_arm_id") != control_id or coverage.get("candidate_row_count") != 16384:
            raise ArtifactValidationError("control receipt arm/coverage mismatch")
        if coverage.get("loss_field") != candidate_coverage.get("loss_field") or coverage.get("scratch_rows_sha256") != candidate_coverage.get("scratch_rows_sha256"):
            raise ArtifactValidationError("control receipt scratch/loss lineage mismatch")
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
    return json.dumps(fraction_jsonify(row), sort_keys=True, separators=(",", ":")).encode("utf-8")


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
            raise ArtifactValidationError("population stream row schema/coverage mismatch")
        observed_pairs.add(pair)
    if any(row.get("producer_function") != expected_row_producer_function for row in rows):
        raise ArtifactValidationError("population stream row producer mismatch")
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


def _validated_case_pairs(case_pairs: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    pairs = tuple(case_pairs)
    for pair in pairs:
        if (
            not isinstance(pair, tuple) or len(pair) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 or value >= 128 for value in pair)
        ):
            raise ArtifactValidationError("population stream invalid case pair")
    if len(set(pairs)) != len(pairs):
        raise ArtifactValidationError("population stream duplicate case pair")
    return pairs


def produce_primary_population_stream(
    case_pairs: Sequence[tuple[int, int]], *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    pairs = _validated_case_pairs(case_pairs)
    rows = tuple(evaluate_pair(source, target, arm_id=expected_arm_id) for source, target in pairs)
    return _produce_population_stream_receipt(
        rows, producer_function="produce_primary_population_stream",
        input_source="case_pairs", expected_arm_id=expected_arm_id,
        expected_row_producer_function="evaluate_pair",
    )


def produce_fresh_replay_stream(
    primary_stream_receipt: Mapping[str, Any], *, expected_arm_id: str = "MIXTURE_BMA_ACTIVE_BRIER",
) -> dict[str, Any]:
    _validate_evidence_receipt(
        primary_stream_receipt, producer_function="produce_primary_population_stream",
        input_sources=("case_pairs",),
    )
    rows = tuple(replay_pair(row) for row in primary_stream_receipt["rows"])
    return _produce_population_stream_receipt(
        rows, producer_function="produce_fresh_replay_stream",
        input_source="primary_population_stream_receipt", expected_arm_id=expected_arm_id,
        expected_row_producer_function="replay_pair",
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
    primary_code_hash = compute_sha256(Path(__file__))
    independent_code_hash = compute_sha256(REPO_ROOT / "scripts/codex/recompute_ego_v2_compositional_causal_transfer_preflight_001e.py")
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
            raise ArtifactValidationError("population stream arm/count/hash mismatch")
    if leakage_stream_receipt["coverage"]["case_count"] != len(leakage_cases) or leakage_stream_receipt["coverage"]["cases_sha256"] != _evidence_sha256(leakage_cases):
        raise ArtifactValidationError("leakage stream count/hash mismatch")
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
            raise ArtifactValidationError("leakage scan receipt status/producer/schema mismatch")
    case_ids = tuple(case.get("case_id") for case in leakage_cases)
    if len(set(case_ids)) != len(case_ids) or set(case_ids) != set(LEAKAGE_CASE_IDS):
        raise ArtifactValidationError("leakage scan case coverage mismatch")
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


def fraction_to_json(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def fraction_from_json(value: Mapping[str, Any]) -> Fraction:
    if set(value) != {"numerator", "denominator"} or not isinstance(value["numerator"], int) or not isinstance(value["denominator"], int) or value["denominator"] <= 0:
        raise ArtifactValidationError("invalid rational encoding")
    return Fraction(value["numerator"], value["denominator"])


def fraction_jsonify(value: Any) -> Any:
    if isinstance(value, Fraction):
        return fraction_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): fraction_jsonify(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [fraction_jsonify(child) for child in value]
    return value


def _restore_fractions(value: Any) -> Any:
    if isinstance(value, Mapping):
        if set(value) == {"numerator", "denominator"}:
            return fraction_from_json(value)
        return {key: _restore_fractions(child) for key, child in value.items()}
    if isinstance(value, list):
        return tuple(_restore_fractions(child) for child in value)
    return value


def serialize_row(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = fraction_jsonify(record)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["row_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def deserialize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    supplied_hash = payload.pop("row_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if supplied_hash is not None and supplied_hash != hashlib.sha256(canonical.encode("utf-8")).hexdigest():
        raise ArtifactValidationError("row hash mismatch")
    selected = payload.get("selected_query")
    if selected not in {*SECOND_QUERY_CANDIDATES, "UNIFORM_MIXTURE"}:
        raise ArtifactValidationError("invalid selected query")
    restored = _restore_fractions(payload)
    if restored.get("arm_id") not in {"MIXTURE_BMA_ACTIVE_BRIER", *CONTROL_REGISTRY}:
        raise ArtifactValidationError("unregistered serialized arm")
    minimizers = tuple(restored.get("minimizers", ()))
    if not minimizers or any(query not in SECOND_QUERY_CANDIDATES for query in minimizers) or tuple(sorted(set(minimizers))) != minimizers:
        raise ArtifactValidationError("invalid query minimizer set")
    query_scores = restored.get("query_scores")
    if not isinstance(query_scores, Mapping) or any(query not in SECOND_QUERY_CANDIDATES or not isinstance(score, Fraction) or score < 0 for query, score in query_scores.items()):
        raise ArtifactValidationError("invalid exact query scores")
    if selected == "UNIFORM_MIXTURE":
        if minimizers != SECOND_QUERY_CANDIDATES:
            raise ArtifactValidationError("uniform mixture query set mismatch")
    elif selected != minimizers[0] or selected not in query_scores:
        raise ArtifactValidationError("lexical query-tie rule mismatch")
    if restored.get("lexical_terminal_loss") != (sum(query_scores.values(), Fraction(0, 1)) / len(query_scores) if selected == "UNIFORM_MIXTURE" else query_scores[selected]):
        raise ArtifactValidationError("lexical terminal loss mismatch")
    return restored


def validate_artifact_record(record: Mapping[str, Any]) -> None:
    required = {"metric_id", "producer_function", "input_artifacts", "run_id", "aggregation_rule", "code_path_hash", "value"}
    if set(record) != required:
        raise ArtifactValidationError("artifact metric schema mismatch")
    fraction_from_json(record["value"])


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


def replay_row(record: Mapping[str, Any]) -> dict[str, Any]:
    try:
        expected = run_arm(str(record["arm_id"]), record["public_input"])
    except Exception as exc:
        return {"match": False, "error": type(exc).__name__}
    return {"match": public_state_signature(record) == public_state_signature(expected)}


def run_formal_population(*, output_dir: Path) -> None:
    del output_dir
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


def main() -> int:
    raise FormalExecutionNotAuthorizedError(FORMAL_BLOCK)


if __name__ == "__main__":
    main()
