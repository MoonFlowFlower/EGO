#!/usr/bin/env python3
"""Exact public-action feasibility verifier for frozen conservative-transfer R7.

The verifier is seed/world/source-bank free. It proves a universal action-set
boundary using only frozen anonymous prototype geometry and exact Python-int L1
arithmetic. It is not a product controller or a learned transfer mechanism.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
from itertools import combinations, permutations
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Mapping, Sequence


TASK_ID = "EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7"
SCHEMA_VERSION = "ego.v2.conservative_transfer.public_action_feasibility.v1"
PRODUCER_MODULE = (
    "check_ego_v2_conservative_transfer_public_action_feasibility_001c_r7"
)
AGGREGATION_RULE = (
    "exact_loss_geometry_quotient_over_10_remaining_sets_6_completions_"
    "and_63_nonempty_exact_member_masks"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / TASK_ID
PRODUCER_RELATIVE_PATH = (
    "scripts/codex/"
    "check_ego_v2_conservative_transfer_public_action_feasibility_001c_r7.py"
)
PHASE_A_COMMIT = "682c1debb271a2b34c20a9c5822ecea78f16bd3b"
PARENT_DESIGN_COMMIT = "ed0902c686cb60b189bce8944d17f5e84a62b3ff"

PARENT_CARD = (
    "docs/codex/tasks/"
    "EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7.md"
)
PARENT_COLLISION = (
    "docs/codex/tasks/"
    "ego-v2-p1-conservative-transfer-public-action-feasibility-001c-r7/"
    "COLLISION_RECORD.md"
)
PARENT_DESIGN = (
    "docs/codex/tasks/"
    "ego-v2-p1-conservative-transfer-public-action-feasibility-001c-r7/"
    "FROZEN_DESIGN.json"
)
IMPLEMENTATION_CARD = (
    "docs/codex/tasks/"
    "EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-"
    "IMPLEMENTATION-001C-R7-I1.md"
)
TEST_RELATIVE_PATH = (
    "scripts/codex/tests/"
    "test_check_ego_v2_conservative_transfer_public_action_feasibility_001c_r7.py"
)

FIXED_AUTHORITIES = (
    (
        PARENT_CARD,
        "4dc267bde27b3caf39f495026891990779f7b4376abf6a380149bd2537a63f92",
        "r7_parent_card",
    ),
    (
        PARENT_COLLISION,
        "c50e372966750e0f4d67edde22535c4fbf349f8cea6b741b1eca6b3923cd57a2",
        "r7_parent_collision",
    ),
    (
        PARENT_DESIGN,
        "1009c951fca9cf2982f6e2ac82550aa8b979e3ef3534eac29858219e5bb8c7e8",
        "r7_parent_design",
    ),
    (
        IMPLEMENTATION_CARD,
        "cb452ccb9408547f99e7ef62dd286dffcae5e60ccfda07c225b9129a71d672ab",
        "r7_implementation_card",
    ),
)

MICRO = 1_000_000
TRUE_GAIN_THRESHOLD_MICRO = 437_500
STRICT_NONMEMBER_REGRET_MICRO = 0
BOUNDED_NONMEMBER_REGRET_MICRO = 87_500
COMPLETION_COUNT = 6


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _run_git(arguments: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError("git external provenance tool unavailable") from exc
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed


def validate_git_runtime(*, version: str, repository_root: Path) -> dict[str, str]:
    if not version.startswith("git version "):
        raise RuntimeError("git version receipt invalid")
    if Path(repository_root).resolve() != REPO_ROOT.resolve():
        raise RuntimeError("git repository root mismatch")
    return {
        "name": "git",
        "version": version,
        "repository_root": str(Path(repository_root).resolve()),
        "role": "external_provenance_tool_only",
    }


def git_runtime_receipt() -> dict[str, str]:
    version = _run_git(["--version"]).stdout.strip()
    repository_root = Path(
        _run_git(["rev-parse", "--show-toplevel"]).stdout.strip()
    )
    return validate_git_runtime(
        version=version, repository_root=repository_root
    )


def _normalized_status_paths() -> set[str]:
    completed = _run_git(["status", "--porcelain=v1", "--untracked-files=all"])
    paths: set[str] = set()
    for line in completed.stdout.splitlines():
        if len(line) < 4:
            raise RuntimeError("malformed git status line")
        value = line[3:].replace("\\", "/")
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.add(value)
    return paths


def evaluate_provenance_state(
    *,
    phase_a_is_ancestor: bool,
    cumulative_diff_paths: set[str],
    dirty_paths: set[str],
    sources_tracked_and_match_head: bool,
    replay_expected_artifact_paths: set[str],
) -> dict[str, Any]:
    required_source_paths = {
        IMPLEMENTATION_CARD,
        PRODUCER_RELATIVE_PATH,
        TEST_RELATIVE_PATH,
    }
    allowed_cumulative_paths = required_source_paths | {
        f"{ARTIFACT_RELATIVE_ROOT}/{name}" for name in OUTPUT_FILE_NAMES
    }
    failures: list[str] = []
    if not phase_a_is_ancestor:
        failures.append("phase_A_commit_is_not_ancestor")
    if not required_source_paths.issubset(cumulative_diff_paths):
        failures.append("required_source_lineage_paths_missing")
    if not cumulative_diff_paths.issubset(allowed_cumulative_paths):
        failures.append("cumulative_diff_outside_allowlist")
    if not sources_tracked_and_match_head:
        failures.append("source_bytes_not_tracked_clean_HEAD")
    if not dirty_paths.issubset(replay_expected_artifact_paths):
        failures.append("dirty_paths_outside_replay_artifact_allowlist")
    return {
        "formal_eligible": not failures,
        "failure_codes": failures,
        "phase_a_is_ancestor": phase_a_is_ancestor,
        "required_source_lineage_present": required_source_paths.issubset(
            cumulative_diff_paths
        ),
        "cumulative_diff_within_allowlist": cumulative_diff_paths.issubset(
            allowed_cumulative_paths
        ),
        "sources_tracked_and_match_head": sources_tracked_and_match_head,
        "nonartifact_dirty_path_count": len(
            dirty_paths - replay_expected_artifact_paths
        ),
    }


def source_provenance_receipt(
    *, replay_expected_dir: Path | None = None
) -> dict[str, Any]:
    head = _run_git(["rev-parse", "HEAD"]).stdout.strip()
    phase_a_ancestor = (
        _run_git(
            ["merge-base", "--is-ancestor", PHASE_A_COMMIT, head], check=False
        ).returncode
        == 0
    )
    cumulative = {
        line.replace("\\", "/")
        for line in _run_git(
            ["diff", "--name-only", f"{PARENT_DESIGN_COMMIT}..{head}"]
        ).stdout.splitlines()
        if line
    }
    tracked_and_clean = True
    for relative in (PRODUCER_RELATIVE_PATH, TEST_RELATIVE_PATH):
        tracked = _run_git(["ls-files", "--error-unmatch", relative], check=False)
        clean = _run_git(["diff", "--quiet", "HEAD", "--", relative], check=False)
        tracked_and_clean = (
            tracked_and_clean and tracked.returncode == 0 and clean.returncode == 0
        )
    dirty = _normalized_status_paths()
    replay_artifacts: set[str] = set()
    if replay_expected_dir is not None:
        try:
            relative_expected = Path(replay_expected_dir).resolve().relative_to(
                REPO_ROOT.resolve()
            )
        except ValueError:
            relative_expected = None
        if relative_expected is not None:
            root = relative_expected.as_posix()
            replay_artifacts = {f"{root}/{name}" for name in OUTPUT_FILE_NAMES}
    evaluated = evaluate_provenance_state(
        phase_a_is_ancestor=phase_a_ancestor,
        cumulative_diff_paths=cumulative,
        dirty_paths=dirty,
        sources_tracked_and_match_head=tracked_and_clean,
        replay_expected_artifact_paths=replay_artifacts,
    )
    source_commit_result = _run_git(
        [
            "log",
            "-1",
            "--format=%H",
            "--",
            PRODUCER_RELATIVE_PATH,
            TEST_RELATIVE_PATH,
        ],
        check=False,
    )
    return {
        **evaluated,
        "phase_a_commit": PHASE_A_COMMIT,
        "parent_design_commit": PARENT_DESIGN_COMMIT,
        "current_head": head,
        "source_commit": source_commit_result.stdout.strip() or None,
        "cumulative_diff_paths": sorted(cumulative),
        "dynamic_source_hash_policy": (
            "tracked_worktree_bytes_must_match_HEAD_no_self_expected_SHA_literal"
        ),
    }


def _load_frozen_design() -> dict[str, Any]:
    value = json.loads((REPO_ROOT / PARENT_DESIGN).read_text(encoding="utf-8"))
    if value.get("task_id") != TASK_ID:
        raise RuntimeError("R7 frozen design task id drift")
    return value


_DESIGN = _load_frozen_design()
PROTOTYPE_BYTES = tuple(
    value.encode("ascii")
    for value in _DESIGN["public_information"]["prototype_canonical_json"]
)
PROTOTYPE_HASHES = tuple(
    _DESIGN["public_information"]["prototype_sha256"]
)
CORE_FILE_NAMES = tuple(_DESIGN["trace_replay"]["core_files"])
OUTPUT_FILE_NAMES = frozenset((*CORE_FILE_NAMES, "replay_report.json"))
ARTIFACT_RELATIVE_ROOT = f"artifacts/{TASK_ID}"


def _prototype_micro_units() -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for raw in PROTOTYPE_BYTES:
        values = json.loads(raw.decode("ascii"), parse_float=Decimal)
        if not isinstance(values, list) or len(values) != 4:
            raise RuntimeError("prototype shape drift")
        row: list[int] = []
        for value in values:
            decimal_value = value if isinstance(value, Decimal) else Decimal(value)
            scaled = decimal_value * MICRO
            if scaled != scaled.to_integral_value():
                raise RuntimeError("prototype is not exact at micro-unit scale")
            row.append(int(scaled))
        rows.append(tuple(row))
    return tuple(rows)


PROTOTYPES = _prototype_micro_units()


def authority_receipts() -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for relative, expected, role in FIXED_AUTHORITIES:
        actual = file_sha256(REPO_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"authority hash drift: {relative}: {actual}")
        receipts.append({"path": relative, "sha256": actual, "role": role})
    for relative, role in (
        (PRODUCER_RELATIVE_PATH, "producer"),
        (TEST_RELATIVE_PATH, "verification_test"),
    ):
        path = REPO_ROOT / relative
        receipts.append(
            {"path": relative, "sha256": file_sha256(path), "role": role}
        )
    return receipts


def fixed_signatures() -> dict[str, Any]:
    hashes = tuple(sha256(raw).hexdigest() for raw in PROTOTYPE_BYTES)
    if hashes != PROTOTYPE_HASHES:
        raise RuntimeError("prototype byte hash drift")
    if PROTOTYPES != _prototype_micro_units():
        raise RuntimeError("prototype decode drift")
    if len(PROTOTYPES) != 5 or any(len(row) != 4 for row in PROTOTYPES):
        raise RuntimeError("prototype grammar drift")
    return {
        "prototype_canonical_json": [raw.decode("ascii") for raw in PROTOTYPE_BYTES],
        "prototype_sha256": list(hashes),
        "prototype_micro_units": [list(row) for row in PROTOTYPES],
        "prototype_count": len(PROTOTYPES),
        "component_count": len(PROTOTYPES[0]),
    }


def round_half_even(numerator: int, denominator: int) -> int:
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("integer numerator and positive integer denominator required")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if 2 * remainder > denominator or (
        2 * remainder == denominator and quotient % 2 == 1
    ):
        quotient += 1
    return sign * quotient


def remaining_sets() -> tuple[tuple[int, int, int], ...]:
    result = tuple(combinations(range(len(PROTOTYPES)), 3))
    if len(result) != 10:
        raise RuntimeError("remaining-set grammar drift")
    return result


def unique_scalar_median_certificate(values: Sequence[int]) -> dict[str, Any]:
    if len(values) != 3 or any(type(value) is not int for value in values):
        raise ValueError("exactly three integer scalar values required")
    ordered = tuple(sorted(values))
    median = ordered[1]
    base = sum(abs(median - value) for value in ordered)
    left = sum(abs((median - 1) - value) for value in ordered)
    right = sum(abs((median + 1) - value) for value in ordered)
    unique = left > base and right > base
    return {
        "ordered_values": list(ordered),
        "median": median,
        "objective_at_median": base,
        "left_unit_gap": left - base,
        "right_unit_gap": right - base,
        "unique": unique,
        "outside_interval_monotonic": True,
    }


def public_median_action(
    remaining: Sequence[int],
) -> tuple[tuple[int, ...], ...]:
    if len(remaining) != 3 or len(set(remaining)) != 3:
        raise ValueError("three distinct remaining prototypes required")
    vector = tuple(
        sorted(PROTOTYPES[index][component] for index in remaining)[1]
        for component in range(4)
    )
    return (vector, vector, vector)


def public_mean_action(
    remaining: Sequence[int],
) -> tuple[tuple[int, ...], ...]:
    if len(remaining) != 3 or len(set(remaining)) != 3:
        raise ValueError("three distinct remaining prototypes required")
    vector = tuple(
        round_half_even(
            sum(PROTOTYPES[index][component] for index in remaining), 3
        )
        for component in range(4)
    )
    return (vector, vector, vector)


def completion_loss(
    action: Sequence[Sequence[int]], truth: Sequence[int]
) -> int:
    if len(action) != 3 or len(truth) != 3:
        raise ValueError("three-token action and truth required")
    total = 0
    for token in range(3):
        if len(action[token]) != 4:
            raise ValueError("each action vector must have four components")
        prototype = PROTOTYPES[truth[token]]
        total += sum(
            abs(int(action[token][component]) - prototype[component])
            for component in range(4)
        )
    return total


def factored_loss_sum(
    action: Sequence[Sequence[int]], remaining: Sequence[int]
) -> int:
    if len(action) != 3 or len(remaining) != 3:
        raise ValueError("three-token action and remaining set required")
    return 2 * sum(
        sum(
            abs(int(action[token][component]) - PROTOTYPES[index][component])
            for component in range(4)
        )
        for token in range(3)
        for index in remaining
    )


def completion_multiplicity(
    remaining: Sequence[int],
) -> tuple[tuple[int, ...], ...]:
    completions = tuple(permutations(remaining))
    return tuple(
        tuple(sum(truth[token] == index for truth in completions) for index in remaining)
        for token in range(3)
    )


def geometry_receipts() -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for remaining in remaining_sets():
        completions = tuple(permutations(remaining))
        median_action = public_median_action(remaining)
        mean_action = public_mean_action(remaining)
        median_losses = [completion_loss(median_action, truth) for truth in completions]
        mean_losses = [completion_loss(mean_action, truth) for truth in completions]
        explicit_sum = sum(median_losses)
        factored_sum = factored_loss_sum(median_action, remaining)
        scalar_certificates = [
            unique_scalar_median_certificate(
                tuple(PROTOTYPES[index][component] for index in remaining)
            )
            for component in range(4)
        ]
        multiplicity = completion_multiplicity(remaining)
        multiplicity_two = all(
            value == 2 for row in multiplicity for value in row
        )
        witness_action = tuple(
            tuple(
                PROTOTYPES[remaining[(token + 1) % 3]][component]
                + (token + 1) * (component + 1)
                for component in range(4)
            )
            for token in range(3)
        )
        witness_explicit = sum(
            completion_loss(witness_action, truth) for truth in completions
        )
        witness_factored = factored_loss_sum(witness_action, remaining)
        universal_identity = multiplicity_two and witness_explicit == witness_factored
        constant_loss = len(set(median_losses)) == 1
        median_unique = all(row["unique"] for row in scalar_certificates)
        receipts.append(
            {
                "remaining_prototypes": list(remaining),
                "completion_count": len(completions),
                "completion_multiplicity": [list(row) for row in multiplicity],
                "median_action_micro": [list(row) for row in median_action],
                "mean_action_micro": [list(row) for row in mean_action],
                "median_completion_losses_micro": median_losses,
                "mean_completion_losses_micro": mean_losses,
                "median_explicit_loss_sum_micro": explicit_sum,
                "median_factored_loss_sum_micro": factored_sum,
                "loss_sum_identity_holds": explicit_sum == factored_sum,
                "universal_loss_sum_identity_valid": universal_identity,
                "universal_identity_receipt": {
                    "all_token_prototype_multiplicities_equal_two": multiplicity_two,
                    "arbitrary_action_explicit_loss_sum_micro": witness_explicit,
                    "arbitrary_action_factored_loss_sum_micro": witness_factored,
                    "arbitrary_action_crosscheck_equal": (
                        witness_explicit == witness_factored
                    ),
                    "symbolic_basis": (
                        "each_token_prototype_pair_occurs_exactly_twice_across_"
                        "all_six_permutations"
                    ),
                },
                "median_is_unique": median_unique,
                "median_loss_constant_over_completions": constant_loss,
                "median_is_minimax": (
                    median_unique and constant_loss and universal_identity
                ),
                "mean_aggregate_excess_error_micro": sum(mean_losses) - explicit_sum,
                "scalar_median_certificates": scalar_certificates,
            }
        )
    return receipts


def randomized_extension_receipt(
    geometries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    deterministic_lower_bound = bool(
        geometries
        and all(
            row.get("universal_loss_sum_identity_valid")
            and row.get("median_is_unique")
            and row.get("median_is_minimax")
            for row in geometries
        )
    )
    unique_equality = bool(
        geometries and all(row.get("median_is_unique") for row in geometries)
    )
    finite_aligned_completion_sets = bool(
        geometries
        and all(row.get("completion_count") == COMPLETION_COUNT for row in geometries)
    )
    expectation_linearity = (
        deterministic_lower_bound and finite_aligned_completion_sets
    )
    return {
        "deterministic_lower_bound_valid": deterministic_lower_bound,
        "unique_equality_condition_valid": unique_equality,
        "expectation_linearity_valid": expectation_linearity,
        "equality_requires_public_median_almost_surely": (
            unique_equality and expectation_linearity
        ),
        "randomized_extension_valid": (
            deterministic_lower_bound
            and unique_equality
            and expectation_linearity
        ),
        "derivation": (
            "take_expectation_of_each_deterministic_loss_sum_inequality_and_"
            "use_unique_equality_condition"
        ),
    }


def _bound_receipt(
    *, membership_size: int, true_gain_micro: int, nonmember_margin_micro: int
) -> dict[str, Any]:
    if not (1 <= membership_size <= 6):
        raise ValueError("membership size must be in 1..6")
    if true_gain_micro < 0 or nonmember_margin_micro < 0:
        raise ValueError("gain and margin must be nonnegative")
    upper = (
        -membership_size * true_gain_micro
        + (COMPLETION_COUNT - membership_size) * nonmember_margin_micro
    )
    if upper < 0:
        status = "infeasible"
        reason = "constraint_sum_below_public_L1_lower_bound"
    elif upper == 0 and true_gain_micro > 0:
        status = "infeasible"
        reason = "unique_equality_forces_A_equals_B_and_zero_true_gain"
    elif true_gain_micro == 0:
        status = "feasible_witness"
        reason = "public_L1_action_is_exact_witness"
    else:
        status = "inconclusive"
        reason = "loss_sum_bound_not_decisive_without_witness"
    return {
        "constraint_sum_upper_micro": upper,
        "status": status,
        "feasible": status == "feasible_witness",
        "reason": reason,
    }


def formal_feasibility_summary() -> dict[str, Any]:
    geometries = remaining_sets()
    membership_counts = {str(k): 0 for k in range(1, 7)}
    strict_count = 0
    bounded_count = 0
    strict_inconclusive = 0
    bounded_inconclusive = 0
    inconclusive_masks = 0
    evaluated = 0
    for _remaining in geometries:
        for mask in range(1, 1 << COMPLETION_COUNT):
            size = mask.bit_count()
            membership_counts[str(size)] += 1
            strict = _bound_receipt(
                membership_size=size,
                true_gain_micro=TRUE_GAIN_THRESHOLD_MICRO,
                nonmember_margin_micro=STRICT_NONMEMBER_REGRET_MICRO,
            )
            bounded = _bound_receipt(
                membership_size=size,
                true_gain_micro=TRUE_GAIN_THRESHOLD_MICRO,
                nonmember_margin_micro=BOUNDED_NONMEMBER_REGRET_MICRO,
            )
            strict_count += int(strict["status"] == "feasible_witness")
            bounded_count += int(bounded["status"] == "feasible_witness")
            strict_inconclusive += int(strict["status"] == "inconclusive")
            bounded_inconclusive += int(bounded["status"] == "inconclusive")
            inconclusive_masks += int(
                strict["status"] == "inconclusive"
                or bounded["status"] == "inconclusive"
            )
            evaluated += 1

    bounds: dict[str, Any] = {}
    for size in range(1, 7):
        strict = _bound_receipt(
            membership_size=size,
            true_gain_micro=TRUE_GAIN_THRESHOLD_MICRO,
            nonmember_margin_micro=STRICT_NONMEMBER_REGRET_MICRO,
        )
        bounded = _bound_receipt(
            membership_size=size,
            true_gain_micro=TRUE_GAIN_THRESHOLD_MICRO,
            nonmember_margin_micro=BOUNDED_NONMEMBER_REGRET_MICRO,
        )
        bounds[str(size)] = {
            "strict_constraint_sum_upper_micro": strict["constraint_sum_upper_micro"],
            "strict_infeasibility_reason": strict["reason"],
            "bounded_constraint_sum_upper_micro": bounded[
                "constraint_sum_upper_micro"
            ],
            "bounded_infeasibility_reason": bounded["reason"],
        }
    return {
        "loss_geometry_count": len(geometries),
        "completion_count_per_geometry": COMPLETION_COUNT,
        "nonempty_mask_count_per_geometry": (1 << COMPLETION_COUNT) - 1,
        "evaluated_geometry_mask_count": evaluated,
        "membership_size_case_counts": membership_counts,
        "strict_feasible_mask_count": strict_count,
        "bounded_feasible_mask_count": bounded_count,
        "strict_inconclusive_mask_count": strict_inconclusive,
        "bounded_inconclusive_mask_count": bounded_inconclusive,
        "inconclusive_mask_count": inconclusive_masks,
        "bounds_by_membership_size": bounds,
        "universal_quantifier": "for_every_B_H2_M_of_B_H2_and_A_of_B_H2",
    }


def zero_gain_positive_control(
    *, remaining: Sequence[int], mask: int
) -> dict[str, Any]:
    completions = tuple(permutations(remaining))
    if mask <= 0 or mask >= 1 << len(completions):
        raise ValueError("nonempty six-completion mask required")
    action = public_median_action(remaining)
    baseline_losses = [completion_loss(action, truth) for truth in completions]
    action_losses = [completion_loss(action, truth) for truth in completions]
    benefits = [base - observed for base, observed in zip(baseline_losses, action_losses)]
    strict_feasible = all(
        benefit >= 0 if mask & (1 << index) else -benefit <= 0
        for index, benefit in enumerate(benefits)
    )
    dispatch_summary = {
        "strict_feasible_mask_count": int(strict_feasible),
        "bounded_feasible_mask_count": int(strict_feasible),
        "inconclusive_mask_count": 0,
    }
    return {
        "remaining_prototypes": list(remaining),
        "mask": mask,
        "true_gain_threshold_micro": 0,
        "action_equals_public_median": action == public_median_action(remaining),
        "truth_benefits_micro": benefits,
        "strict_feasible": strict_feasible,
        "dispatch_summary": dispatch_summary,
    }


def dispatch_verdict(
    summary: Mapping[str, Any],
    *,
    private_truth_or_seed_input: bool = False,
    instrument_invalid: bool = False,
) -> str:
    if private_truth_or_seed_input:
        return "PRIVATE_TRUTH_OR_SEED_INPUT"
    if instrument_invalid:
        return "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    strict = summary.get("strict_feasible_mask_count")
    bounded = summary.get("bounded_feasible_mask_count")
    inconclusive = summary.get("inconclusive_mask_count", 0)
    if (
        type(strict) is not int
        or type(bounded) is not int
        or strict < 0
        or bounded < 0
        or strict > bounded
        or type(inconclusive) is not int
        or inconclusive < 0
    ):
        return "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    if inconclusive > 0:
        return "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    if strict > 0:
        return "R7_STATIC_REFERENCE_FEASIBLE"
    if bounded > 0:
        return "BOUNDED_REGRET_ONLY"
    return "PUBLIC_INFORMATION_TWO_SIDED_HEADROOM_ABSENT"


def relabel_invariance_receipt() -> dict[str, Any]:
    observed_order_complements = [
        tuple(index for index in range(5) if index not in observed)
        for observed in permutations(range(5), 2)
    ]
    observed_order_invariant = (
        set(observed_order_complements) == set(remaining_sets())
        and all(observed_order_complements.count(row) == 2 for row in remaining_sets())
    )

    remaining = (0, 2, 4)
    action = (
        (11, 22, 33, 44),
        (55, 66, 77, 88),
        (99, 111, 222, 333),
    )
    base_losses = sorted(
        completion_loss(action, truth) for truth in permutations(remaining)
    )
    token_invariant = True
    for token_order in permutations(range(3)):
        permuted_action = tuple(action[index] for index in token_order)
        losses = sorted(
            completion_loss(permuted_action, truth)
            for truth in permutations(remaining)
        )
        token_invariant = token_invariant and losses == base_losses

    label_order = (4, 3, 2, 1, 0)
    inverse = {old: new for new, old in enumerate(label_order)}
    relabelled_prototypes = tuple(PROTOTYPES[old] for old in label_order)
    prototype_invariant = True
    for truth in permutations(remaining):
        relabelled_truth = tuple(inverse[index] for index in truth)
        direct = completion_loss(action, truth)
        relabelled = sum(
            sum(
                abs(action[token][component] - relabelled_prototypes[index][component])
                for component in range(4)
            )
            for token, index in enumerate(relabelled_truth)
        )
        prototype_invariant = prototype_invariant and direct == relabelled

    return {
        "observed_order_invariant": observed_order_invariant,
        "unobserved_token_relabel_invariant": token_invariant,
        "prototype_relabel_invariant": prototype_invariant,
        "geometry_quotient_complete": observed_order_invariant
        and len(remaining_sets()) == 10,
        "universal_bank_and_action_quantifier": (
            "for_every_B_H2_M_of_B_H2_and_A_of_B_H2"
        ),
    }


def _common_metadata(
    *, replay_expected_dir: Path | None = None
) -> dict[str, Any]:
    receipts = authority_receipts()
    provenance = source_provenance_receipt(
        replay_expected_dir=replay_expected_dir
    )
    git_runtime = git_runtime_receipt()
    code_hash = next(row["sha256"] for row in receipts if row["role"] == "producer")
    run_id = "public-action-r7-" + canonical_hash(
        {
            "task_id": TASK_ID,
            "code_path_hash": code_hash,
            "inputs": receipts,
            "source_provenance": provenance,
            "git_runtime": git_runtime,
        }
    )[:16]
    return {
        "task_id": TASK_ID,
        "producer_function": f"{PRODUCER_MODULE}.write_evidence_bundle",
        "aggregation_rule": AGGREGATION_RULE,
        "run_id": run_id,
        "code_path_hash": code_hash,
        "input_artifacts": receipts,
        "source_provenance": provenance,
        "external_provenance_tool": git_runtime,
        "runtime_receipt": {
            "python_implementation": platform.python_implementation(),
            "python_version": sys.version.split()[0],
            "python_dependency_policy": "Python standard library only",
            "external_executable_dependency": "git for provenance gate only",
            "decision_dtype": "unbounded Python int",
            "floating_verdict_arithmetic": False,
        },
    }


def _artifact_payloads(
    *, replay_expected_dir: Path | None = None
) -> tuple[dict[str, Mapping[str, Any]], list[dict[str, Any]], str]:
    common = _common_metadata(replay_expected_dir=replay_expected_dir)
    signatures = fixed_signatures()
    geometries = geometry_receipts()
    formal = formal_feasibility_summary()
    relabel = relabel_invariance_receipt()
    randomized = randomized_extension_receipt(geometries)
    control = zero_gain_positive_control(remaining=(0, 1, 2), mask=1)
    proof_certificate_valid = bool(
        len(geometries) == 10
        and all(
            row["loss_sum_identity_holds"]
            and row["universal_loss_sum_identity_valid"]
            and row["median_is_unique"]
            and row["median_is_minimax"]
            for row in geometries
        )
        and all(
            relabel[key]
            for key in (
                "observed_order_invariant",
                "unobserved_token_relabel_invariant",
                "prototype_relabel_invariant",
                "geometry_quotient_complete",
            )
        )
        and formal["evaluated_geometry_mask_count"] == 630
        and formal["inconclusive_mask_count"] == 0
        and randomized["randomized_extension_valid"]
    )
    verdict = dispatch_verdict(
        formal, instrument_invalid=not proof_certificate_valid
    )
    negative = verdict == "PUBLIC_INFORMATION_TWO_SIDED_HEADROOM_ABSENT"
    invalid = verdict == "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"

    result = {
        "schema_version": SCHEMA_VERSION,
        **common,
        "status": (
            "instrument_invalid_stop"
            if invalid
            else (
                "bounded_negative_static_preimplementation_stop"
                if negative
                else "static_feasibility_requires_separate_successor_card"
            )
        ),
        "verdict": verdict,
        "hypothesis": (
            "A target-truth-blind public action can give every exact-member "
            "completion at least 437500 total-error-micro benefit while every "
            "nonmember completion has regret at most 0 or 87500."
        ),
        "fixed_signatures": signatures,
        "formal_feasibility": formal,
        "proof_certificate_valid": proof_certificate_valid,
        "geometry_receipt_hash": canonical_hash(geometries),
        "relabel_invariance": relabel,
        "randomized_extension": randomized,
        "same_model_lineage": True,
        "external_independent_audit": False,
        "claim_ceiling": (
            "Exact seed-free public-action feasibility for the universal exact-"
            "member/nonmember contract on the fixed R7 two-row geometry only."
        ),
    }
    baseline = {
        "schema_version": f"{SCHEMA_VERSION}.baseline",
        **common,
        "primary_baseline_id": "PUBLIC_PREFIX_L1_MEDIAN_MINIMAX",
        "historical_diagnostic_id": "R5_SCRATCH_POSTERIOR_MEAN",
        "geometry_count": len(geometries),
        "all_median_loss_sum_identities_hold": all(
            row["loss_sum_identity_holds"] for row in geometries
        ),
        "all_medians_unique_and_minimax": all(
            row["median_is_unique"] and row["median_is_minimax"]
            for row in geometries
        ),
        "mean_strictly_worse_geometry_count": sum(
            row["mean_aggregate_excess_error_micro"] > 0 for row in geometries
        ),
        "mean_total_aggregate_excess_error_micro": sum(
            row["mean_aggregate_excess_error_micro"] for row in geometries
        ),
        "geometry_receipts": geometries,
    }
    ablation = {
        "schema_version": f"{SCHEMA_VERSION}.ablation",
        **common,
        "mean_baseline_ablation": {
            "verdict_role": "diagnostic_only_cannot_replace_L1_baseline",
            "strictly_worse_geometry_count": baseline[
                "mean_strictly_worse_geometry_count"
            ],
            "total_aggregate_excess_error_micro": baseline[
                "mean_total_aggregate_excess_error_micro"
            ],
        },
        "zero_gain_A_equals_B_positive_control": control,
        "positive_dispatch_reached": (
            dispatch_verdict(control["dispatch_summary"])
            == "R7_STATIC_REFERENCE_FEASIBLE"
        ),
        "may_rescue_formal_verdict": False,
    }
    if not proof_certificate_valid:
        failures = [
            {
                "code": "PUBLIC_ACTION_PROOF_CERTIFICATE_INVALID",
                "verdict": verdict,
                "evidence": {
                    "geometry_count": len(geometries),
                    "all_loss_sum_identities_hold": all(
                        row["loss_sum_identity_holds"] for row in geometries
                    ),
                    "relabel_invariance": relabel,
                    "randomized_extension": randomized,
                },
            }
        ]
    elif negative:
        failures = [
            {
                "code": "UNIVERSAL_MEMBER_NONMEMBER_ACTION_INTERSECTION_EMPTY",
                "verdict": verdict,
                "evidence": {
                    "strict_feasible_mask_count": formal[
                        "strict_feasible_mask_count"
                    ],
                    "bounded_feasible_mask_count": formal[
                        "bounded_feasible_mask_count"
                    ],
                    "evaluated_geometry_mask_count": formal[
                        "evaluated_geometry_mask_count"
                    ],
                    "true_gain_threshold_total_error_micro": (
                        TRUE_GAIN_THRESHOLD_MICRO
                    ),
                    "bounded_nonmember_regret_total_error_micro": (
                        BOUNDED_NONMEMBER_REGRET_MICRO
                    ),
                },
            }
        ]
    else:
        failures = []
    failure = {
        "schema_version": f"{SCHEMA_VERSION}.failure_manifest",
        **common,
        "failure_count": len(failures),
        "failures": failures,
        "forbidden_next_actions": (
            [
                "implement_product_or_neural_selector_from_R7",
                "claim_R5_D2_D3_D4_or_distributional_impossibility",
                "run_worlds_seeds_or_pilots_without_a_separate_card",
                "retune_thresholds_or_baseline_after_R7",
            ]
            if negative or invalid
            else [
                "implement_product_or_neural_selector_without_a_separate_card",
                "claim_fresh_or_controller_path_effect_from_static_feasibility",
            ]
        ),
        "allowed_next_action": (
            "repair_the_static_proof_instrument_under_a_successor_card"
            if invalid
            else (
                "reframe_to_a_separately_frozen_active_information_or_"
                "distributional_contract"
                if negative
                else "seek_a_separate_successor_implementation_card"
            )
        ),
    }
    trace: list[dict[str, Any]] = [
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "authority_and_fixed_signatures",
            "fixed_signatures": signatures,
        }
    ]
    trace.extend(
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "loss_geometry_receipt",
            "geometry": row,
        }
        for row in geometries
    )
    trace.extend(
        {
            "schema_version": f"{SCHEMA_VERSION}.trace",
            **common,
            "event": "membership_size_bound",
            "membership_size": int(size),
            "bound": bound,
        }
        for size, bound in formal["bounds_by_membership_size"].items()
    )
    trace.extend(
        [
            {
                "schema_version": f"{SCHEMA_VERSION}.trace",
                **common,
                "event": "quotient_and_relabel_receipt",
                "receipt": relabel,
            },
            {
                "schema_version": f"{SCHEMA_VERSION}.trace",
                **common,
                "event": "verdict_inputs",
                "formal_feasibility": formal,
                "verdict": verdict,
            },
            {
                "schema_version": f"{SCHEMA_VERSION}.trace",
                **common,
                "event": "zero_gain_positive_control",
                "control": control,
            },
        ]
    )
    claim = (
        "Bounded claim only: exact seed-free public-action adjudication of the "
        "universal exact-member-benefit/nonmember-safety intersection for the "
        "fixed R7 two-row prototype geometry. This does not adjudicate R5 "
        "D2/D3/D4, local-shift, fixed-bank, distributional, active-query, "
        "controller, neural, survival, AGI, agency, consciousness, subjectivity, "
        "emotion, companion, or electronic life claims.\n"
        f"Provenance run_id={common['run_id']} "
        f"code_path_hash={common['code_path_hash']} "
        f"source_commit={common['source_provenance']['source_commit']} "
        f"formal_eligible={str(common['source_provenance']['formal_eligible']).lower()}.\n"
    )
    payloads: dict[str, Mapping[str, Any]] = {
        "result.json": result,
        "baseline_comparison.json": baseline,
        "ablation_report.json": ablation,
        "failure_manifest.json": failure,
    }
    return payloads, trace, claim


def _serialized_core(
    payloads: Mapping[str, Mapping[str, Any]],
    trace: Sequence[Mapping[str, Any]],
    claim: str,
) -> dict[str, bytes]:
    serialized = {
        name: json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True).encode(
            "utf-8"
        )
        + b"\n"
        for name, value in payloads.items()
    }
    serialized["trace.jsonl"] = b"".join(
        canonical_bytes(row) + b"\n" for row in trace
    )
    serialized["claim_ceiling.txt"] = claim.encode("utf-8")
    if set(serialized) != set(CORE_FILE_NAMES):
        raise RuntimeError("core file set drift")
    return serialized


def write_evidence_bundle(
    output_dir: Path, *, replay_expected_dir: Path | None = None
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("output directory must be empty or absent")
    payloads, trace, claim = _artifact_payloads(
        replay_expected_dir=replay_expected_dir
    )
    source_provenance = payloads["result.json"]["source_provenance"]
    if (
        output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve()
        and not source_provenance["formal_eligible"]
    ):
        raise RuntimeError(
            "canonical evidence requires clean committed source provenance"
        )
    serialized = _serialized_core(payloads, trace, claim)
    recomputed_hashes = {
        name: sha256(content).hexdigest() for name, content in sorted(serialized.items())
    }

    if replay_expected_dir is None:
        expected_hashes = dict(recomputed_hashes)
        recomputed_equal = True
        comparison_mode = "same_process_initial_core_serialization"
    else:
        expected_dir = Path(replay_expected_dir)
        expected_names = {path.name for path in expected_dir.iterdir()}
        if expected_names != set(OUTPUT_FILE_NAMES):
            raise RuntimeError("expected bundle file set drift")
        expected_hashes = {
            name: sha256((expected_dir / name).read_bytes()).hexdigest()
            for name in sorted(serialized)
        }
        recomputed_equal = expected_hashes == recomputed_hashes
        comparison_mode = "fresh_process_recompute_then_external_bundle_readback"
    if not recomputed_equal:
        raise AssertionError("fresh recomputation does not match expected core bundle")

    replay_report = {
        "schema_version": f"{SCHEMA_VERSION}.replay",
        **_common_metadata(replay_expected_dir=replay_expected_dir),
        "comparison_mode": comparison_mode,
        "core_file_names": list(CORE_FILE_NAMES),
        "expected_core_file_sha256": expected_hashes,
        "recomputed_core_file_sha256": recomputed_hashes,
        "recomputed_equal": recomputed_equal,
        "stored_verdict_action_or_witness_used_as_input": False,
        "same_model_lineage": True,
        "external_independent_audit": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in serialized.items():
        (output_dir / name).write_bytes(content)
    (output_dir / "replay_report.json").write_text(
        json.dumps(replay_report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    observed_names = {path.name for path in output_dir.iterdir()}
    if observed_names != set(OUTPUT_FILE_NAMES):
        raise RuntimeError("written bundle file set drift")
    result = payloads["result.json"]
    return {
        "result": result,
        "result_sha256": canonical_hash(result),
        "replay_report": replay_report,
        "output_files": sorted([*serialized, "replay_report.json"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--replay-expected-dir", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = write_evidence_bundle(
        args.output_dir, replay_expected_dir=args.replay_expected_dir
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
