#!/usr/bin/env python3
"""Exact seed-free feasibility preflight for the frozen R5 transfer gate.

This producer has no world, seed, source-history, controller, engine, or private
mapping input.  NumPy is used only to batch signed-integer arithmetic; every
posterior, rounding, quantile, threshold, and verdict comparison is exact.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
from itertools import combinations, permutations
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


TASK_ID = "EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6"
SCHEMA_VERSION = "ego.v2.conservative_transfer.static_headroom_preflight.v1"
PRODUCER_MODULE = "check_ego_v2_conservative_transfer_static_headroom_001c_r6"
AGGREGATION_RULE = (
    "complete_integer_enumeration_of_all_six_source_posterior_weight_states_"
    "and_all_120_target_mappings_at_feedback_budget_2"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / TASK_ID

R5_AUTHORITY = {
    "docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-BENCHMARK-ADMISSION-001C-R5.md": (
        "d9bef189de2d62f157fafcf44874940cdf41a1997c51d4ebbfe27e7d094fbc53"
    ),
    "docs/codex/tasks/ego-v2-p1-conservative-transfer-benchmark-admission-001c-r5/COLLISION_RECORD.md": (
        "44d76988be7269201ff606c16c7813f634ee0afa7b3dff676e7fedc2c8962c1a"
    ),
    "docs/codex/tasks/ego-v2-p1-conservative-transfer-benchmark-admission-001c-r5/FROZEN_DESIGN.json": (
        "07abe6caadce1f7b76cfeee051b5d62c63a11f0f115e912e09c89eea42296443"
    ),
}
R6_AUTHORITY_PATHS = (
    "docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6.md",
    "docs/codex/tasks/ego-v2-p1-conservative-transfer-static-headroom-preflight-001c-r6/COLLISION_RECORD.md",
)
TEST_RELATIVE_PATH = (
    "scripts/codex/tests/"
    "test_check_ego_v2_conservative_transfer_static_headroom_001c_r6.py"
)

MICRO = 1_000_000
BASE = np.array([-18_000, 0, 0, 0], dtype=np.int64)
SCORER_STATE = np.array([450_000, 620_000, 500_000, 430_000], dtype=np.int64)
PROTOTYPE_BYTES = (
    b"[0.0,-0.02,0.0,0.16]",
    b"[0.0,-0.18,0.0,0.04]",
    b"[0.0,0.0,0.16,0.02]",
    b"[0.0,0.12,0.0,0.0]",
    b"[0.28,0.0,0.0,0.0]",
)


def prototype_micro_units_from_frozen_bytes() -> np.ndarray:
    rows: list[list[int]] = []
    for raw in PROTOTYPE_BYTES:
        values = json.loads(raw.decode("ascii"), parse_float=Decimal)
        if not isinstance(values, list) or len(values) != 4:
            raise AssertionError("frozen prototype JSON shape drift")
        row: list[int] = []
        for value in values:
            decimal_value = value if isinstance(value, Decimal) else Decimal(value)
            scaled = decimal_value * MICRO
            if scaled != scaled.to_integral_value():
                raise AssertionError("prototype is not exact at micro-unit scale")
            row.append(int(scaled))
        rows.append(row)
    return np.array(rows, dtype=np.int64)


PROTOTYPES = prototype_micro_units_from_frozen_bytes()
PROTOTYPE_HASHES = (
    "22659515e916b3b5ead3390438733bda2e15df9b44b6b0b9afcab30718b0dae9",
    "9799be678e4269454a06e199889f37eee9cc1aec02b810befdef3fcc583b04b8",
    "3d6288b3042ee89950548d7a3ef44d183243feb7af0913ce9a25b9a2b040099f",
    "4df0754afbdd63f7e4865bfd10062c20ec5414e469c6b4f8776cddbd8babd5ff",
    "846bdcd2a0768a906623d807c95580c025a63b99d87b2335d7d097f972f71c16",
)
MAPPINGS = tuple(permutations(range(5)))
SWAPS = tuple(combinations(range(5), 2))
REQUIRED_TOTAL_REDUCTION_MICRO = 437_500

_STATE_LAYERS: tuple[frozenset[tuple[int, ...]], ...] | None = None
_PRIMARY_CACHE: dict[str, Any] | None = None
_CROSSCHECK_CACHE: dict[str, Any] | None = None
_ABLATION_CACHE: dict[str, Any] | None = None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def swap(mapping: Sequence[int], pair: tuple[int, int]) -> tuple[int, ...]:
    result = list(mapping)
    left, right = pair
    result[left], result[right] = result[right], result[left]
    return tuple(result)


def _compatible_mappings(observed_pair: tuple[int, int]) -> tuple[tuple[int, ...], ...]:
    return tuple(mapping for mapping in MAPPINGS if mapping[:2] == observed_pair)


def _source_contribution(
    source: tuple[int, ...], compatible: Sequence[tuple[int, ...]]
) -> tuple[int, ...]:
    position = {mapping: index for index, mapping in enumerate(compatible)}
    vector = [0] * 6
    if source in position:
        vector[position[source]] += 20
    for pair in SWAPS:
        neighbour = swap(source, pair)
        if neighbour in position:
            vector[position[neighbour]] += 2
    return tuple(vector)


def source_vectors(target: tuple[int, ...] = MAPPINGS[0]) -> frozenset[tuple[int, ...]]:
    compatible = _compatible_mappings((target[0], target[1]))
    vectors = frozenset(_source_contribution(source, compatible) for source in MAPPINGS)
    if len(vectors) != 13:
        raise AssertionError("per-source contribution grammar drift")
    return vectors


def _state_layers() -> tuple[frozenset[tuple[int, ...]], ...]:
    global _STATE_LAYERS
    if _STATE_LAYERS is not None:
        return _STATE_LAYERS
    vectors = source_vectors()
    layers: list[frozenset[tuple[int, ...]]] = [frozenset({(0, 0, 0, 0, 0, 0)})]
    for _ in range(6):
        layers.append(
            frozenset(
                tuple(left + right for left, right in zip(state, vector))
                for state in layers[-1]
                for vector in vectors
            )
        )
    expected = (1, 13, 91, 455, 1_820, 6_188, 18_564)
    observed = tuple(len(layer) for layer in layers)
    if observed != expected:
        raise AssertionError(f"attainable-state grammar drift: {observed!r}")
    _STATE_LAYERS = tuple(layers)
    return _STATE_LAYERS


def six_source_states() -> np.ndarray:
    canonical_vectors = source_vectors()
    if any(source_vectors(mapping) != canonical_vectors for mapping in MAPPINGS):
        raise AssertionError("source contribution grammar is not relabel-invariant")
    return np.array(sorted(_state_layers()[6]), dtype=np.int64)


def _true_analogy_states(
    target_mapping: tuple[int, ...], compatible: Sequence[tuple[int, ...]]
) -> np.ndarray:
    target_vector = _source_contribution(target_mapping, compatible)
    # Selecting one required target entry plus any other five entries exactly
    # covers every multiset in which the target occurs at least once.
    states = {
        tuple(left + right for left, right in zip(target_vector, five_state))
        for five_state in _state_layers()[5]
    }
    if len(states) != 6_188:
        raise AssertionError("true-analogy state grammar drift")
    return np.array(sorted(states), dtype=np.int64)


def round_half_even_scalar(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(int(numerator)), int(denominator))
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        quotient += 1
    return sign * quotient


def _round_half_even_ratio(numerator: np.ndarray, denominator: np.ndarray | int) -> np.ndarray:
    denominator_array = np.asarray(denominator, dtype=np.int64)
    if np.any(denominator_array <= 0):
        raise ValueError("denominator must be positive")
    sign = np.where(numerator < 0, -1, 1)
    absolute = np.abs(numerator)
    quotient = absolute // denominator_array
    remainder = absolute % denominator_array
    increment = (2 * remainder > denominator_array) | (
        (2 * remainder == denominator_array) & (quotient % 2 == 1)
    )
    return sign * (quotient + increment.astype(np.int64))


def weighted_lower_quantile(
    *,
    benefits: Sequence[int],
    weights: Sequence[int],
    numerator: int,
    denominator: int,
) -> int:
    if len(benefits) != len(weights) or not benefits:
        raise ValueError("benefits and weights must be non-empty and aligned")
    if numerator <= 0 or denominator <= 0 or numerator > denominator:
        raise ValueError("quantile must be in (0,1]")
    grouped: dict[int, int] = {}
    for benefit, weight in zip(benefits, weights):
        if type(weight) is not int or weight <= 0:
            raise ValueError("weights must be positive integers")
        grouped[int(benefit)] = grouped.get(int(benefit), 0) + weight
    total = sum(grouped.values())
    cumulative = 0
    for benefit, weight in sorted(grouped.items()):
        cumulative += weight
        if denominator * cumulative >= numerator * total:
            return benefit
    raise AssertionError("quantile accumulation failed")


def _posterior_gate_decisions(
    *, benefits: np.ndarray, weights: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    if (
        benefits.ndim != 2
        or weights.ndim != 2
        or benefits.shape != weights.shape
        or benefits.shape[1] == 0
        or np.any(weights <= 0)
    ):
        raise ValueError("benefits and positive weights must have one aligned 2D shape")
    denominators = weights.sum(axis=1)[:, None]
    order = np.argsort(benefits, axis=1, kind="stable")
    ordered_benefits = np.take_along_axis(benefits, order, axis=1)
    ordered_weights = np.take_along_axis(weights, order, axis=1)
    cumulative = np.cumsum(ordered_weights, axis=1)
    threshold_reached = 20 * cumulative >= denominators
    q_index = threshold_reached.argmax(axis=1)
    q05 = ordered_benefits[np.arange(len(benefits)), q_index]
    return q05, q05 >= 0


def fixed_signatures() -> dict[str, Any]:
    hashes = tuple(sha256(raw).hexdigest() for raw in PROTOTYPE_BYTES)
    if hashes != PROTOTYPE_HASHES or tuple(sorted(PROTOTYPE_BYTES)) != PROTOTYPE_BYTES:
        raise AssertionError("card-frozen prototype bytes or ordering drift")
    decoded = prototype_micro_units_from_frozen_bytes()
    if not np.array_equal(PROTOTYPES, decoded):
        raise AssertionError("evaluated prototype geometry is not bound to frozen bytes")
    if MAPPINGS[0] != (0, 1, 2, 3, 4):
        raise AssertionError("identity mapping index drift")
    if MAPPINGS[24] != (1, 0, 2, 3, 4):
        raise AssertionError("swap-0-1 mapping index drift")
    if MAPPINGS[119] != (4, 3, 2, 1, 0):
        raise AssertionError("reverse mapping index drift")
    posts = SCORER_STATE + BASE + PROTOTYPES
    expected_posts = np.array(
        [
            [432_000, 600_000, 500_000, 590_000],
            [432_000, 440_000, 500_000, 470_000],
            [432_000, 620_000, 660_000, 450_000],
            [432_000, 740_000, 500_000, 430_000],
            [712_000, 620_000, 500_000, 430_000],
        ],
        dtype=np.int64,
    )
    if not np.array_equal(posts, expected_posts):
        raise AssertionError("canonical scorer post-state drift")
    if not np.all((posts > 0) & (posts < MICRO)):
        raise AssertionError("canonical scorer must remain fully non-clipped")
    return {
        "prototype_micro_units": PROTOTYPES.tolist(),
        "prototype_canonical_json": [raw.decode("ascii") for raw in PROTOTYPE_BYTES],
        "prototype_sha256": list(PROTOTYPE_HASHES),
        "canonical_scorer_posts_micro": posts.tolist(),
        "permutation_indices": {"identity": 0, "swap_0_1": 24, "reverse": 119},
        "one_swap_order": [list(pair) for pair in SWAPS],
    }


def _evaluate_group(
    compatible: np.ndarray, states: np.ndarray, *, apply_gate: bool
) -> tuple[np.ndarray, int]:
    weights = states + 1
    denominators = weights.sum(axis=1)[:, None]
    reductions = np.zeros((len(states), 6), dtype=np.int64)
    nontrivial_gate_uses = 0
    for token_offset in range(3):
        truths = PROTOTYPES[compatible[:, token_offset]] + BASE
        scratch = _round_half_even_ratio(truths.sum(axis=0), 6)
        candidate = _round_half_even_ratio(weights @ truths, denominators)
        scratch_error = np.abs(truths - scratch).sum(axis=1)
        candidate_error = np.abs(candidate[:, None, :] - truths[None, :, :]).sum(axis=2)
        if apply_gate:
            benefits = scratch_error[None, :] - candidate_error
            _, use_candidate = _posterior_gate_decisions(
                benefits=benefits, weights=weights
            )
            nontrivial_gate_uses += int(
                np.count_nonzero(use_candidate & np.any(candidate != scratch, axis=1))
            )
            prediction = np.where(use_candidate[:, None], candidate, scratch)
        else:
            prediction = candidate
        endpoint_error = np.abs(prediction[:, None, :] - truths[None, :, :]).sum(axis=2)
        reductions += scratch_error[None, :] - endpoint_error
    return reductions, nontrivial_gate_uses


def exhaustive_result() -> dict[str, Any]:
    global _PRIMARY_CACHE
    if _PRIMARY_CACHE is not None:
        return json.loads(json.dumps(_PRIMARY_CACHE))
    fixed_signatures()
    states = six_source_states()
    state_index = {tuple(state): index for index, state in enumerate(states.tolist())}
    positive_cases = 0
    nontrivial_gate_uses = 0
    maximum_reduction = -1
    argmax: dict[str, Any] | None = None
    true_positive_cases = 0
    true_maximum_reduction = -1
    true_argmax: dict[str, Any] | None = None
    true_case_count = 0
    primary_case_count = 0
    covered_targets: set[tuple[int, ...]] = set()
    true_state_counts: set[int] = set()

    for remaining in combinations(range(5), 3):
        compatible_tuples = tuple(permutations(remaining))
        compatible = np.array(compatible_tuples, dtype=np.int64)
        reductions, uses = _evaluate_group(compatible, states, apply_gate=True)
        primary_case_count += int(reductions.size)
        nontrivial_gate_uses += uses
        positive_cases += int(np.count_nonzero(reductions > 0))
        local_flat = int(reductions.argmax())
        local_maximum = int(reductions.flat[local_flat])
        if local_maximum > maximum_reduction:
            state_i, truth_i = np.unravel_index(local_flat, reductions.shape)
            maximum_reduction = local_maximum
            argmax = {
                "remaining_prototypes": list(remaining),
                "source_state": states[state_i].tolist(),
                "truth_order": compatible[truth_i].tolist(),
            }

        # The observed complement ordering is irrelevant to these six weights;
        # use the ascending complement to construct exact target source entries.
        observed = tuple(value for value in range(5) if value not in remaining)
        for observed_order in (observed, tuple(reversed(observed))):
            covered_targets.update(
                (observed_order[0], observed_order[1], *tail)
                for tail in compatible_tuples
            )
        full_compatible = _compatible_mappings((observed[0], observed[1]))
        for truth_i, target_tail in enumerate(compatible_tuples):
            target_mapping = (observed[0], observed[1], *target_tail)
            true_states = _true_analogy_states(target_mapping, full_compatible)
            true_state_counts.add(int(len(true_states)))
            indices = np.array(
                [state_index[tuple(state)] for state in true_states.tolist()],
                dtype=np.int64,
            )
            truth_reductions = reductions[indices, truth_i]
            true_case_count += int(len(truth_reductions))
            true_positive_cases += int(np.count_nonzero(truth_reductions > 0))
            local_true_index = int(truth_reductions.argmax())
            local_true_maximum = int(truth_reductions[local_true_index])
            if local_true_maximum > true_maximum_reduction:
                true_maximum_reduction = local_true_maximum
                true_argmax = {
                    "remaining_prototypes": list(remaining),
                    "source_state": true_states[local_true_index].tolist(),
                    "truth_order": list(target_tail),
                    "target_mapping_occurs_in_source_multiset": True,
                }

    if covered_targets != set(MAPPINGS):
        raise AssertionError("target coverage does not equal the complete mapping space")
    if len(true_state_counts) != 1:
        raise AssertionError("true-analogy state count differs by target")
    true_state_count = next(iter(true_state_counts))
    result = {
        "mapping_count": len(MAPPINGS),
        "per_source_vector_count": len(source_vectors()),
        "attainable_six_source_state_count": int(len(states)),
        "covered_target_mapping_count": len(covered_targets),
        "evaluated_prior_target_case_count": primary_case_count,
        "positive_budget2_case_count": positive_cases,
        "nontrivial_transfer_gate_use_count": nontrivial_gate_uses,
        "maximum_total_absolute_error_reduction_micro": maximum_reduction,
        "maximum_mae_improvement": f"{maximum_reduction}/20000000",
        "true_analogy_state_count_per_target": true_state_count,
        "true_analogy_evaluated_case_count": true_case_count,
        "true_analogy_full_target_case_count_including_observed_order_symmetry": (
            true_case_count * 2
        ),
        "true_analogy_positive_budget2_case_count": true_positive_cases,
        "true_analogy_maximum_total_absolute_error_reduction_micro": (
            true_maximum_reduction
        ),
        "true_analogy_maximum_mae_improvement": (
            f"{true_maximum_reduction}/20000000"
        ),
        "required_total_absolute_error_reduction_micro": (
            REQUIRED_TOTAL_REDUCTION_MICRO
        ),
        "required_mae_improvement": "21875/1000000",
        "admission_possible": (
            true_maximum_reduction >= REQUIRED_TOTAL_REDUCTION_MICRO
        ),
        "unconstrained_argmax_example": argmax,
        "true_analogy_argmax_example": true_argmax,
    }
    _PRIMARY_CACHE = result
    return json.loads(json.dumps(result))


def ordered_pair_symmetry_crosscheck() -> dict[str, Any]:
    global _CROSSCHECK_CACHE
    if _CROSSCHECK_CACHE is not None:
        return json.loads(json.dumps(_CROSSCHECK_CACHE))
    states = six_source_states()
    positive = 0
    maximum = -1
    cases = 0
    for first in range(5):
        for second in range(5):
            if first == second:
                continue
            group = np.array(_compatible_mappings((first, second)), dtype=np.int64)
            weights = states + 1
            denominators = weights.sum(axis=1)[:, None]
            reductions = np.zeros((len(states), 6), dtype=np.int64)
            for token in (2, 3, 4):
                truths = PROTOTYPES[group[:, token]] + BASE
                scratch = _round_half_even_ratio(truths.sum(axis=0), 6)
                candidate = _round_half_even_ratio(weights @ truths, denominators)
                scratch_error = np.abs(truths - scratch).sum(axis=1)
                candidate_error = np.abs(
                    candidate[:, None, :] - truths[None, :, :]
                ).sum(axis=2)
                benefits = scratch_error[None, :] - candidate_error
                _, use_candidate = _posterior_gate_decisions(
                    benefits=benefits, weights=weights
                )
                chosen = np.where(use_candidate[:, None], candidate, scratch)
                chosen_error = np.abs(
                    chosen[:, None, :] - truths[None, :, :]
                ).sum(axis=2)
                reductions += scratch_error[None, :] - chosen_error
            cases += int(reductions.size)
            positive += int(np.count_nonzero(reductions > 0))
            maximum = max(maximum, int(reductions.max()))
    result = {
        "method": "ordered_observed_pair_enumeration",
        "evaluated_prior_target_case_count": cases,
        "positive_budget2_case_count": positive,
        "maximum_total_absolute_error_reduction_micro": maximum,
    }
    _CROSSCHECK_CACHE = result
    return json.loads(json.dumps(result))


def ungated_bma_diagnostic() -> dict[str, Any]:
    global _ABLATION_CACHE
    if _ABLATION_CACHE is not None:
        return json.loads(json.dumps(_ABLATION_CACHE))
    states = six_source_states()
    positive = 0
    maximum = -1
    minimum = 2**63 - 1
    for remaining in combinations(range(5), 3):
        compatible = np.array(tuple(permutations(remaining)), dtype=np.int64)
        reductions, _ = _evaluate_group(compatible, states, apply_gate=False)
        positive += int(np.count_nonzero(reductions > 0))
        maximum = max(maximum, int(reductions.max()))
        minimum = min(minimum, int(reductions.min()))
    result = {
        "ablation": "delete_lower_5pct_gate_and_always_use_transfer_bma",
        "verdict_role": "diagnostic_only_cannot_rescue",
        "evaluated_prior_target_case_count": int(len(states) * 10 * 6),
        "positive_case_count": positive,
        "maximum_total_absolute_error_reduction_micro": maximum,
        "minimum_total_absolute_error_reduction_micro": minimum,
        "interpretation": (
            "The frozen gate removes both potential benefit and negative-transfer "
            "harm; this diagnostic does not authorize changing the frozen rule."
        ),
    }
    _ABLATION_CACHE = result
    return json.loads(json.dumps(result))


def clear_computation_caches() -> None:
    global _PRIMARY_CACHE, _CROSSCHECK_CACHE, _ABLATION_CACHE
    _PRIMARY_CACHE = None
    _CROSSCHECK_CACHE = None
    _ABLATION_CACHE = None


def dispatch_verdict(
    primary: Mapping[str, Any],
    *,
    private_truth_or_seed_input: bool = False,
    instrument_invalid: bool = False,
) -> str:
    if private_truth_or_seed_input:
        return "PRIVATE_TRUTH_OR_SEED_INPUT"
    if instrument_invalid:
        return "STATIC_HEADROOM_INSTRUMENT_INVALID"
    maximum = primary.get(
        "true_analogy_maximum_total_absolute_error_reduction_micro"
    )
    if type(maximum) is not int:
        return "STATIC_HEADROOM_INSTRUMENT_INVALID"
    if maximum < REQUIRED_TOTAL_REDUCTION_MICRO:
        return "CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM"
    return "STATIC_REFERENCE_HEADROOM_FEASIBLE"


def authority_receipts() -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for relative, expected in sorted(R5_AUTHORITY.items()):
        actual = file_sha256(REPO_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"R5 authority hash drift: {relative}: {actual}")
        receipts.append({"path": relative, "sha256": actual, "role": "normative_r5"})
    for relative in R6_AUTHORITY_PATHS:
        path = REPO_ROOT / relative
        receipts.append(
            {"path": relative, "sha256": file_sha256(path), "role": "r6_task_authority"}
        )
    test_path = REPO_ROOT / TEST_RELATIVE_PATH
    receipts.append(
        {
            "path": TEST_RELATIVE_PATH,
            "sha256": file_sha256(test_path),
            "role": "verification_test",
        }
    )
    return receipts


def _common_metadata() -> dict[str, Any]:
    code_path_hash = file_sha256(Path(__file__))
    inputs = authority_receipts()
    run_id = "static-headroom-" + canonical_hash(
        {"task_id": TASK_ID, "code_path_hash": code_path_hash, "inputs": inputs}
    )[:16]
    return {
        "task_id": TASK_ID,
        "producer_function": f"{PRODUCER_MODULE}.write_evidence_bundle",
        "run_id": run_id,
        "code_path_hash": code_path_hash,
        "input_artifacts": inputs,
        "aggregation_rule": AGGREGATION_RULE,
        "runtime_receipt": {
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "dtype": np.dtype(np.int64).str,
            "decision_arithmetic": "signed_integer_micro_units",
            "numpy_role": "batched_integer_arithmetic_only",
        },
    }


def _artifact_payloads() -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    common = _common_metadata()
    primary = exhaustive_result()
    crosscheck = ordered_pair_symmetry_crosscheck()
    ablation = ungated_bma_diagnostic()
    agreement = {
        "same_model_lineage": True,
        "external_independent_audit": False,
        "shared_integer_arithmetic_kernel": True,
        "crosscheck_role": "ordered_pair_symmetry_expansion_only",
        "positive_case_count_symmetry_agrees": (
            2 * primary["positive_budget2_case_count"]
            == crosscheck["positive_budget2_case_count"]
        ),
        "maximum_reduction_agrees": (
            primary["maximum_total_absolute_error_reduction_micro"]
            == crosscheck["maximum_total_absolute_error_reduction_micro"]
        ),
    }
    verdict = dispatch_verdict(primary)
    negative = verdict == "CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM"
    result = {
        "schema_version": SCHEMA_VERSION,
        **common,
        "status": (
            "bounded_negative_preimplementation_stop"
            if negative
            else "static_feasibility_return_requires_separate_implementation_card"
        ),
        "verdict": verdict,
        "hypothesis": (
            "A true-analogy-constrained six-source state can achieve at least "
            "0.021875 gated MAE improvement at feedback budget 2."
        ),
        "fixed_signatures": fixed_signatures(),
        "primary_enumeration": primary,
        "ordered_pair_symmetry_crosscheck": crosscheck,
        "agreement": agreement,
        "claim_ceiling": (
            "Complete seed-free finite feasibility adjudication of the exact "
            "frozen R5 budget-2 lower-5pct transfer gate only."
        ),
    }
    baseline = {
        "schema_version": f"{SCHEMA_VERSION}.baseline",
        **common,
        "baseline_id": "STRUCTURE_MATCHED_SCRATCH_BAYES",
        "candidate_id": "FROZEN_R5_TRANSFER_BMA_WITH_LOWER_5PCT_GATE",
        "feedback_budget": 2,
        "scratch_support_after_two_distinct_rows": 6,
        "candidate_nontrivial_gate_use_count": primary[
            "nontrivial_transfer_gate_use_count"
        ],
        "candidate_maximum_mae_improvement": primary["maximum_mae_improvement"],
        "true_analogy_candidate_maximum_mae_improvement": primary[
            "true_analogy_maximum_mae_improvement"
        ],
        "required_mae_improvement": primary["required_mae_improvement"],
        "baseline_equivalence": (
            primary["nontrivial_transfer_gate_use_count"] == 0
            and primary["maximum_total_absolute_error_reduction_micro"] == 0
        ),
    }
    ablation_report = {
        "schema_version": f"{SCHEMA_VERSION}.ablation",
        **common,
        "normative_gate_enabled": {
            "positive_case_count": primary["positive_budget2_case_count"],
            "nontrivial_gate_use_count": primary[
                "nontrivial_transfer_gate_use_count"
            ],
            "maximum_total_absolute_error_reduction_micro": primary[
                "maximum_total_absolute_error_reduction_micro"
            ],
        },
        "gate_deleted_diagnostic": ablation,
        "may_rescue_verdict": False,
    }
    failures = (
        [
            {
                "code": "FROZEN_LOWER_5PCT_GATE_COLLAPSES_TO_SCRATCH_AT_BUDGET_2",
                "verdict": verdict,
                "evidence": {
                    "global_positive_cases": primary["positive_budget2_case_count"],
                    "true_analogy_positive_cases": primary[
                        "true_analogy_positive_budget2_case_count"
                    ],
                    "maximum_mae_improvement": primary["maximum_mae_improvement"],
                    "required_mae_improvement": primary["required_mae_improvement"],
                },
            }
        ]
        if negative
        else []
    )
    failure = {
        "schema_version": f"{SCHEMA_VERSION}.failure_manifest",
        **common,
        "failure_count": len(failures),
        "failures": failures,
        "forbidden_next_actions": (
            [
                "implement_the_frozen_r5_product_path",
                "run_source_or_development_or_heldout_seeds",
                "retune_quantile_prior_budget_or_threshold_under_r6",
                "claim_general_transfer_or_causal_schema_failure",
            ]
            if negative
            else [
                "run_source_or_development_or_heldout_seeds_without_a_separate_card",
                "claim_transfer_or_controller_path_effect_from_static_feasibility",
            ]
        ),
        "allowed_next_action": (
            "prospective_decision_rule_redesign_under_a_separate_frozen_task_card"
            if negative
            else "return_to_a_separate_frozen_product_path_implementation_card"
        ),
    }
    trace = [
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "authority_and_fixed_signatures",
            "fixed_signatures": fixed_signatures(),
        },
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "complete_finite_coverage",
            "coverage": {
                "per_source_vectors": primary["per_source_vector_count"],
                "six_source_states": primary[
                    "attainable_six_source_state_count"
                ],
                "target_mappings": primary["covered_target_mapping_count"],
                "primary_cases": primary["evaluated_prior_target_case_count"],
                "true_analogy_cases": primary["true_analogy_evaluated_case_count"],
                "ordered_pair_crosscheck_cases": crosscheck[
                    "evaluated_prior_target_case_count"
                ],
            },
        },
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "verdict_inputs",
            "primary": primary,
            "ordered_pair_symmetry_crosscheck": crosscheck,
            "agreement": agreement,
        },
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "gate_deletion_diagnostic",
            "ablation": ablation,
        },
    ]
    adjudication = "infeasibility" if negative else "feasibility"
    claim = (
        f"Bounded claim only: complete seed-free mathematical {adjudication} "
        "adjudication of the exact frozen R5 feedback-budget-2 lower-5% transfer "
        "gate. This does not prove transfer learning, causal-schema induction, "
        "neural emergence, survival benefit, AGI, agency, consciousness, "
        "subjectivity, or electronic life.\n"
    )
    payloads = {
        "result.json": result,
        "baseline_comparison.json": baseline,
        "ablation_report.json": ablation_report,
        "failure_manifest.json": failure,
    }
    return payloads, trace, claim


def _serialized_core(
    payloads: Mapping[str, Mapping[str, Any]],
    trace: Sequence[Mapping[str, Any]],
    claim: str,
) -> dict[str, bytes]:
    serialized = {
        name: json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8")
        + b"\n"
        for name, value in payloads.items()
    }
    serialized["trace.jsonl"] = b"".join(canonical_bytes(row) + b"\n" for row in trace)
    serialized["claim_ceiling.txt"] = claim.encode("utf-8")
    return serialized


def write_evidence_bundle(
    output_dir: Path, *, replay_expected_dir: Path | None = None
) -> dict[str, Any]:
    clear_computation_caches()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads, trace, claim = _artifact_payloads()
    first_serialized = _serialized_core(payloads, trace, claim)
    actual_hashes = {
        name: sha256(content).hexdigest()
        for name, content in sorted(first_serialized.items())
    }

    expected_hashes: dict[str, str]
    comparison_mode: str
    if replay_expected_dir is None:
        expected_hashes = dict(actual_hashes)
        agreement = payloads["result.json"]["agreement"]
        recomputed_equal = bool(
            agreement["positive_case_count_symmetry_agrees"]
            and agreement["maximum_reduction_agrees"]
        )
        comparison_mode = "primary_plus_ordered_pair_symmetry_crosscheck"
    else:
        replay_expected_dir = Path(replay_expected_dir)
        expected_hashes = {
            name: sha256((replay_expected_dir / name).read_bytes()).hexdigest()
            for name in sorted(first_serialized)
        }
        recomputed_equal = expected_hashes == actual_hashes
        comparison_mode = "fresh_process_recompute_then_external_bundle_readback"
    common = _common_metadata()
    replay_report = {
        "schema_version": f"{SCHEMA_VERSION}.replay",
        **common,
        "comparison_mode": comparison_mode,
        "stored_outputs_used_as_enumeration_inputs": False,
        "same_model_lineage": True,
        "external_independent_audit": False,
        "expected_core_file_sha256": expected_hashes,
        "recomputed_core_file_sha256": actual_hashes,
        "recomputed_equal": recomputed_equal,
        "primary_symmetry_crosscheck_agreement": payloads["result.json"][
            "agreement"
        ],
    }
    if not recomputed_equal:
        raise AssertionError("replay bundle does not match fresh recomputation")

    for name, content in first_serialized.items():
        (output_dir / name).write_bytes(content)
    (output_dir / "replay_report.json").write_text(
        json.dumps(replay_report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    result = payloads["result.json"]
    return {
        "result": result,
        "result_sha256": canonical_hash(result),
        "replay_report": replay_report,
        "output_files": sorted(
            [*first_serialized, "replay_report.json"]
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--replay",
        type=Path,
        default=None,
        help="compare a fresh recomputation with a prior evidence directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = write_evidence_bundle(
        args.output_dir, replay_expected_dir=args.replay
    )
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "verdict": bundle["result"]["verdict"],
                "result_sha256": bundle["result_sha256"],
                "output_files": bundle["output_files"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
