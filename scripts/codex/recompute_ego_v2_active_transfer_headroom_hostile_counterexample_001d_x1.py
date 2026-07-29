from __future__ import annotations

import json
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations
from math import gcd
from pathlib import Path
from typing import Any


TASK_ID = "EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-HOSTILE-COUNTEREXAMPLE-001D-X1"
PARENT_TASK_ID = "EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D"
REPO = Path(__file__).resolve().parents[2]
DESIGN_PATH = REPO / "docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json"
DESIGN_SHA256 = "f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916"

PRIMARY_ARM = "ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK"
RAW_ARM = "ARM_I_TRANSFER__A_L1_EVSI__D_L1_MEDIAN"
PUBLIC_ARM = "ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1"
ARM_ORDER = (PRIMARY_ARM, RAW_ARM, PUBLIC_ARM)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _design() -> dict[str, Any]:
    if _file_sha256(DESIGN_PATH) != DESIGN_SHA256:
        raise ValueError("frozen design hash drift")
    value = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if value["task_id"] != PARENT_TASK_ID:
        raise ValueError("frozen design task drift")
    return value


@lru_cache(maxsize=1)
def mapping_space() -> tuple[tuple[int, ...], ...]:
    return tuple(permutations(range(5)))


def _mapping_bytes(mapping: tuple[int, ...]) -> bytes:
    return json.dumps(list(mapping), separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _validate_mapping(mapping: Any) -> tuple[int, ...]:
    if not isinstance(mapping, (list, tuple)) or len(mapping) != 5:
        raise ValueError("mapping shape drift")
    if any(type(value) is not int for value in mapping):
        raise ValueError("mapping entry type drift")
    row = tuple(mapping)
    if tuple(sorted(row)) != (0, 1, 2, 3, 4):
        raise ValueError("mapping must be a permutation")
    return row


def _validate_bank(bank: Any) -> tuple[tuple[int, ...], ...]:
    if not isinstance(bank, (list, tuple)) or len(bank) != 6:
        raise ValueError("bank shape drift")
    return tuple(sorted(_validate_mapping(row) for row in bank))


def _bank_bytes(bank: Any) -> bytes:
    return json.dumps([list(row) for row in _validate_bank(bank)], separators=(",", ":"), ensure_ascii=True).encode("ascii")


def build_hash_bank_zero() -> tuple[tuple[int, ...], ...]:
    prefix = f"{PARENT_TASK_ID}\x1fHASH_BANK\x1f0\x1f".encode("utf-8")
    ranked = sorted(
        mapping_space(),
        key=lambda mapping: (sha256(prefix + _mapping_bytes(mapping)).digest(), _mapping_bytes(mapping)),
    )
    return tuple(sorted(ranked[:6]))


@lru_cache(maxsize=1)
def _prototype_table() -> tuple[tuple[int, ...], ...]:
    rows = tuple(tuple(int(value) for value in row) for row in _design()["public_grammar"]["prototype_vectors_micro"])
    if len(rows) != 5 or any(len(row) != 4 for row in rows):
        raise ValueError("prototype table drift")
    return rows


@lru_cache(maxsize=1)
def _mapping_index() -> dict[tuple[int, ...], int]:
    return {mapping: index for index, mapping in enumerate(mapping_space())}


def _source_counts(bank: Any) -> tuple[int, ...]:
    counts = [0] * 120
    index = _mapping_index()
    for mapping in _validate_bank(bank):
        counts[index[mapping]] += 1
    return tuple(counts)


def _swap(mapping: tuple[int, ...], left: int, right: int) -> tuple[int, ...]:
    row = list(mapping)
    row[left], row[right] = row[right], row[left]
    return tuple(row)


def _local_counts(bank: Any) -> tuple[int, ...]:
    counts = [0] * 120
    index = _mapping_index()
    for mapping in _validate_bank(bank):
        for left, right in combinations(range(5), 2):
            counts[index[_swap(mapping, left, right)]] += 1
    return tuple(counts)


def _condition(weights: tuple[int, ...], history: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    return tuple(
        weight if weight > 0 and all(mapping[token] == outcome for token, outcome in history) else 0
        for mapping, weight in zip(mapping_space(), weights)
    )


def _primitive(weights: tuple[int, ...]) -> tuple[int, ...]:
    divisor = 0
    for weight in weights:
        if weight > 0:
            divisor = gcd(divisor, weight)
    if divisor <= 0:
        raise ValueError("zero posterior")
    return tuple(weight // divisor for weight in weights)


def _weights(inference: str, bank: Any, history: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    if inference == "scratch":
        base = tuple([1] * 120)
    elif inference == "transfer":
        source = _source_counts(bank)
        local = _local_counts(bank)
        base = tuple(1 + 20 * source[index] + 2 * local[index] for index in range(120))
    else:
        raise ValueError("unknown inference")
    return _primitive(_condition(base, history))


def round_half_even(numerator: int, denominator: int) -> int:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("invalid exact rounding input")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient % 2 == 1):
        quotient += 1
    return sign * quotient


def weighted_median_endpoints(values: Any, weights: Any) -> tuple[int, int, int]:
    if not isinstance(values, (list, tuple)) or not isinstance(weights, (list, tuple)) or len(values) != len(weights):
        raise ValueError("median shape drift")
    pairs = sorted((int(value), int(weight)) for value, weight in zip(values, weights) if int(weight) > 0)
    if not pairs:
        raise ValueError("empty weighted median")
    total = sum(weight for _, weight in pairs)
    cumulative = 0
    lower = pairs[0][0]
    for value, weight in pairs:
        cumulative += weight
        if 2 * cumulative >= total:
            lower = value
            break
    cumulative = 0
    upper = pairs[-1][0]
    for value, weight in reversed(pairs):
        cumulative += weight
        if 2 * cumulative >= total:
            upper = value
            break
    midpoint = round_half_even(lower + upper, 2)
    risks = [sum(weight * abs(value - action) for value, weight in pairs) for action in (lower, midpoint, upper)]
    if len(set(risks)) != 1:
        raise AssertionError("median risk identity failed")
    return lower, midpoint, upper


def _prediction(weights: tuple[int, ...], token: int) -> tuple[tuple[int, ...], tuple[tuple[int, int, int], ...]]:
    rows = [_prototype_table()[mapping[token]] for mapping, weight in zip(mapping_space(), weights) if weight > 0]
    masses = [weight for weight in weights if weight > 0]
    output = []
    endpoints = []
    for component in range(4):
        endpoint = weighted_median_endpoints([row[component] for row in rows], masses)
        endpoints.append(endpoint)
        output.append(endpoint[1])
    return tuple(output), tuple(endpoints)


def _l1(left: Any, right: Any) -> int:
    return sum(abs(int(a) - int(b)) for a, b in zip(left, right))


def _posterior_counts(weights: tuple[int, ...], token: int) -> dict[int, int]:
    counts: dict[int, int] = {}
    for mapping, weight in zip(mapping_space(), weights):
        if weight > 0:
            counts[mapping[token]] = counts.get(mapping[token], 0) + weight
    return counts


def _arm_semantics(arm_id: str) -> tuple[str, str]:
    if arm_id == PRIMARY_ARM:
        return "transfer", "lcb"
    if arm_id == RAW_ARM:
        return "transfer", "raw"
    if arm_id == PUBLIC_ARM:
        return "scratch", "scratch"
    raise ValueError("unsupported X1 arm")


def _q05_benefit(
    transfer_weights: tuple[int, ...],
    transfer_prediction: tuple[int, ...],
    scratch_prediction: tuple[int, ...],
    token: int,
) -> int:
    values = []
    for mapping, weight in zip(mapping_space(), transfer_weights):
        if weight > 0:
            truth = _prototype_table()[mapping[token]]
            benefit = _l1(scratch_prediction, truth) - _l1(transfer_prediction, truth)
            values.append((benefit, weight))
    total = sum(weight for _, weight in values)
    cumulative = 0
    for benefit, weight in sorted(values):
        cumulative += weight
        if 20 * cumulative >= total:
            return benefit
    raise AssertionError("q05 selection failed")


def _prediction_decision(arm_id: str, bank: Any, history: tuple[tuple[int, int], ...]) -> dict[str, Any]:
    inference, decision = _arm_semantics(arm_id)
    transfer_weights = _weights(inference, bank, history)
    scratch_weights = _weights("scratch", bank, history)
    observed = dict(history)
    predictions = []
    endpoint_rows = []
    used_transfer = []
    lcb_values = []
    for token in range(5):
        if token in observed:
            row = _prototype_table()[observed[token]]
            predictions.append(list(row))
            endpoint_rows.append([[value, value] for value in row])
            used_transfer.append(False)
            lcb_values.append(None)
            continue
        transfer, transfer_endpoints = _prediction(transfer_weights, token)
        scratch, scratch_endpoints = _prediction(scratch_weights, token)
        if decision == "scratch":
            selected = scratch
            endpoints = scratch_endpoints
            use_transfer = False
            q05 = None
        elif decision == "raw":
            selected = transfer
            endpoints = transfer_endpoints
            use_transfer = True
            q05 = None
        else:
            q05 = _q05_benefit(transfer_weights, transfer, scratch, token)
            use_transfer = q05 >= 0
            selected = transfer if use_transfer else scratch
            endpoints = transfer_endpoints if use_transfer else scratch_endpoints
        predictions.append(list(selected))
        endpoint_rows.append([[lower, upper] for lower, _, upper in endpoints])
        used_transfer.append(use_transfer)
        lcb_values.append(q05)
    return {
        "prediction_micro": predictions,
        "median_endpoints_micro": endpoint_rows,
        "used_transfer": used_transfer,
        "lcb05_benefit_micro": lcb_values,
    }


def _query_decision(arm_id: str, bank: Any, h1: tuple[tuple[int, int], ...]) -> dict[str, Any]:
    inference, _ = _arm_semantics(arm_id)
    h1_weights = _weights(inference, bank, h1)
    eligible = tuple(token for token in range(5) if token not in {row[0] for row in h1})
    score_rows = []
    for query in eligible:
        score = 0
        for outcome in sorted(_posterior_counts(h1_weights, query)):
            h2 = h1 + ((query, outcome),)
            decision = _prediction_decision(arm_id, bank, h2)
            for mapping, weight in zip(mapping_space(), h1_weights):
                if weight <= 0 or mapping[query] != outcome:
                    continue
                for token in range(5):
                    if token not in {h1[0][0], query}:
                        score += weight * _l1(
                            decision["prediction_micro"][token],
                            _prototype_table()[mapping[token]],
                        )
        score_rows.append({"token_index": query, "int_score": score})
    minimum = min(row["int_score"] for row in score_rows)
    minimizing = [row["token_index"] for row in score_rows if row["int_score"] == minimum]
    return {
        "eligible_tokens": list(eligible),
        "score_kind": "l1_risk_integer",
        "exact_scores": score_rows,
        "minimizing_tokens": minimizing,
        "selected_token": min(minimizing),
        "tie_rule": "lexical_minimum",
    }


def _rational(value: Fraction | int) -> dict[str, int]:
    fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
    return {"n": fraction.numerator, "d": fraction.denominator}


def _metric_rational(raw: int, components: int) -> dict[str, int]:
    return _rational(Fraction(raw, components * 1_000_000))


def _token_losses(decision: dict[str, Any], target: tuple[int, ...]) -> list[int]:
    return [
        _l1(decision["prediction_micro"][token], _prototype_table()[target[token]])
        for token in range(5)
    ]


def _evaluate_metric(bank: Any, target: Any, arm_id: str) -> dict[str, Any]:
    bank = _validate_bank(bank)
    target = _validate_mapping(target)
    h1 = ((0, target[0]),)
    candidate_query = _query_decision(arm_id, bank, h1)
    q_candidate = candidate_query["selected_token"]
    candidate_history = h1 + ((q_candidate, target[q_candidate]),)
    candidate = _prediction_decision(arm_id, bank, candidate_history)

    public_query = _query_decision(PUBLIC_ARM, bank, h1)
    q_public = public_query["selected_token"]
    public_history = h1 + ((q_public, target[q_public]),)
    public = _prediction_decision(PUBLIC_ARM, bank, public_history)
    same_history = _prediction_decision(PUBLIC_ARM, bank, candidate_history)

    candidate_losses = _token_losses(candidate, target)
    public_losses = _token_losses(public, target)
    same_losses = _token_losses(same_history, target)
    candidate_tokens = [token for token in range(5) if token not in {0, q_candidate}]
    public_tokens = [token for token in range(5) if token not in {0, q_public}]
    common_tokens = [token for token in range(5) if token not in {0, q_candidate, q_public}]
    own_denominator = 4 * len(candidate_tokens)
    public_denominator = 4 * len(public_tokens)
    common_denominator = 4 * len(common_tokens)

    candidate_full = sum(candidate_losses)
    public_full = sum(public_losses)
    candidate_own = sum(candidate_losses[token] for token in candidate_tokens)
    public_own = sum(public_losses[token] for token in public_tokens)
    candidate_common = sum(candidate_losses[token] for token in common_tokens)
    public_common = sum(public_losses[token] for token in common_tokens)
    same_raw = sum(same_losses[token] for token in candidate_tokens)
    common_raw = public_common - candidate_common
    query_asymmetry = 0 if q_candidate == q_public else public_losses[q_candidate] - candidate_losses[q_public]
    full_improvement = public_full - candidate_full
    if full_improvement != common_raw + query_asymmetry:
        raise AssertionError("metric decomposition drift")
    same_forward = same_raw - candidate_own

    rationals = {
        "candidate_full_endpoint_mae": _metric_rational(candidate_full, 20),
        "baseline_full_endpoint_mae": _metric_rational(public_full, 20),
        "full_endpoint_improvement": _metric_rational(full_improvement, 20),
        "candidate_own_unqueried_forward_mae": _metric_rational(candidate_own, own_denominator),
        "baseline_own_unqueried_forward_mae": _metric_rational(public_own, public_denominator),
        "candidate_common_unqueried_forward_mae": _metric_rational(candidate_common, common_denominator),
        "baseline_common_unqueried_forward_mae": _metric_rational(public_common, common_denominator),
        "common_unqueried_forward_improvement": _metric_rational(common_raw, common_denominator),
        "candidate_same_history_forward_mae": _metric_rational(candidate_own, own_denominator),
        "same_history_scratch_forward_mae": _metric_rational(same_raw, own_denominator),
        "same_history_forward_improvement": _metric_rational(same_forward, own_denominator),
        "common_contribution_to_full_improvement": _metric_rational(common_raw, 20),
        "query_asymmetry_contribution_to_full_improvement": _metric_rational(query_asymmetry, 20),
    }
    return {
        "arm_id": arm_id,
        "target_mapping": list(target),
        "selected_query_token": q_candidate,
        "public_selected_query_token": q_public,
        "candidate_prediction_micro": candidate["prediction_micro"],
        "public_prediction_micro": public["prediction_micro"],
        "same_history_scratch_prediction_micro": same_history["prediction_micro"],
        "used_transfer": candidate["used_transfer"],
        "lcb05_benefit_micro": candidate["lcb05_benefit_micro"],
        "candidate_token_losses_raw": candidate_losses,
        "baseline_token_losses_raw": public_losses,
        "same_history_scratch_token_losses_raw": same_losses,
        "full_improvement_raw": full_improvement,
        "common_raw": common_raw,
        "query_asymmetry_raw": query_asymmetry,
        "same_history_forward_raw": same_forward,
        "metric_denominators": {
            "full": 20,
            "own_unqueried": own_denominator,
            "common_unqueried": common_denominator,
            "same_history_forward": own_denominator,
        },
        "metric_rationals": rationals,
    }


def _classification(bank: Any, target: Any) -> dict[str, Any]:
    bank = _validate_bank(bank)
    target = _validate_mapping(target)
    occurrence = sum(mapping == target for mapping in bank)
    distance = min(sum(left != right for left, right in zip(source, target)) for source in set(bank))
    if occurrence:
        stratum = "EXACT_MEMBER_D0"
    else:
        stratum = f"NONMEMBER_D{distance}" if distance >= 3 else "LOCAL_SHIFT_D2"
    return {"stratum": stratum, "source_occurrence": occurrence, "distance": distance}


def _fraction(value: dict[str, int]) -> Fraction:
    return Fraction(value["n"], value["d"])


def _thresholds() -> dict[str, dict[str, int]]:
    source = _design()["thresholds"]
    keys = (
        "member_full_improvement_min",
        "member_common_forward_min",
        "member_same_history_forward_min",
        "canonical_member_common_forward_min",
        "canonical_member_same_history_forward_min",
        "nonmember_bounded_full_regret_max",
        "nonmember_strict_full_regret_max",
    )
    return {key: _rational(Fraction(source[key])) for key in keys}


def _aggregate_arm(bank: Any, rows: list[dict[str, Any]], arm_id: str, thresholds: dict[str, Any]) -> dict[str, Any]:
    arm_rows = [row for row in rows if row["arm_id"] == arm_id]
    by_target = {tuple(row["target_mapping"]): row for row in arm_rows}
    support = tuple(sorted(set(_validate_bank(bank))))
    member_rows = []
    for target in support:
        metric = by_target[target]["metric"]
        full = _fraction(metric["metric_rationals"]["full_endpoint_improvement"])
        common = _fraction(metric["metric_rationals"]["common_unqueried_forward_improvement"])
        same = _fraction(metric["metric_rationals"]["same_history_forward_improvement"])
        passed = (
            full >= _fraction(thresholds["member_full_improvement_min"])
            and common >= _fraction(thresholds["member_common_forward_min"])
            and same >= _fraction(thresholds["member_same_history_forward_min"])
        )
        member_rows.append({
            "target_mapping": list(target),
            "full_improvement": _rational(full),
            "common_improvement": _rational(common),
            "same_history_improvement": _rational(same),
            "passes": passed,
        })
    canonical = support[0]
    canonical_row = next(row for row in member_rows if tuple(row["target_mapping"]) == canonical)
    canonical_pass = (
        _fraction(canonical_row["common_improvement"]) >= _fraction(thresholds["canonical_member_common_forward_min"])
        and _fraction(canonical_row["same_history_improvement"]) >= _fraction(thresholds["canonical_member_same_history_forward_min"])
    )
    nonmembers = [row for row in arm_rows if row["classification"]["distance"] > 0]
    worst = min(
        nonmembers,
        key=lambda row: _fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"]),
    )
    worst_improvement = _fraction(worst["metric"]["metric_rationals"]["full_endpoint_improvement"])
    bounded_safety = all(
        -_fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"])
        <= _fraction(thresholds["nonmember_bounded_full_regret_max"])
        for row in nonmembers
    )
    strict_safety = all(
        -_fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"])
        <= _fraction(thresholds["nonmember_strict_full_regret_max"])
        for row in nonmembers
    )
    return {
        "arm_id": arm_id,
        "canonical_member": list(canonical),
        "member_rows": member_rows,
        "all_distinct_members_pass": all(row["passes"] for row in member_rows),
        "canonical_member_passes": canonical_pass,
        "member_and_forward": all(row["passes"] for row in member_rows) and canonical_pass,
        "bounded_safety": bounded_safety,
        "strict_safety": strict_safety,
        "worst_nonmember": {
            "target_mapping": worst["target_mapping"],
            "classification": worst["classification"],
            "full_improvement": _rational(worst_improvement),
            "regret": _rational(-worst_improvement),
        },
    }


@lru_cache(maxsize=1)
def _build_cached() -> dict[str, Any]:
    bank = build_hash_bank_zero()
    thresholds = _thresholds()
    rows = []
    for arm_id in ARM_ORDER:
        for target in mapping_space():
            rows.append({
                "arm_id": arm_id,
                "target_mapping": list(target),
                "classification": _classification(bank, target),
                "metric": _evaluate_metric(bank, target, arm_id),
            })
    aggregate = {
        "schema_version": "X1_GATE_AGGREGATE_V1",
        "bank_role_id": "HASH_00",
        "median_convention": "midpoint_integer",
        "query_tie_rule": "lexical_minimum",
        "target_count": 120,
        "row_count": 360,
        "conservative": _aggregate_arm(bank, rows, PRIMARY_ARM, thresholds),
        "raw": _aggregate_arm(bank, rows, RAW_ARM, thresholds),
        "public": _aggregate_arm(bank, rows, PUBLIC_ARM, thresholds),
    }
    payload = {
        "schema_version": "X1_INDEPENDENT_EVIDENCE_V1",
        "task_id": TASK_ID,
        "bank": [list(row) for row in bank],
        "bank_sha256": sha256(_bank_bytes(bank)).hexdigest(),
        "thresholds": thresholds,
        "rows": rows,
        "aggregate": aggregate,
    }
    payload["payload_sha256"] = sha256(canonical_bytes(payload)).hexdigest()
    return payload


def build_independent_evidence() -> dict[str, Any]:
    return deepcopy(_build_cached())


if __name__ == "__main__":
    print(json.dumps({
        "task_id": TASK_ID,
        "bank_sha256": build_independent_evidence()["bank_sha256"],
        "row_count": 360,
    }, sort_keys=True))
