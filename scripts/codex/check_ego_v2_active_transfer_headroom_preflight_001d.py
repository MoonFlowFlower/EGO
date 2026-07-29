from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from math import factorial, gcd
from pathlib import Path
import sys
from typing import Any


TASK_ID = 'EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D'
SCHEMA_VERSION = 'ego.v2.active_transfer_headroom_preflight.i1'
REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_RELATIVE_PATH = 'docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json'
CARD_RELATIVE_PATH = 'docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D.md'
COLLISION_RELATIVE_PATH = 'docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/COLLISION_RECORD.md'
FORMAL_ONLY_FLAGS = {'--output-dir', '--artifact-dir', '--formal', '--exhaustive', '--replay-expected-dir'}
EXPECTED_AUTHORITY = {
    CARD_RELATIVE_PATH: 'c9a7d71dcd92b0bc4571a4e5aa975e04fc97485d47b23b826894f13cac96072e',
    COLLISION_RELATIVE_PATH: '75e870cd638e58949e48ff0a3ea42101d71279196905cc461b1aa996762a0ae1',
    DESIGN_RELATIVE_PATH: 'f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916',
}


class FormalRunNotAuthorized(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _frozen_design() -> dict[str, Any]:
    # The hash-bound design is immutable process authority, not learner state.
    # Caching its parsed registry avoids tens of thousands of redundant disk
    # reads during the exact 120 x 45 callable evaluation.
    return _read_json(REPO_ROOT / DESIGN_RELATIVE_PATH)


def load_frozen_design() -> dict[str, Any]:
    # Never expose the process-cached authority object to a caller that could
    # mutate subsequent arm dispatch. Internal evaluator paths use only the
    # private cached object.
    return deepcopy(_frozen_design())


def authority_receipts() -> list[dict[str, str]]:
    rows = []
    for rel in (CARD_RELATIVE_PATH, COLLISION_RELATIVE_PATH, DESIGN_RELATIVE_PATH):
        path = REPO_ROOT / rel
        actual = _sha256(path)
        expected = EXPECTED_AUTHORITY[rel]
        rows.append(
            {
                'path': rel,
                'sha256': actual,
                'expected_sha256': expected,
                'matches_expected': actual == expected,
            }
        )
    return rows


def validate_authority_hashes() -> list[dict[str, str]]:
    receipts = authority_receipts()
    if not all(row['sha256'] == row['expected_sha256'] for row in receipts):
        raise ValueError('authority hash drift')
    return receipts


def validate_frozen_registry(design: dict) -> dict[str, int]:
    primary = design['bank_suite']['primary_role_ids']
    property_ids = tuple(design['bank_suite']['property_predicates'].keys())
    arm_records = design['arm_registry']['records']
    ablations = design['ablation_registry']['records']
    verdicts = design['verdict_dispatch']
    if len(primary) != design['bank_suite']['primary_role_count']:
        raise ValueError('primary role registry drift')
    if len(property_ids) != 4:
        raise ValueError('property role registry drift')
    if len({row['arm_id'] for row in arm_records}) != design['arm_registry']['total_count']:
        raise ValueError('arm registry drift')
    if len({row['ablation_id'] for row in ablations}) != design['ablation_registry']['count']:
        raise ValueError('ablation registry drift')
    if len(verdicts) != 11:
        raise ValueError('verdict registry drift')
    return {
        'primary_role_count': len(primary),
        'property_role_count': len(property_ids),
        'arm_count': len({row['arm_id'] for row in arm_records}),
        'ablation_count': len({row['ablation_id'] for row in ablations}),
        'verdict_count': len(verdicts),
    }


@lru_cache(maxsize=120)
def canonical_mapping_bytes(mapping: tuple[int, ...]) -> bytes:
    mapping = _validate_mapping(mapping)
    return json.dumps(list(mapping), separators=(',', ':'), ensure_ascii=True).encode('ascii')


def canonical_bank_bytes(bank: tuple[tuple[int, ...], ...]) -> bytes:
    canonical = [list(row) for row in _validate_bank(bank)]
    return json.dumps(canonical, separators=(',', ':'), ensure_ascii=True).encode('ascii')


@lru_cache(maxsize=1)
def mapping_space() -> tuple[tuple[int, ...], ...]:
    return tuple(permutations(range(5)))


def _strict_int(value: Any, *, name: str, minimum: int | None = None, maximum: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f'{name} must be an integer')
    if minimum is not None and value < minimum:
        raise ValueError(f'{name} below range')
    if maximum is not None and value > maximum:
        raise ValueError(f'{name} above range')
    return value


def _validate_mapping(mapping) -> tuple[int, ...]:
    if not isinstance(mapping, (list, tuple)) or len(mapping) != 5:
        raise ValueError('mapping shape drift')
    row = tuple(_strict_int(value, name='prototype index', minimum=0, maximum=4) for value in mapping)
    if tuple(sorted(row)) != (0, 1, 2, 3, 4):
        raise ValueError('mapping must be a permutation')
    return row


def _validate_bank(bank) -> tuple[tuple[int, ...], ...]:
    if not isinstance(bank, (list, tuple)) or len(bank) != 6:
        raise ValueError('bank must contain six entries')
    return tuple(sorted(_validate_mapping(row) for row in bank))


def _digest_rank(prefix: str) -> tuple[tuple[int, ...], ...]:
    return tuple(
        sorted(
            mapping_space(),
            key=lambda mapping: (
                sha256(prefix.encode('utf-8') + canonical_mapping_bytes(mapping)).digest(),
                canonical_mapping_bytes(mapping),
            ),
        )
    )


def build_hash_bank(index: int) -> tuple[tuple[int, ...], ...]:
    index = _strict_int(index, name='hash-bank index', minimum=0, maximum=65535)
    prefix = f'{TASK_ID}\x1fHASH_BANK\x1f{index}\x1f'
    return tuple(sorted(_digest_rank(prefix)[:6]))


def build_multiplicity_bank(partition: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    if not isinstance(partition, (list, tuple)) or not partition:
        raise ValueError('partition must be a nonempty sequence')
    partition = tuple(_strict_int(value, name='partition part', minimum=1) for value in partition)
    frozen_partitions = tuple(
        tuple(int(value) for value in row)
        for row in _frozen_design()['bank_suite']['multiplicity_bank']['partitions']
    )
    if partition not in frozen_partitions:
        raise ValueError('partition is not a frozen multiplicity partition')
    partition_json = json.dumps(list(partition), separators=(',', ':'), ensure_ascii=True)
    prefix = f'{TASK_ID}\x1fMULTIPLICITY\x1f{partition_json}\x1f'
    ranked = _digest_rank(prefix)
    rows: list[tuple[int, ...]] = []
    for mapping, count in zip(ranked, partition):
        rows.extend([mapping] * count)
    return tuple(sorted(rows))


@lru_cache(maxsize=1)
def _mapping_index_map() -> dict[tuple[int, ...], int]:
    return {mapping: index for index, mapping in enumerate(mapping_space())}


def source_counts(bank) -> tuple[int, ...]:
    counts = [0] * len(mapping_space())
    index_map = _mapping_index_map()
    for mapping in _validate_bank(bank):
        counts[index_map[mapping]] += 1
    return tuple(counts)


def _swap(mapping: tuple[int, ...], i: int, j: int) -> tuple[int, ...]:
    row = list(mapping)
    row[i], row[j] = row[j], row[i]
    return tuple(row)


def local_counts(bank) -> tuple[int, ...]:
    return _local_counts_entries(_validate_bank(bank))


def _local_counts_entries(entries) -> tuple[int, ...]:
    index_map = _mapping_index_map()
    counts = [0] * len(mapping_space())
    for source_mapping in tuple(_validate_mapping(row) for row in entries):
        for i in range(5):
            for j in range(i + 1, 5):
                counts[index_map[_swap(source_mapping, i, j)]] += 1
    return tuple(counts)


def _rotate_mapping(mapping: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(mapping[(i + 1) % 5] for i in range(5))


def _condition(weights: tuple[int, ...], history: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    space = mapping_space()
    conditioned = []
    for mapping, weight in zip(space, weights):
        if weight <= 0:
            conditioned.append(0)
            continue
        keep = all(mapping[token] == proto for token, proto in history)
        conditioned.append(weight if keep else 0)
    return tuple(conditioned)


def _history_key(public_history) -> tuple[tuple[int, int], ...]:
    if not isinstance(public_history, (list, tuple)) or len(public_history) not in (1, 2):
        raise ValueError('history must contain one or two rows')
    history: list[tuple[int, int]] = []
    for row in public_history:
        if not isinstance(row, dict) or set(row) != {'token_index', 'prototype_index'}:
            raise ValueError('history row keys drift')
        history.append(
            (
                _strict_int(row['token_index'], name='history token', minimum=0, maximum=4),
                _strict_int(row['prototype_index'], name='history prototype', minimum=0, maximum=4),
            )
        )
    if len({token for token, _ in history}) != len(history):
        raise ValueError('history tokens must be distinct')
    return tuple(history)


_FORBIDDEN_ALIASES = (
    'target_mapping', 'membership_stratum', 'stratum', 'distance', 'bank_role',
    'future_outcome', 'world_id', 'world_layout', 'policy_id', 'run_id',
    'source_id', 'hidden_cause', 'objects_by_cause', 'private_state',
    'global_state', 'scorer_truth', 'scorer', 'checkpoint_metric', 'metric_row',
    'verdict', 'artifact_path', 'artifact_hash', 'static_oracle', 'oracle_output',
)


def _reject_forbidden_aliases(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError('all object keys must be strings')
            lowered = key.lower()
            if any(alias in lowered for alias in _FORBIDDEN_ALIASES):
                raise ValueError('forbidden public alias')
            _reject_forbidden_aliases(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_forbidden_aliases(nested)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(alias in lowered for alias in _FORBIDDEN_ALIASES):
            raise ValueError('encoded forbidden public alias')


def _canonical_public_history(public_history, initial_token_index: int) -> tuple[tuple[int, int, int], ...]:
    if type(public_history) is not list or len(public_history) not in (1, 2):
        raise ValueError('public history shape drift')
    rows: list[tuple[int, int, int]] = []
    for expected_ordinal, row in enumerate(public_history):
        if type(row) is not dict or set(row) != {'ordinal', 'token_index', 'prototype_index'}:
            raise ValueError('public history row keys drift')
        ordinal = _strict_int(row['ordinal'], name='history ordinal', minimum=0, maximum=1)
        token = _strict_int(row['token_index'], name='history token', minimum=0, maximum=4)
        prototype = _strict_int(row['prototype_index'], name='history prototype', minimum=0, maximum=4)
        if ordinal != expected_ordinal:
            raise ValueError('history ordinals must be contiguous')
        rows.append((ordinal, token, prototype))
    if rows[0][1] != initial_token_index:
        raise ValueError('initial history token mismatch')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('history tokens must be distinct')
    return tuple(rows)


def validate_public_input(payload: dict) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError('public input must be an object')
    _reject_forbidden_aliases(payload)
    required = {'schema_version', 'prototype_table', 'source_mappings', 'initial_token_index', 'public_history', 'query_counts', 'remaining_budget', 'learner_state'}
    if set(payload) != required:
        raise ValueError('public input keys drift')
    if payload['schema_version'] != 'ego.v2.active_transfer.public_input.v1':
        raise ValueError('public input schema drift')
    if type(payload['prototype_table']) is not list or len(payload['prototype_table']) != 5:
        raise ValueError('prototype table shape drift')
    prototypes = []
    for row in payload['prototype_table']:
        if type(row) is not dict or set(row) != {'prototype_index', 'vector_micro'}:
            raise ValueError('prototype row keys drift')
        index = _strict_int(row['prototype_index'], name='prototype index', minimum=0, maximum=4)
        vector = row['vector_micro']
        if type(vector) is not list or len(vector) != 4:
            raise ValueError('prototype vector shape drift')
        prototypes.append((index, tuple(_strict_int(value, name='prototype component') for value in vector)))
    if sorted(index for index, _ in prototypes) != list(range(5)):
        raise ValueError('prototype indices drift')
    expected_prototypes = tuple(
        (index, tuple(vector)) for index, vector in enumerate(_prototype_table())
    )
    if tuple(prototypes) != expected_prototypes:
        raise ValueError('prototype table semantic drift')
    source = _validate_bank(payload['source_mappings'])
    initial = _strict_int(payload['initial_token_index'], name='initial token', minimum=0, maximum=4)
    history = _canonical_public_history(payload['public_history'], initial)
    if type(payload['query_counts']) is not list or len(payload['query_counts']) != 5:
        raise ValueError('query counts shape drift')
    query_counts = tuple(_strict_int(value, name='query count', minimum=0) for value in payload['query_counts'])
    expected_counts = [0] * 5
    for _, token, _ in history:
        expected_counts[token] += 1
    if query_counts != tuple(expected_counts):
        raise ValueError('query counts semantic drift')
    remaining = _strict_int(payload['remaining_budget'], name='remaining budget', minimum=0, maximum=1)
    if remaining != 2 - len(history):
        raise ValueError('remaining budget semantic drift')
    learner_state = validate_state(payload['learner_state'])
    simple_history = [
        {'token_index': token, 'prototype_index': prototype}
        for _, token, prototype in history
    ]
    expected_state = build_state(
        learner_state['arm_id'], source, simple_history, median_convention='midpoint_integer'
    )
    if learner_state != expected_state:
        raise ValueError('state semantic drift')
    return {
        'schema_version': payload['schema_version'],
        'prototype_table': tuple(prototypes),
        'source_mappings': source,
        'initial_token_index': initial,
        'public_history': history,
        'query_counts': query_counts,
        'remaining_budget': remaining,
        'learner_state': learner_state,
    }


def _arm_record(arm_id: str) -> dict[str, Any]:
    for row in _frozen_design()['arm_registry']['records']:
        if row['arm_id'] == arm_id:
            return row
    raise ValueError('unknown arm id')


def _base_contributions(inference_id: str, bank) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    src = list(source_counts(bank))
    loc = list(local_counts(bank))
    scratch = [1] * len(mapping_space())
    if inference_id == 'I_SCRATCH':
        return tuple(scratch), tuple([0] * len(src)), tuple([0] * len(src))
    if inference_id == 'I_TRANSFER':
        return tuple(scratch), tuple(20 * v for v in src), tuple(2 * v for v in loc)
    if inference_id == 'I_TRANSFER_NO_LOCAL':
        return tuple(scratch), tuple(20 * v for v in src), tuple([0] * len(src))
    if inference_id == 'I_CONSISTENCY':
        return tuple([0] * len(src)), tuple(src), tuple([0] * len(src))
    if inference_id == 'I_NO_UPDATE':
        return tuple(scratch), tuple(20 * v for v in src), tuple(2 * v for v in loc)
    if inference_id == 'I_TRANSFER_MASK_H2':
        return tuple(scratch), tuple(20 * v for v in src), tuple(2 * v for v in loc)
    if inference_id == 'I_TRANSFER_THEN_SCRATCH':
        return tuple(scratch), tuple(20 * v for v in src), tuple(2 * v for v in loc)
    if inference_id == 'I_TRANSFER_FLAT':
        support = [1 if v > 0 else 0 for v in src]
        unique_local = list(_local_counts_entries(tuple(sorted({tuple(row) for row in bank}))))
        k = sum(support)
        return tuple([k] * len(src)), tuple(120 * v for v in support), tuple(12 * v for v in unique_local)
    if inference_id == 'I_SHAM':
        rotated = tuple(sorted(_rotate_mapping(tuple(row)) for row in bank))
        sham_src = list(source_counts(rotated))
        sham_loc = list(local_counts(rotated))
        return tuple(scratch), tuple(20 * v for v in sham_src), tuple(2 * v for v in sham_loc)
    raise ValueError('unsupported inference id')


def _rational(value: int | Fraction) -> dict[str, int]:
    fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
    return {'n': fraction.numerator, 'd': fraction.denominator}


def _encode_family(family: dict[str, tuple[int, ...]]) -> dict[str, list[dict[str, int]]]:
    return {name: [_rational(value) for value in family[name]] for name in ('scratch', 'source', 'local')}


def _sealed_prior(inference_id: str, bank, history: tuple[tuple[int, int], ...]) -> dict[str, tuple[int, ...]]:
    scratch, source, local = _base_contributions(inference_id, bank)
    conditioned = {
        'scratch': _condition(scratch, history),
        'source': _condition(source, history),
        'local': _condition(local, history),
    }
    if inference_id == 'I_CONSISTENCY' and sum(conditioned['source']) == 0:
        conditioned = {
            'scratch': _condition(tuple([1] * 120), history),
            'source': tuple([0] * 120),
            'local': tuple([0] * 120),
        }
    return conditioned


def build_state(arm_id: str, bank, public_history, *, median_convention: str) -> dict[str, Any]:
    if median_convention not in {'lower', 'midpoint_integer', 'upper'}:
        raise ValueError('unknown median convention')
    bank = _validate_bank(bank)
    record = _arm_record(arm_id)
    if record['kind'] == 'aggregate':
        raise ValueError('aggregate arm has no FINITE trajectory state')
    history = _history_key(public_history)
    stage = 'H1' if len(history) == 1 else 'H2'
    scratch, source, local = _base_contributions(record['inference_id'], bank)
    unconditional = {'scratch': scratch, 'source': source, 'local': local}
    inference_id = record['inference_id']
    if inference_id == 'I_NO_UPDATE':
        incoming = unconditional
        sealed = unconditional
    elif stage == 'H1':
        incoming = unconditional
        sealed = _sealed_prior(inference_id, bank, history)
    elif inference_id == 'I_TRANSFER_MASK_H2':
        incoming = _sealed_prior('I_TRANSFER_MASK_H2', bank, history[:1])
        sealed = incoming
    elif inference_id == 'I_TRANSFER_THEN_SCRATCH':
        zeros = tuple([0] * 120)
        incoming = {
            'scratch': _condition(tuple([1] * 120), history[:1]),
            'source': zeros,
            'local': zeros,
        }
        sealed = {
            'scratch': _condition(tuple([1] * 120), history),
            'source': zeros,
            'local': zeros,
        }
    else:
        incoming = _sealed_prior(inference_id, bank, history[:1])
        sealed = _sealed_prior(inference_id, bank, history)
    effective = tuple(sealed['scratch'][i] + sealed['source'][i] + sealed['local'][i] for i in range(len(mapping_space())))
    if sum(effective) <= 0:
        raise ValueError('zero effective evidence')
    source_multiplicity = source_counts(bank)
    consistency = _condition(source_multiplicity, history)
    selected_second_token = history[1][0] if len(history) > 1 else None
    return {
        'schema_version': 'FINITE_ACTIVE_TRANSFER_STATE_V1',
        'arm_id': arm_id,
        'inference_id': inference_id,
        'acquisition_id': record['acquisition_id'],
        'decision_id': record['decision_id'],
        'transition_id': record['transition_id'],
        'stage': stage,
        'feedback_count': len(history),
        'incoming_family_contributions': _encode_family(incoming),
        'sealed_family_contributions': _encode_family(sealed),
        'effective_mapping_weights': [_rational(value) for value in effective],
        'consistency_counts': list(consistency),
        'selected_second_token': selected_second_token,
    }


def validate_state(payload: dict) -> dict[str, Any]:
    """Validate closed shape and context-free invariants only.

    This function is intentionally non-authoritative without the source bank and
    public history. ``validate_public_input`` performs the authoritative semantic
    recomputation and exact state comparison using that context.
    """
    if type(payload) is not dict:
        raise ValueError('state must be an object')
    required = {'schema_version', 'arm_id', 'inference_id', 'acquisition_id', 'decision_id', 'transition_id', 'stage', 'feedback_count', 'incoming_family_contributions', 'sealed_family_contributions', 'effective_mapping_weights', 'consistency_counts', 'selected_second_token'}
    if set(payload) != required:
        raise ValueError('state keys drift')
    if payload['schema_version'] != 'FINITE_ACTIVE_TRANSFER_STATE_V1':
        raise ValueError('state schema drift')
    record = _arm_record(payload['arm_id'])
    for field in ('inference_id', 'acquisition_id', 'decision_id', 'transition_id'):
        if payload[field] != record[field]:
            raise ValueError('state registry drift')
    if payload['stage'] not in {'H1', 'H2'}:
        raise ValueError('state stage drift')
    feedback_count = _strict_int(payload['feedback_count'], name='feedback count', minimum=1, maximum=2)
    if (payload['stage'], feedback_count) not in {('H1', 1), ('H2', 2)}:
        raise ValueError('state feedback drift')
    selected = payload['selected_second_token']
    if payload['stage'] == 'H1' and selected is not None:
        raise ValueError('H1 selected token drift')
    if payload['stage'] == 'H2':
        _strict_int(selected, name='selected second token', minimum=0, maximum=4)

    decoded_families: dict[str, dict[str, tuple[Fraction, ...]]] = {}
    for field in ('incoming_family_contributions', 'sealed_family_contributions'):
        family = payload[field]
        if type(family) is not dict or set(family) != {'scratch', 'source', 'local'}:
            raise ValueError('state family keys drift')
        decoded_families[field] = {}
        for name in ('scratch', 'source', 'local'):
            vector = family[name]
            if type(vector) is not list or len(vector) != 120:
                raise ValueError('state family shape drift')
            decoded_families[field][name] = tuple(_decode_rational(row) for row in vector)
            if any(value < 0 for value in decoded_families[field][name]):
                raise ValueError('negative state contribution')
    effective_rows = payload['effective_mapping_weights']
    if type(effective_rows) is not list or len(effective_rows) != 120:
        raise ValueError('state length drift')
    effective = tuple(_decode_rational(row) for row in effective_rows)
    sealed = decoded_families['sealed_family_contributions']
    expected = tuple(sealed['scratch'][i] + sealed['source'][i] + sealed['local'][i] for i in range(120))
    if effective != expected or sum(effective) <= 0:
        raise ValueError('state semantic drift')
    counts = payload['consistency_counts']
    if type(counts) is not list or len(counts) != 120:
        raise ValueError('consistency count shape drift')
    for value in counts:
        _strict_int(value, name='consistency count', minimum=0)
    if any(value > 6 for value in counts) or sum(counts) > 6:
        raise ValueError('consistency count bound drift')
    return payload


def _decode_rational(payload: Any) -> Fraction:
    if type(payload) is not dict or set(payload) != {'n', 'd'}:
        raise ValueError('reduced rational keys drift')
    numerator = _strict_int(payload['n'], name='rational numerator')
    denominator = _strict_int(payload['d'], name='rational denominator', minimum=1)
    if gcd(abs(numerator), denominator) != 1 or (numerator == 0 and denominator != 1):
        raise ValueError('rational not reduced')
    return Fraction(numerator, denominator)


def _state_integer_weights(state: dict[str, Any]) -> tuple[int, ...]:
    weights = tuple(_decode_rational(row) for row in state['effective_mapping_weights'])
    if any(weight.denominator != 1 for weight in weights):
        raise ValueError('non-integer primitive state weight')
    return tuple(weight.numerator for weight in weights)


def _primitive_integer_weights(state: dict[str, Any]) -> tuple[int, ...]:
    """Remove global integer scale before any acquisition or decision use."""
    weights = _state_integer_weights(state)
    if any(weight < 0 for weight in weights):
        raise ValueError('negative primitive state weight')
    divisor = 0
    for weight in weights:
        if weight > 0:
            divisor = gcd(divisor, weight)
    if divisor <= 0:
        raise ValueError('zero primitive state weight')
    return tuple(weight // divisor for weight in weights)


def round_half_even_fraction(numerator: int, denominator: int) -> int:
    numerator = _strict_int(numerator, name='rounding numerator')
    denominator = _strict_int(denominator, name='rounding denominator', minimum=1)
    sign = -1 if numerator < 0 else 1
    q, r = divmod(abs(numerator), denominator)
    if 2 * r > denominator or (2 * r == denominator and q % 2 == 1):
        q += 1
    return sign * q


def weighted_median_endpoints(values, weights):
    if not isinstance(values, (list, tuple)) or not isinstance(weights, (list, tuple)):
        raise ValueError('median values and weights must be sequences')
    if len(values) != len(weights):
        raise ValueError('median values and weights length drift')
    pairs = []
    for value, weight in zip(values, weights):
        value = _strict_int(value, name='median value')
        weight = _strict_int(weight, name='median weight', minimum=0)
        if weight > 0:
            pairs.append((value, weight))
    pairs.sort()
    if not pairs:
        raise ValueError('median requires positive total weight')
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
    midpoint = round_half_even_fraction(lower + upper, 2)
    risks = tuple(sum(weight * abs(value - action) for value, weight in pairs) for action in (lower, midpoint, upper))
    if lower > midpoint or midpoint > upper or len(set(risks)) != 1:
        raise AssertionError('weighted median minimal-risk invariant failed')
    return lower, midpoint, upper


_CONTROLLED_PROTOTYPE_TABLE: ContextVar[tuple[tuple[int, ...], ...] | None] = ContextVar(
    'controlled_prototype_table', default=None,
)


@lru_cache(maxsize=1)
def _frozen_prototype_table():
    return tuple(tuple(int(v) for v in row) for row in _frozen_design()['public_grammar']['prototype_vectors_micro'])


def _prototype_table():
    controlled = _CONTROLLED_PROTOTYPE_TABLE.get()
    return _frozen_prototype_table() if controlled is None else controlled


@contextmanager
def _controlled_prototype_table_context(validated_table):
    table = tuple(tuple(int(value) for value in row) for row in validated_table)
    if len(table) != 5 or any(len(row) != 4 for row in table):
        raise ValueError('controlled prototype table shape drift')
    frozen = _frozen_prototype_table()
    if len(set(table)) != 5 or tuple(sorted(table)) != tuple(sorted(frozen)):
        raise ValueError('controlled prototype table requires exact frozen-vector bijection')
    if _CONTROLLED_PROTOTYPE_TABLE.get() is not None:
        raise ValueError('nested controlled prototype table override')
    # Decision-byte cache keys do not carry a prototype table because ordinary
    # execution has one frozen table.  A controlled relabel therefore brackets
    # the cache lifetime so no canonical-table bytes can cross the boundary.
    _clear_decision_byte_memoization()
    token = _CONTROLLED_PROTOTYPE_TABLE.set(table)
    try:
        yield
    finally:
        _CONTROLLED_PROTOTYPE_TABLE.reset(token)
        _clear_decision_byte_memoization()


def _weighted_prediction(weights, token_index: int, median_convention: str):
    table = _prototype_table()
    space = mapping_space()
    rows = [table[mapping[token_index]] for mapping, weight in zip(space, weights) if weight > 0]
    masses = [weight for weight in weights if weight > 0]
    if not rows:
        rows = list(table)
        masses = [1] * len(rows)
    prediction = []
    endpoints = []
    for component in range(4):
        values = [row[component] for row in rows]
        lower, midpoint, upper = weighted_median_endpoints(values, masses)
        endpoints.append((lower, midpoint, upper))
        if median_convention == 'lower':
            prediction.append(lower)
        elif median_convention == 'upper':
            prediction.append(upper)
        else:
            prediction.append(midpoint)
    return tuple(prediction), tuple(endpoints)


def _l1(left, right) -> int:
    return sum(abs(int(a) - int(b)) for a, b in zip(left, right))


def _posterior_predictive_counts(weights, token_index: int) -> dict[int, int]:
    counts: dict[int, int] = {}
    for mapping, weight in zip(mapping_space(), weights):
        if weight <= 0:
            continue
        proto = mapping[token_index]
        counts[proto] = counts.get(proto, 0) + int(weight)
    return counts


def _construct_and_validate_public_context(
    arm_id: str,
    bank,
    public_history,
    *,
    median_convention: str,
) -> dict[str, Any]:
    """Build the sole closed public payload used by every live decision call."""
    bank = _validate_bank(bank)
    history = _history_key(public_history)
    initial_token = history[0][0]
    query_counts = [0] * 5
    for token, _ in history:
        query_counts[token] += 1
    payload = {
        'schema_version': 'ego.v2.active_transfer.public_input.v1',
        'prototype_table': [
            {'prototype_index': index, 'vector_micro': list(vector)}
            for index, vector in enumerate(_prototype_table())
        ],
        'source_mappings': [list(mapping) for mapping in bank],
        'initial_token_index': initial_token,
        'public_history': [
            {'ordinal': ordinal, 'token_index': token, 'prototype_index': prototype}
            for ordinal, (token, prototype) in enumerate(history)
        ],
        'query_counts': query_counts,
        'remaining_budget': 2 - len(history),
        'learner_state': build_state(
            arm_id, bank, public_history, median_convention=median_convention,
        ),
    }
    return validate_public_input(payload)


def _eig_acquisition_scores(weights: tuple[int, ...], eligible: tuple[int, ...]) -> list[dict[str, int]]:
    """Exact EIG integer surrogate; intentionally independent of entropy code."""
    rows = []
    for token in eligible:
        counts = _posterior_predictive_counts(weights, token)
        product = 1
        for outcome in sorted(counts):
            count = counts[outcome]
            if count > 0:
                product *= count ** count
        rows.append({'token_index': token, 'int_score': product})
    return rows


def _max_outcome_entropy_scores(weights: tuple[int, ...], eligible: tuple[int, ...]) -> list[dict[str, int]]:
    """Exact outcome-entropy integer surrogate, recomputed without EIG aliasing."""
    rows = []
    space = mapping_space()
    for token in eligible:
        outcome_counts: dict[int, int] = {}
        for mapping, weight in zip(space, weights):
            if weight > 0:
                outcome = mapping[token]
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + weight
        score = 1
        for outcome in sorted(outcome_counts):
            count = outcome_counts[outcome]
            if count > 0:
                score *= count ** count
        rows.append({'token_index': token, 'int_score': score})
    return rows


def _evsi_acquisition_scores(
    arm_id: str,
    bank: tuple[tuple[int, ...], ...],
    public_history,
    h1_weights: tuple[int, ...],
    eligible: tuple[int, ...],
    *,
    median_convention: str,
) -> list[dict[str, int]]:
    initial_token = _history_key(public_history)[0][0]
    table = _prototype_table()
    space = mapping_space()
    rows = []
    for query in eligible:
        score = 0
        outcomes = sorted(_posterior_predictive_counts(h1_weights, query))
        for outcome in outcomes:
            h2 = list(public_history) + [
                {'token_index': query, 'prototype_index': outcome}
            ]
            branch_decision = _fresh_prediction_decision(
                arm_id,
                bank,
                _history_key(h2),
                median_convention,
            )
            for mapping, primitive_weight in zip(space, h1_weights):
                if primitive_weight <= 0 or mapping[query] != outcome:
                    continue
                for token in range(5):
                    if token in {initial_token, query}:
                        continue
                    score += primitive_weight * _l1(
                        branch_decision['prediction_micro'][token],
                        table[mapping[token]],
                    )
        rows.append({'token_index': query, 'int_score': score})
    return rows


def _select_exact_minimizer(
    scores: list[dict[str, int]], query_policy: int | None,
) -> tuple[list[int], int]:
    if not scores:
        raise ValueError('query acquisition has no exact scores')
    min_score = min(row['int_score'] for row in scores)
    minimizing = [row['token_index'] for row in scores if row['int_score'] == min_score]
    if query_policy is None:
        return minimizing, min(minimizing)
    query_policy = _strict_int(query_policy, name='query policy', minimum=0, maximum=4)
    if query_policy not in minimizing:
        raise ValueError('query policy must select an exact minimizer')
    return minimizing, query_policy


def query_decision(
    arm_id: str,
    bank,
    public_history,
    *,
    median_convention: str,
    query_policy: int | None = None,
) -> dict[str, Any]:
    record = _arm_record(arm_id)
    if record['kind'] == 'aggregate' or record['acquisition_id'] == 'A_UNIFORM_MIXTURE':
        raise ValueError('A_UNIFORM_MIXTURE is aggregate-only')
    context = _construct_and_validate_public_context(
        arm_id, bank, public_history, median_convention=median_convention,
    )
    if context['remaining_budget'] != 1:
        raise ValueError('query decision requires the H1 budget')
    bank = context['source_mappings']
    history = tuple((token, prototype) for _, token, prototype in context['public_history'])
    observed = {token for token, _ in history}
    eligible = tuple(token for token in range(5) if token not in observed)
    acquisition_id = record['acquisition_id']
    if acquisition_id == 'A_NO_QUERY':
        if query_policy is not None:
            raise ValueError('no-query acquisition rejects query policy')
        return {
            'schema_version': 'QUERY_DECISION_V1', 'arm_id': arm_id,
            'eligible_tokens': [], 'score_kind': 'none', 'exact_scores': [],
            'minimizing_tokens': [], 'selected_token': None, 'tie_rule': 'none',
        }
    if acquisition_id.startswith('A_FIXED_V'):
        fixed = int(acquisition_id.removeprefix('A_FIXED_V'))
        if fixed not in eligible:
            raise ValueError('fixed token is not eligible')
        scores = [
            {'token_index': token, 'int_score': 0 if token == fixed else 1}
            for token in eligible
        ]
        minimizing, selected = _select_exact_minimizer(scores, query_policy)
        score_kind = 'fixed_indicator_integer'
    elif acquisition_id == 'A_PASSIVE':
        scores = [
            {'token_index': token, 'int_score': rank}
            for rank, token in enumerate(eligible)
        ]
        minimizing, selected = _select_exact_minimizer(scores, query_policy)
        score_kind = 'lexical_rank_integer'
    else:
        weights = _primitive_integer_weights(context['learner_state'])
        if acquisition_id == 'A_EIG':
            scores = _eig_acquisition_scores(weights, eligible)
            score_kind = 'eig_product_integer'
        elif acquisition_id == 'A_MAX_OUTCOME_ENTROPY':
            scores = _max_outcome_entropy_scores(weights, eligible)
            score_kind = 'eig_product_integer'
        elif acquisition_id == 'A_L1_EVSI':
            simple_history = [
                {'token_index': token, 'prototype_index': prototype}
                for token, prototype in history
            ]
            scores = _evsi_acquisition_scores(
                arm_id, bank, simple_history, weights, eligible,
                median_convention=median_convention,
            )
            score_kind = 'l1_risk_integer'
        else:
            raise ValueError('unsupported trajectory acquisition')
        minimizing, selected = _select_exact_minimizer(scores, query_policy)
    return {
        'schema_version': 'QUERY_DECISION_V1', 'arm_id': arm_id,
        'eligible_tokens': list(eligible), 'score_kind': score_kind,
        'exact_scores': scores, 'minimizing_tokens': minimizing,
        'selected_token': selected,
        'tie_rule': (
            'lexical_minimum' if query_policy is None
            else 'enumerated_exact_minimizer'
        ),
    }


def _scratch_comparator_weights(
    inference_id: str,
    bank: tuple[tuple[int, ...], ...],
    history: tuple[tuple[int, int], ...],
    *,
    median_convention: str,
) -> tuple[int, ...]:
    if inference_id == 'I_NO_UPDATE':
        return tuple([1] * len(mapping_space()))
    comparator_history = history[:1] if inference_id == 'I_TRANSFER_MASK_H2' else history
    public_history = [
        {'token_index': token, 'prototype_index': prototype}
        for token, prototype in comparator_history
    ]
    state = build_state(
        'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1',
        bank,
        public_history,
        median_convention=median_convention,
    )
    return _primitive_integer_weights(state)


def _lower_five_percent_benefit(
    transfer_weights: tuple[int, ...],
    transfer_prediction: tuple[int, ...],
    scratch_prediction: tuple[int, ...],
    token: int,
) -> int:
    weighted_benefits = []
    table = _prototype_table()
    for mapping, weight in zip(mapping_space(), transfer_weights):
        if weight <= 0:
            continue
        truth = table[mapping[token]]
        benefit = _l1(scratch_prediction, truth) - _l1(transfer_prediction, truth)
        weighted_benefits.append((benefit, weight))
    if not weighted_benefits:
        raise ValueError('empty transfer posterior')
    total = sum(weight for _, weight in weighted_benefits)
    cumulative = 0
    for benefit, weight in sorted(weighted_benefits):
        cumulative += weight
        if 20 * cumulative >= total:
            return benefit
    raise AssertionError('LCB quantile selection failed')


def prediction_decision(arm_id: str, bank, public_history, *, median_convention: str) -> dict[str, Any]:
    record = _arm_record(arm_id)
    if record['kind'] == 'aggregate' or record['acquisition_id'] == 'A_UNIFORM_MIXTURE':
        raise ValueError('A_UNIFORM_MIXTURE is aggregate-only')
    context = _construct_and_validate_public_context(
        arm_id, bank, public_history, median_convention=median_convention,
    )
    bank = context['source_mappings']
    history = tuple((token, prototype) for _, token, prototype in context['public_history'])
    observed = {token: prototype for token, prototype in history}
    transfer_weights = _primitive_integer_weights(context['learner_state'])
    scratch_weights = _scratch_comparator_weights(
        record['inference_id'], bank, history, median_convention=median_convention,
    )
    prediction: list[list[int]] = []
    endpoints: list[list[list[int]]] = []
    used_transfer: list[bool] = []
    lcb05: list[int | None] = []
    for token in range(5):
        if token in observed:
            row = _prototype_table()[observed[token]]
            prediction.append(list(row))
            endpoints.append([[value, value] for value in row])
            used_transfer.append(False)
            lcb05.append(None)
            continue
        transfer_row, transfer_end = _weighted_prediction(
            transfer_weights, token, median_convention,
        )
        scratch_row, scratch_end = _weighted_prediction(
            scratch_weights, token, median_convention,
        )
        if record['decision_id'] == 'D_SCRATCH_L1':
            selected_row, selected_end, selected_transfer, token_lcb = (
                scratch_row, scratch_end, False, None,
            )
        elif record['decision_id'] == 'D_L1_MEDIAN':
            selected_row, selected_end, selected_transfer, token_lcb = (
                transfer_row, transfer_end, True, None,
            )
        elif record['decision_id'] == 'D_LCB05_FALLBACK':
            token_lcb = _lower_five_percent_benefit(
                transfer_weights, transfer_row, scratch_row, token,
            )
            selected_transfer = token_lcb >= 0
            selected_row = transfer_row if selected_transfer else scratch_row
            selected_end = transfer_end if selected_transfer else scratch_end
        else:
            raise ValueError('unsupported decision id')
        prediction.append(list(selected_row))
        endpoints.append([[lower, upper] for lower, _, upper in selected_end])
        used_transfer.append(selected_transfer)
        lcb05.append(token_lcb)
    return {
        'schema_version': 'PREDICTION_DECISION_V1',
        'arm_id': arm_id,
        'prediction_micro': prediction,
        'median_endpoints_micro': endpoints,
        'used_transfer': used_transfer,
        'lcb05_benefit_micro': lcb05,
    }


def enumerate_query_tie_decisions(
    arm_id: str,
    bank,
    public_history,
    *,
    median_convention: str,
) -> list[dict[str, Any]]:
    lexical = query_decision(
        arm_id, bank, public_history, median_convention=median_convention,
    )
    return [
        query_decision(
            arm_id,
            bank,
            public_history,
            median_convention=median_convention,
            query_policy=token,
        )
        for token in lexical['minimizing_tokens']
    ]


def enumerate_query_tie_policies(
    arm_id: str,
    bank,
    *,
    initial_token_index: int,
    median_convention: str,
) -> dict[str, Any]:
    """Enumerate one exact-minimizer choice per nonempty H1 outcome leaf."""
    initial_token_index = _strict_int(
        initial_token_index, name='initial token', minimum=0, maximum=4,
    )
    leaf_minimizers: list[list[int]] = []
    h1_outcomes: list[int] = []
    for outcome in range(5):
        history = [
            {'token_index': initial_token_index, 'prototype_index': outcome}
        ]
        decision = query_decision(
            arm_id, bank, history, median_convention=median_convention,
        )
        if decision['minimizing_tokens']:
            h1_outcomes.append(outcome)
            leaf_minimizers.append(list(decision['minimizing_tokens']))
    policies = [list(choices) for choices in product(*leaf_minimizers)]
    if len(policies) > 4 ** 5:
        raise AssertionError('query tie policy bound exceeded')
    return {
        'h1_outcomes': h1_outcomes,
        'leaf_minimizing_tokens': leaf_minimizers,
        'policies': policies,
        'policy_count': len(policies),
        'query_selection_sensitive': any(len(tokens) > 1 for tokens in leaf_minimizers),
    }


def prediction_median_sensitivity(arm_id: str, bank, public_history) -> dict[str, Any]:
    hashes = {}
    for convention in ('lower', 'midpoint_integer', 'upper'):
        decision = prediction_decision(
            arm_id, bank, public_history, median_convention=convention,
        )
        canonical = json.dumps(
            decision, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
        ).encode('ascii')
        hashes[convention] = sha256(canonical).hexdigest()
    return {
        'decision_sha256': hashes,
        'sensitive': len(set(hashes.values())) > 1,
    }


PUBLIC_ARM_ID = 'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1'


def classify_target(bank, target_mapping) -> dict[str, Any]:
    """Compute private target strata from distinct source support only."""
    bank = _validate_bank(bank)
    target = _validate_mapping(target_mapping)
    support = tuple(sorted(set(bank)))
    distance = min(
        sum(left != right for left, right in zip(target, source))
        for source in support
    )
    if distance == 1:
        raise ValueError('D1 is impossible for permutation targets')
    strata = {
        0: 'EXACT_MEMBER_D0',
        2: 'LOCAL_SHIFT_D2',
        3: 'NONMEMBER_D3',
        4: 'NONMEMBER_D4',
        5: 'NONMEMBER_D5',
    }
    if distance not in strata:
        raise ValueError('invalid target distance')
    occurrence = sum(source == target for source in bank)
    if (distance == 0) != (occurrence > 0):
        raise AssertionError('member classification identity failed')
    if occurrence < 0 or occurrence > 6:
        raise AssertionError('source occurrence bound failed')
    return {
        'stratum': strata[distance],
        'source_occurrence': occurrence,
        'distance': distance,
    }


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
    ).encode('ascii')


@lru_cache(maxsize=None)
def _memoized_query_decision_bytes(
    arm_id: str,
    canonical_bank: tuple[tuple[int, ...], ...],
    public_history: tuple[tuple[int, int], ...],
    median_convention: str,
    query_policy: int | None,
) -> bytes:
    history_rows = [
        {'token_index': token, 'prototype_index': prototype}
        for token, prototype in public_history
    ]
    return _canonical_json_bytes(
        query_decision(
            arm_id,
            canonical_bank,
            history_rows,
            median_convention=median_convention,
            query_policy=query_policy,
        )
    )


@lru_cache(maxsize=None)
def _memoized_prediction_decision_bytes(
    arm_id: str,
    canonical_bank: tuple[tuple[int, ...], ...],
    public_history: tuple[tuple[int, int], ...],
    median_convention: str,
) -> bytes:
    history_rows = [
        {'token_index': token, 'prototype_index': prototype}
        for token, prototype in public_history
    ]
    return _canonical_json_bytes(
        prediction_decision(
            arm_id,
            canonical_bank,
            history_rows,
            median_convention=median_convention,
        )
    )


def _clear_decision_byte_memoization() -> None:
    _memoized_query_decision_bytes.cache_clear()
    _memoized_prediction_decision_bytes.cache_clear()


def _fresh_query_decision(
    arm_id: str,
    bank: tuple[tuple[int, ...], ...],
    history: tuple[tuple[int, int], ...],
    median_convention: str,
    query_policy: int | None,
) -> dict[str, Any]:
    canonical_bank = _validate_bank(bank)
    canonical_history = _history_key([
        {'token_index': token, 'prototype_index': prototype}
        for token, prototype in history
    ])
    # Memoization is a same-arm, same-public-state pure-function optimization.
    # Only canonical bytes are retained; every caller receives a fresh decode.
    return json.loads(
        _memoized_query_decision_bytes(
            arm_id,
            canonical_bank,
            canonical_history,
            median_convention,
            query_policy,
        ).decode('ascii')
    )


def _fresh_prediction_decision(
    arm_id: str,
    bank: tuple[tuple[int, ...], ...],
    history: tuple[tuple[int, int], ...],
    median_convention: str,
) -> dict[str, Any]:
    canonical_bank = _validate_bank(bank)
    canonical_history = _history_key([
        {'token_index': token, 'prototype_index': prototype}
        for token, prototype in history
    ])
    return json.loads(
        _memoized_prediction_decision_bytes(
            arm_id,
            canonical_bank,
            canonical_history,
            median_convention,
        ).decode('ascii')
    )


def _parse_pairwise_query_policy(query_policy) -> tuple[int | None, int | None]:
    if type(query_policy) is dict:
        if set(query_policy) != {'candidate', 'public'}:
            raise ValueError('query policy pair requires exact candidate/public keys')
        values = []
        for side in ('candidate', 'public'):
            value = query_policy[side]
            if value is None:
                values.append(None)
            else:
                try:
                    values.append(
                        _strict_int(
                            value, name=f'{side} query policy component',
                            minimum=0, maximum=4,
                        )
                    )
                except ValueError as error:
                    raise ValueError('query policy pair component must be int or null') from error
        return values[0], values[1]
    if query_policy is None:
        return None, None
    try:
        candidate = _strict_int(
            query_policy, name='candidate query policy', minimum=0, maximum=4,
        )
    except ValueError as error:
        raise ValueError('query policy must be an integer or exact pair') from error
    return candidate, None


def _normalized_rational(raw: int, component_denominator: int) -> dict[str, int]:
    component_denominator = _strict_int(
        component_denominator, name='metric component denominator', minimum=1,
    )
    return _rational(Fraction(raw, component_denominator * 1_000_000))


def _token_losses(prediction: dict[str, Any], target: tuple[int, ...]) -> list[int]:
    table = _prototype_table()
    return [
        _l1(tuple(prediction['prediction_micro'][token]), table[target[token]])
        for token in range(5)
    ]


def _assert_observed_copies(
    decision: dict[str, Any], history: tuple[tuple[int, int], ...],
) -> None:
    table = _prototype_table()
    for token, prototype in history:
        if tuple(decision['prediction_micro'][token]) != table[prototype]:
            raise AssertionError('observed token was not copied exactly')


def _trajectory_target_metric(
    bank: tuple[tuple[int, ...], ...],
    target: tuple[int, ...],
    arm_id: str,
    *,
    median_convention: str,
    candidate_query_policy: int | None,
    public_query_policy: int | None,
) -> dict[str, Any]:
    record = _arm_record(arm_id)
    if record['kind'] != 'trajectory':
        raise ValueError('trajectory metric requires a trajectory arm')

    h1 = ((0, target[0]),)
    candidate_query = _fresh_query_decision(
        arm_id, bank, h1, median_convention, candidate_query_policy,
    )
    q_candidate = candidate_query['selected_token']
    candidate_history = h1
    if q_candidate is not None:
        candidate_history = h1 + ((q_candidate, target[q_candidate]),)
    candidate = _fresh_prediction_decision(
        arm_id, bank, candidate_history, median_convention,
    )

    # PUBLIC is a separate trajectory: it chooses its own qB at H1, observes
    # its own H2, and never receives the candidate's selected action.
    public_query = _fresh_query_decision(
        PUBLIC_ARM_ID, bank, h1, median_convention, public_query_policy,
    )
    q_public = public_query['selected_token']
    if q_public is None:
        raise AssertionError('PUBLIC comparator must select one H2 query')
    public_history = h1 + ((q_public, target[q_public]),)
    public = _fresh_prediction_decision(
        PUBLIC_ARM_ID, bank, public_history, median_convention,
    )

    # The same-history comparator is scratch prediction on the candidate's
    # exact history.  Its acquisition is not rerun and cannot alter that H2.
    same_history_scratch = _fresh_prediction_decision(
        PUBLIC_ARM_ID, bank, candidate_history, median_convention,
    )
    _assert_observed_copies(candidate, candidate_history)
    _assert_observed_copies(public, public_history)
    _assert_observed_copies(same_history_scratch, candidate_history)

    candidate_losses = _token_losses(candidate, target)
    public_losses = _token_losses(public, target)
    same_history_losses = _token_losses(same_history_scratch, target)
    candidate_own_tokens = [
        token for token in range(5) if token != 0 and token != q_candidate
    ]
    public_own_tokens = [token for token in range(5) if token not in {0, q_public}]
    common_tokens = [
        token for token in range(5)
        if token != 0 and token != q_candidate and token != q_public
    ]
    own_denominator = 4 * len(candidate_own_tokens)
    public_own_denominator = 4 * len(public_own_tokens)
    common_denominator = 4 * len(common_tokens)
    same_history_denominator = own_denominator
    expected_own = 16 if q_candidate is None else 12
    if own_denominator != expected_own or public_own_denominator != 12:
        raise AssertionError('own-unqueried denominator drift')
    if q_candidate is not None:
        expected_common = 12 if q_candidate == q_public else 8
        if common_denominator != expected_common:
            raise AssertionError('common-unqueried denominator drift')
    elif common_denominator != 12:
        # With no qC there are three tokens outside {initial,qB}; the frozen
        # 8-component different-query formula applies only to two actual H2
        # queries.
        raise AssertionError('no-query common denominator drift')

    candidate_full = sum(candidate_losses)
    public_full = sum(public_losses)
    candidate_own = sum(candidate_losses[token] for token in candidate_own_tokens)
    public_own = sum(public_losses[token] for token in public_own_tokens)
    candidate_common = sum(candidate_losses[token] for token in common_tokens)
    public_common = sum(public_losses[token] for token in common_tokens)
    same_history_raw = sum(same_history_losses[token] for token in candidate_own_tokens)
    common_raw = public_common - candidate_common
    if q_candidate == q_public:
        query_asymmetry_raw = 0
    else:
        public_at_candidate_query = 0 if q_candidate is None else public_losses[q_candidate]
        query_asymmetry_raw = public_at_candidate_query - candidate_losses[q_public]
    full_improvement_raw = public_full - candidate_full
    if full_improvement_raw != common_raw + query_asymmetry_raw:
        raise AssertionError('full/common/query-asymmetry identity failed')
    same_history_forward_raw = same_history_raw - candidate_own

    metric_rationals = {
        'candidate_full_endpoint_mae': _normalized_rational(candidate_full, 20),
        'baseline_full_endpoint_mae': _normalized_rational(public_full, 20),
        'full_endpoint_improvement': _normalized_rational(full_improvement_raw, 20),
        'candidate_own_unqueried_forward_mae': _normalized_rational(candidate_own, own_denominator),
        'baseline_own_unqueried_forward_mae': _normalized_rational(public_own, public_own_denominator),
        'candidate_common_unqueried_forward_mae': _normalized_rational(candidate_common, common_denominator),
        'baseline_common_unqueried_forward_mae': _normalized_rational(public_common, common_denominator),
        'common_unqueried_forward_improvement': _normalized_rational(common_raw, common_denominator),
        'candidate_same_history_forward_mae': _normalized_rational(candidate_own, same_history_denominator),
        'same_history_scratch_forward_mae': _normalized_rational(same_history_raw, same_history_denominator),
        'same_history_forward_improvement': _normalized_rational(same_history_forward_raw, same_history_denominator),
        'common_contribution_to_full_improvement': _normalized_rational(common_raw, 20),
        'query_asymmetry_contribution_to_full_improvement': _normalized_rational(query_asymmetry_raw, 20),
    }
    return {
        'schema_version': 'ARM_TARGET_METRIC_V1',
        'arm_id': arm_id,
        'target_mapping': list(target),
        'selected_query_token': q_candidate,
        'public_selected_query_token': q_public,
        'query_decision': candidate_query,
        'public_query_decision': public_query,
        'prediction_decision': candidate,
        'public_prediction_decision': public,
        'same_history_scratch_prediction_decision': same_history_scratch,
        'used_transfer': candidate['used_transfer'],
        'candidate_own_unqueried_tokens': candidate_own_tokens,
        'baseline_own_unqueried_tokens': public_own_tokens,
        'common_unqueried_tokens': common_tokens,
        'candidate_token_losses_raw': candidate_losses,
        'baseline_token_losses_raw': public_losses,
        'same_history_scratch_token_losses_raw': same_history_losses,
        'candidate_full_loss_raw': candidate_full,
        'baseline_full_loss_raw': public_full,
        'candidate_own_unqueried_loss_raw': candidate_own,
        'baseline_own_unqueried_loss_raw': public_own,
        'candidate_common_unqueried_loss_raw': candidate_common,
        'baseline_common_unqueried_loss_raw': public_common,
        'same_history_scratch_loss_raw': same_history_raw,
        'full_improvement_raw': full_improvement_raw,
        'common_raw': common_raw,
        'query_asymmetry_raw': query_asymmetry_raw,
        'same_history_forward_raw': same_history_forward_raw,
        'metric_denominators': {
            'full': 20,
            'own_unqueried': own_denominator,
            'common_unqueried': common_denominator,
            'same_history_forward': same_history_denominator,
        },
        'metric_rationals': metric_rationals,
    }


def _uniform_mixture_branch_ids(record: dict[str, Any]) -> list[str]:
    acquisition_order = ['A_FIXED_V1', 'A_FIXED_V2', 'A_FIXED_V3', 'A_FIXED_V4']
    records = _frozen_design()['arm_registry']['records']
    branches = []
    for acquisition_id in acquisition_order:
        matches = [
            row['arm_id'] for row in records
            if row['kind'] == 'trajectory'
            and row['inference_id'] == record['inference_id']
            and row['decision_id'] == record['decision_id']
            and row['acquisition_id'] == acquisition_id
        ]
        if len(matches) != 1:
            raise ValueError('uniform-mixture branch registry drift')
        branches.append(matches[0])
    return branches


def evaluate_target(
    bank,
    target_mapping,
    arm_id: str,
    *,
    median_convention: str,
    query_policy=None,
) -> dict[str, Any]:
    bank = _validate_bank(bank)
    target = _validate_mapping(target_mapping)
    record = _arm_record(arm_id)
    immutable_bank = canonical_bank_bytes(bank)
    immutable_target = canonical_mapping_bytes(target)
    candidate_query_policy, public_query_policy = _parse_pairwise_query_policy(
        query_policy
    )
    if record['kind'] == 'trajectory':
        metric = _trajectory_target_metric(
            bank,
            target,
            arm_id,
            median_convention=median_convention,
            candidate_query_policy=candidate_query_policy,
            public_query_policy=public_query_policy,
        )
    elif record['kind'] == 'aggregate':
        if candidate_query_policy is not None:
            raise ValueError('aggregate metric rejects candidate query policy')
        branch_ids = _uniform_mixture_branch_ids(record)
        branches = [
            _trajectory_target_metric(
                bank,
                target,
                branch_id,
                median_convention=median_convention,
                candidate_query_policy=None,
                public_query_policy=public_query_policy,
            )
            for branch_id in branch_ids
        ]
        metric_ids = tuple(branches[0]['metric_rationals'])
        if any(tuple(branch['metric_rationals']) != metric_ids for branch in branches):
            raise AssertionError('uniform-mixture metric registry drift')
        expected = {}
        for metric_id in metric_ids:
            value = sum(
                (_decode_rational(branch['metric_rationals'][metric_id]) for branch in branches),
                Fraction(0, 1),
            ) / 4
            expected[metric_id] = _rational(value)
        metric = {
            'schema_version': 'AGGREGATE_METRIC_V1',
            'arm_id': arm_id,
            'branch_arm_ids': branch_ids,
            'branch_weights': [_rational(Fraction(1, 4)) for _ in branches],
            'expected_metric_rationals': expected,
        }
        expected_keys = set(
            _frozen_design()['closed_schemas']['AGGREGATE_METRIC_V1']['keys']
        )
        if set(metric) != expected_keys:
            raise AssertionError('aggregate metric schema drift')
    else:
        raise ValueError('unsupported frozen arm kind')
    if canonical_bank_bytes(bank) != immutable_bank or canonical_mapping_bytes(target) != immutable_target:
        raise AssertionError('immutable evaluator input changed')
    return metric


def _validate_query_policies(
    query_policies,
    bank: tuple[tuple[int, ...], ...],
    median_convention: str,
) -> dict[str, tuple[int, ...]]:
    if query_policies is None:
        return {}
    if type(query_policies) is not dict:
        raise ValueError('query_policies must be a dict')
    records = {row['arm_id']: row for row in _frozen_design()['arm_registry']['records']}
    policies: dict[str, tuple[int, ...]] = {}
    for arm_id, policy in query_policies.items():
        if type(arm_id) is not str or arm_id not in records:
            raise ValueError('unknown or extra query policy arm')
        record = records[arm_id]
        if record['kind'] != 'trajectory' or record['acquisition_id'] in {'A_NO_QUERY', 'A_UNIFORM_MIXTURE'}:
            raise ValueError('query policy arm has no selectable H2 query')
        if not isinstance(policy, (list, tuple)) or len(policy) != 5:
            raise ValueError('query policy must contain exactly five H1-leaf choices')
        canonical = tuple(
            _strict_int(value, name='query policy leaf', minimum=0, maximum=4)
            for value in policy
        )
        for outcome, selected in enumerate(canonical):
            _fresh_query_decision(
                arm_id, bank, ((0, outcome),), median_convention, selected,
            )
        policies[arm_id] = canonical
    return policies


def _validate_bank_role_provenance(
    bank_role_ids,
    bank: tuple[tuple[int, ...], ...],
) -> tuple[str, ...]:
    if not isinstance(bank_role_ids, (list, tuple)) or not bank_role_ids:
        raise ValueError('bank role aliases must be a nonempty sequence')
    role_ids = tuple(bank_role_ids)
    if any(type(role_id) is not str or not role_id for role_id in role_ids):
        raise ValueError('bank role aliases must be nonempty strings')
    if len(set(role_ids)) != len(role_ids):
        raise ValueError('bank role aliases must be unique')

    design = _frozen_design()
    primary_ids = tuple(design['bank_suite']['primary_role_ids'])
    property_ids = tuple(design['bank_suite']['property_predicates'])
    registered = set(primary_ids) | set(property_ids)
    if any(role_id not in registered for role_id in role_ids):
        raise ValueError('bank role must be an exact registered role id')
    property_banks = scan_property_banks() if any(
        role_id in property_ids for role_id in role_ids
    ) else {}
    partitions = {
        'MULT_' + '_'.join(str(value) for value in partition): tuple(partition)
        for partition in design['bank_suite']['multiplicity_bank']['partitions']
    }
    supplied_bytes = canonical_bank_bytes(bank)
    for role_id in role_ids:
        if role_id.startswith('HASH_'):
            expected_bank = build_hash_bank(int(role_id.removeprefix('HASH_')))
        elif role_id in partitions:
            expected_bank = build_multiplicity_bank(partitions[role_id])
        else:
            expected_bank = _validate_bank(property_banks[role_id]['bank'])
        if canonical_bank_bytes(expected_bank) != supplied_bytes:
            raise ValueError('bank role canonical bank bytes mismatch')
    return role_ids


def _evaluate_bank_once(
    bank_role_ids,
    bank,
    *,
    median_convention: str,
    query_policies=None,
) -> list[dict[str, Any]]:
    bank = _validate_bank(bank)
    role_ids = _validate_bank_role_provenance(bank_role_ids, bank)
    policies = _validate_query_policies(query_policies, bank, median_convention)
    records = _frozen_design()['arm_registry']['records']
    if len(records) != 45 or len({row['arm_id'] for row in records}) != 45:
        raise ValueError('exact 45-arm registry required')
    bank_hash = sha256(canonical_bank_bytes(bank)).hexdigest()
    public_policy = policies.get(PUBLIC_ARM_ID)
    rows: list[dict[str, Any]] = []
    table = _prototype_table()
    for target in mapping_space():
        classification = classify_target(bank, target)
        scorer_truth = [list(table[target[token]]) for token in range(5)]
        for record in records:
            arm_id = record['arm_id']
            candidate_policy = policies.get(arm_id)
            candidate_leaf = (
                None if candidate_policy is None else candidate_policy[target[0]]
            )
            public_leaf = (
                None if public_policy is None else public_policy[target[0]]
            )
            metric = evaluate_target(
                bank,
                target,
                arm_id,
                median_convention=median_convention,
                query_policy={
                    'candidate': candidate_leaf,
                    'public': public_leaf,
                },
            )
            envelope = {
                'schema_version': 'VERIFIER_PRIVATE_ENVELOPE_V1',
                'bank_role_ids': list(role_ids),
                'canonical_bank_sha256': bank_hash,
                'target_mapping': list(target),
                'stratum': classification['stratum'],
                'source_occurrence': classification['source_occurrence'],
                'distance': classification['distance'],
                'scorer_truth': scorer_truth,
                'metric_rows': [metric],
                'artifact_receipts': [],
            }
            expected_keys = set(
                _frozen_design()['closed_schemas']['VERIFIER_PRIVATE_ENVELOPE_V1']['keys']
            )
            if set(envelope) != expected_keys:
                raise AssertionError('verifier-private envelope schema drift')
            rows.append(envelope)
    if len(rows) != 120 * 45:
        raise AssertionError('bank evaluator row-count drift')
    return rows


def evaluate_bank(
    bank_role_ids,
    bank,
    *,
    median_convention: str,
    query_policies=None,
) -> list[dict[str, Any]]:
    # Decision-byte memoization is bank-call scoped. Clearing both before and
    # after prevents cross-bank/run carry-over while preserving exact pure-call
    # deduplication inside one 120 x 45 evaluation.
    _clear_decision_byte_memoization()
    try:
        return _evaluate_bank_once(
            bank_role_ids,
            bank,
            median_convention=median_convention,
            query_policies=query_policies,
        )
    finally:
        _clear_decision_byte_memoization()


def _source_groups(bank) -> dict[int, tuple[tuple[int, ...], ...]]:
    support = tuple(sorted(set(_validate_bank(bank))))
    return {outcome: tuple(mapping for mapping in support if mapping[0] == outcome) for outcome in range(5)}


def _legal_policies(bank) -> tuple[tuple[int, ...], ...]:
    groups = _source_groups(bank)
    choices = [(-1,) if not groups[outcome] else (1, 2, 3, 4) for outcome in range(5)]
    return tuple(product(*choices))


def _separable_witness(bank) -> dict[str, Any] | None:
    groups = _source_groups(bank)
    for policy in _legal_policies(bank):
        if all(
            not group or len({mapping[policy[outcome]] for mapping in group}) == len(group)
            for outcome, group in groups.items()
        ):
            return {'policy': list(policy)}
    return None


def _collision_witnesses(bank) -> dict[str, Any] | None:
    groups = _source_groups(bank)
    policy_witnesses = []
    table = _prototype_table()
    for policy in _legal_policies(bank):
        witness = None
        for outcome in range(5):
            query = policy[outcome]
            if query == -1:
                continue
            group = groups[outcome]
            for left_index, left in enumerate(group):
                for right in group[left_index + 1:]:
                    if left[query] != right[query]:
                        continue
                    for token in range(1, 5):
                        if token == query:
                            continue
                        if _l1(table[left[token]], table[right[token]]) > 0:
                            witness = [outcome, list(left), list(right), token]
                            break
                    if witness is not None:
                        break
                if witness is not None:
                    break
            if witness is not None:
                break
        if witness is None:
            return None
        policy_witnesses.append({'policy': list(policy), 'witness': witness})
    return {'policy_witnesses': policy_witnesses}


def _eig_score(weights: tuple[int, ...], token: int) -> int:
    score = 1
    for count in _posterior_predictive_counts(weights, token).values():
        if count > 0:
            score *= count ** count
    return score


def _evsi_score(weights: tuple[int, ...], initial_token: int, query: int) -> int:
    score = 0
    for outcome in sorted(_posterior_predictive_counts(weights, query)):
        h2_weights = _condition(weights, ((query, outcome),))
        for token in range(5):
            if token in {initial_token, query}:
                continue
            prediction, _ = _weighted_prediction(h2_weights, token, 'midpoint_integer')
            for mapping, weight in zip(mapping_space(), h2_weights):
                if weight > 0:
                    score += weight * _l1(prediction, _prototype_table()[mapping[token]])
    return score


def _decoy_witness(bank) -> dict[str, Any] | None:
    for outcome in range(5):
        history = [{'token_index': 0, 'prototype_index': outcome}]
        state = build_state(
            'ARM_I_TRANSFER__A_L1_EVSI__D_L1_MEDIAN',
            bank,
            history,
            median_convention='midpoint_integer',
        )
        weights = _primitive_integer_weights(state)
        eig_scores = {query: _eig_score(weights, query) for query in range(1, 5)}
        evsi_scores = {query: _evsi_score(weights, 0, query) for query in range(1, 5)}
        eig_min = [query for query, score in eig_scores.items() if score == min(eig_scores.values())]
        evsi_min = [query for query, score in evsi_scores.items() if score == min(evsi_scores.values())]
        if len(eig_min) == 1 and len(evsi_min) == 1 and eig_min[0] != evsi_min[0]:
            return {
                'h1_outcome': outcome,
                'eig_query': eig_min[0],
                'evsi_query': evsi_min[0],
            }
    return None


def _marginal_vector(entries: tuple[tuple[int, ...], ...], token: int) -> tuple[int, ...]:
    return tuple(sum(mapping[token] == prototype for mapping in entries) for prototype in range(5))


def _joint_vector(entries: tuple[tuple[int, ...], ...], left: int, right: int) -> tuple[int, ...]:
    return tuple(
        sum(mapping[left] == left_prototype and mapping[right] == right_prototype for mapping in entries)
        for left_prototype in range(5)
        for right_prototype in range(5)
    )


def _balanced_marginal_witness(bank) -> dict[str, Any] | None:
    canonical = _validate_bank(bank)
    for outcome in range(5):
        entries = tuple(mapping for mapping in canonical if mapping[0] == outcome)
        if len(set(entries)) < 2:
            continue
        marginals = tuple(_marginal_vector(entries, query) for query in range(1, 5))
        if len(set(marginals)) != 1:
            continue
        ordered_pairs = tuple((left, right) for left in range(1, 5) for right in range(1, 5) if left != right)
        joints = {pair: _joint_vector(entries, *pair) for pair in ordered_pairs}
        for first, second in combinations(ordered_pairs, 2):
            if joints[first] != joints[second]:
                return {
                    'h1_outcome': outcome,
                    'ordered_pair_a': list(first),
                    'ordered_pair_b': list(second),
                    'joint_vector_a': list(joints[first]),
                    'joint_vector_b': list(joints[second]),
                }
    return None


def _property_record(index: int, bank, witness: dict[str, Any]) -> dict[str, Any]:
    canonical = canonical_bank_bytes(bank)
    return {
        'first_index': index,
        'bank': [list(row) for row in _validate_bank(bank)],
        'canonical_bank_bytes': canonical.decode('ascii'),
        'canonical_bank_sha256': sha256(canonical).hexdigest(),
        'witness': witness,
    }


def _scan_property_banks(*, scan_stop: int) -> dict[str, dict]:
    scan_stop = _strict_int(scan_stop, name='property scan stop', minimum=0, maximum=65535)
    results: dict[str, dict] = {}
    predicates = (
        ('B_SEPARABLE', _separable_witness),
        ('B_COLLISION', _collision_witnesses),
        ('B_DECOY', _decoy_witness),
        ('B_BALANCED_MARGINAL', _balanced_marginal_witness),
    )
    for index in range(scan_stop + 1):
        bank = build_hash_bank(index)
        for role, predicate in predicates:
            if role in results:
                continue
            witness = predicate(bank)
            if witness is not None:
                results[role] = _property_record(index, bank, witness)
        if len(results) == len(predicates):
            return results
    raise ValueError('property bank scan incomplete')


@lru_cache(maxsize=1)
def scan_property_banks() -> dict[str, dict]:
    return _scan_property_banks(scan_stop=65535)


def registered_ablation_ids() -> tuple[str, ...]:
    records = _frozen_design()['ablation_registry']['records']
    ids = tuple(row['ablation_id'] for row in records)
    if len(ids) != 13 or len(set(ids)) != 13:
        raise ValueError('exact frozen 13-entry ablation registry required')
    return ids


def _validate_permutation(permutation, *, name: str) -> tuple[int, ...]:
    try:
        row = tuple(
            _strict_int(value, name=f'{name} entry', minimum=0, maximum=4)
            for value in permutation
        )
    except TypeError as error:
        raise ValueError(f'{name} must be a permutation') from error
    if len(row) != 5 or tuple(sorted(row)) != (0, 1, 2, 3, 4):
        raise ValueError(f'{name} must be a permutation')
    return row


def _inverse_permutation(permutation: tuple[int, ...]) -> tuple[int, ...]:
    inverse = [0] * 5
    for old, new in enumerate(permutation):
        inverse[new] = old
    return tuple(inverse)


def _semantic_sha256(value: Any) -> str:
    return sha256(_canonical_json_bytes(value)).hexdigest()


def _behavior_semantic_payload(trace: dict[str, Any]) -> dict[str, Any]:
    """Strip registry identity while retaining every computed behavior field."""
    output = deepcopy(trace)
    output.pop('arm_id', None)
    for state_key in ('state_h1', 'state_final'):
        state = output[state_key]
        for field in (
            'arm_id', 'inference_id', 'acquisition_id', 'decision_id',
            'transition_id',
        ):
            state.pop(field, None)
    output['query_decision'].pop('arm_id', None)
    output['prediction_decision'].pop('arm_id', None)
    return output


def _run_live_semantic_trace(
    arm_id: str,
    bank,
    target_mapping,
    *,
    initial_token_index: int,
    median_convention: str,
    query_policy: int | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Run the live state -> query -> state -> prediction path once."""
    canonical_bank = _validate_bank(bank)
    target = _validate_mapping(target_mapping)
    initial = _strict_int(
        initial_token_index, name='initial token', minimum=0, maximum=4,
    )
    h1 = [{'token_index': initial, 'prototype_index': target[initial]}]
    state_h1 = build_state(
        arm_id, canonical_bank, h1, median_convention=median_convention,
    )
    query = query_decision(
        arm_id,
        canonical_bank,
        h1,
        median_convention=median_convention,
        query_policy=query_policy,
    )
    history = list(h1)
    if query['selected_token'] is not None:
        selected = query['selected_token']
        history.append(
            {'token_index': selected, 'prototype_index': target[selected]}
        )
    state_final = build_state(
        arm_id, canonical_bank, history, median_convention=median_convention,
    )
    prediction = prediction_decision(
        arm_id, canonical_bank, history, median_convention=median_convention,
    )
    trace = {
        'arm_id': arm_id,
        'public_history': history,
        'state_h1': state_h1,
        'query_decision': query,
        'state_final': state_final,
        'prediction_decision': prediction,
    }
    return trace, {
        'state_calls': 2,
        'query_decision_calls': 1,
        'prediction_decision_calls': 1,
    }


def _sum_invocation_receipts(*receipts: dict[str, int]) -> dict[str, int]:
    keys = sorted({key for receipt in receipts for key in receipt})
    return {key: sum(receipt.get(key, 0) for receipt in receipts) for key in keys}


def _execute_ordinary_ablation(
    record: dict[str, Any],
    bank,
    target_mapping,
    *,
    median_convention: str,
) -> dict[str, Any]:
    arm_ids = tuple(record.get('registered_arm_ids', ()))
    if not arm_ids:
        raise ValueError('ordinary ablation has no registered arms')
    target = _validate_mapping(target_mapping)
    bundles = []
    receipts = []
    for arm_id in arm_ids:
        # ``evaluate_target`` is the metric producer.  The explicit semantic
        # trace independently exercises the exact live state/query/pred path.
        metric = evaluate_target(
            bank, target, arm_id, median_convention=median_convention,
        )
        trace, trace_receipt = _run_live_semantic_trace(
            arm_id,
            bank,
            target,
            initial_token_index=0,
            median_convention=median_convention,
        )
        bundles.append({'arm_id': arm_id, 'metric': metric, 'trace': trace})
        receipts.append(dict(trace_receipt, evaluate_target_calls=1))

    primary_arm_id = _frozen_design()['arm_registry']['primary_conservative']
    primary_reference, primary_receipt = _run_live_semantic_trace(
        primary_arm_id,
        bank,
        target,
        initial_token_index=0,
        median_convention=median_convention,
    )
    registered_hashes = [
        _semantic_sha256(_behavior_semantic_payload(bundle['trace']))
        for bundle in bundles
    ]
    primary_hash = _semantic_sha256(_behavior_semantic_payload(primary_reference))
    equal_to_primary = [value == primary_hash for value in registered_hashes]

    semantic_output: Any = bundles
    output = {
        'ablation_id': record['ablation_id'],
        'registered': True,
        'executed_arm_ids': list(arm_ids),
        'semantic_output': semantic_output,
        'semantic_sha256': _semantic_sha256(semantic_output),
        'semantic_hashes': {
            'registered_arms': registered_hashes,
            'primary_reference': primary_hash,
        },
        'semantic_equal_to_primary': equal_to_primary,
        'semantic_changed_from_primary': [not value for value in equal_to_primary],
        'invocation_receipts': _sum_invocation_receipts(
            *receipts, primary_receipt,
        ),
    }
    if record['ablation_id'] == 'ABL_SOURCE_DELETE':
        if arm_ids != (PUBLIC_ARM_ID,):
            raise ValueError('source-delete must bind canonical PUBLIC arm')
        # Both receipts are produced by the canonical PUBLIC callables.  There
        # is deliberately no second scratch implementation.
        reference, reference_receipt = _run_live_semantic_trace(
            PUBLIC_ARM_ID,
            bank,
            target,
            initial_token_index=0,
            median_convention=median_convention,
        )
        ablation_trace = bundles[0]['trace']
        hashes = {
            'ablation': _semantic_sha256(ablation_trace),
            'canonical_public': _semantic_sha256(reference),
        }
        output['semantic_hashes'].update(hashes)
        output['public_byte_identity'] = hashes['ablation'] == hashes['canonical_public']
        output['invocation_receipts'] = _sum_invocation_receipts(
            output['invocation_receipts'], reference_receipt,
        )
    if record['ablation_id'] == 'ABL_NO_QUERY':
        denominators = [
            bundle['metric']['metric_denominators']['own_unqueried']
            for bundle in bundles
        ]
        output['own_unqueried_denominators'] = denominators
    return output


def enumerate_unique_source_orders(bank) -> tuple[tuple[tuple[int, ...], ...], ...]:
    canonical = _validate_bank(bank)
    orders = tuple(sorted(set(permutations(canonical))))
    multiplicities = [canonical.count(mapping) for mapping in sorted(set(canonical))]
    expected = 1
    for value in range(2, 7):
        expected *= value
    for multiplicity in multiplicities:
        divisor = 1
        for value in range(2, multiplicity + 1):
            divisor *= value
        expected //= divisor
    if len(orders) != expected:
        raise AssertionError('unique source-order count identity failed')
    return orders


def execute_source_order_invariance_case(
    bank,
    target_mapping,
    source_order,
    *,
    median_convention: str,
    arm_ids=None,
) -> dict[str, Any]:
    canonical = _validate_bank(bank)
    reordered = tuple(_validate_mapping(row) for row in source_order)
    if len(reordered) != 6 or tuple(sorted(reordered)) != canonical:
        raise ValueError('source order must preserve the exact bank multiset')
    if arm_ids is None:
        selected_arms = tuple(
            row['arm_id'] for row in _frozen_design()['arm_registry']['records']
            if row['kind'] == 'trajectory'
        )
    else:
        selected_arms = tuple(arm_ids)
    trajectory_ids = {
        row['arm_id'] for row in _frozen_design()['arm_registry']['records']
        if row['kind'] == 'trajectory'
    }
    if (
        not selected_arms
        or len(set(selected_arms)) != len(selected_arms)
        or any(arm_id not in trajectory_ids for arm_id in selected_arms)
    ):
        raise ValueError('source-order arms must be exact registered trajectory arms')

    baseline = []
    reordered_output = []
    receipts = []
    for arm_id in selected_arms:
        first, first_receipt = _run_live_semantic_trace(
            arm_id,
            canonical,
            target_mapping,
            initial_token_index=0,
            median_convention=median_convention,
        )
        second, second_receipt = _run_live_semantic_trace(
            arm_id,
            reordered,
            target_mapping,
            initial_token_index=0,
            median_convention=median_convention,
        )
        baseline.append(first)
        reordered_output.append(second)
        receipts.extend((first_receipt, second_receipt))
    baseline_hash = _semantic_sha256(baseline)
    reordered_hash = _semantic_sha256(reordered_output)
    return {
        'scope_arm_ids': list(selected_arms),
        'unique_order_count': len(enumerate_unique_source_orders(canonical)),
        'baseline_semantic_sha256': baseline_hash,
        'reordered_semantic_sha256': reordered_hash,
        'semantic_hashes': {
            'baseline': baseline_hash,
            'intervened': reordered_hash,
        },
        'semantic_equal': baseline_hash == reordered_hash,
        'semantic_changed': baseline_hash != reordered_hash,
        'invocation_receipts': _sum_invocation_receipts(*receipts),
    }


def _relabel_mapping_tokens(mapping, permutation) -> tuple[int, ...]:
    mapping = _validate_mapping(mapping)
    permutation = _validate_permutation(permutation, name='token permutation')
    relabelled = [0] * 5
    for old_index, new_index in enumerate(permutation):
        relabelled[new_index] = mapping[old_index]
    return tuple(relabelled)


def _inverse_map_mapping_weight_vector(values, permutation) -> list[Any]:
    if len(values) != 120:
        raise ValueError('mapping-indexed vector shape drift')
    index_map = _mapping_index_map()
    return [
        deepcopy(values[index_map[_relabel_mapping_tokens(mapping, permutation)]])
        for mapping in mapping_space()
    ]


def _inverse_map_token_state(state: dict[str, Any], permutation) -> dict[str, Any]:
    permutation = _validate_permutation(permutation, name='token permutation')
    inverse = _inverse_permutation(permutation)
    output = deepcopy(state)
    for family_field in ('incoming_family_contributions', 'sealed_family_contributions'):
        for family in ('scratch', 'source', 'local'):
            output[family_field][family] = _inverse_map_mapping_weight_vector(
                output[family_field][family], permutation,
            )
    output['effective_mapping_weights'] = _inverse_map_mapping_weight_vector(
        output['effective_mapping_weights'], permutation,
    )
    output['consistency_counts'] = _inverse_map_mapping_weight_vector(
        output['consistency_counts'], permutation,
    )
    if output['selected_second_token'] is not None:
        output['selected_second_token'] = inverse[output['selected_second_token']]
    return output


def _inverse_map_token_query(query: dict[str, Any], permutation) -> dict[str, Any]:
    permutation = _validate_permutation(permutation, name='token permutation')
    inverse = _inverse_permutation(permutation)
    output = deepcopy(query)
    for field in ('eligible_tokens', 'minimizing_tokens'):
        output[field] = sorted(inverse[token] for token in output[field])
    remapped_scores = []
    for row in output['exact_scores']:
        remapped_scores.append(dict(row, token_index=inverse[row['token_index']]))
    output['exact_scores'] = sorted(remapped_scores, key=lambda row: row['token_index'])
    if output['selected_token'] is not None:
        output['selected_token'] = inverse[output['selected_token']]
    return output


def _inverse_map_token_prediction(
    prediction: dict[str, Any], permutation,
) -> dict[str, Any]:
    permutation = _validate_permutation(permutation, name='token permutation')
    output = deepcopy(prediction)
    for field in (
        'prediction_micro', 'median_endpoints_micro', 'used_transfer',
        'lcb05_benefit_micro',
    ):
        values = output[field]
        output[field] = [deepcopy(values[permutation[old]]) for old in range(5)]
    return output


def _inverse_map_token_trace(trace: dict[str, Any], permutation) -> dict[str, Any]:
    permutation = _validate_permutation(permutation, name='token permutation')
    inverse = _inverse_permutation(permutation)
    output = deepcopy(trace)
    output['public_history'] = [
        dict(row, token_index=inverse[row['token_index']])
        for row in output['public_history']
    ]
    output['state_h1'] = _inverse_map_token_state(output['state_h1'], permutation)
    output['query_decision'] = _inverse_map_token_query(
        output['query_decision'], permutation,
    )
    output['state_final'] = _inverse_map_token_state(
        output['state_final'], permutation,
    )
    output['prediction_decision'] = _inverse_map_token_prediction(
        output['prediction_decision'], permutation,
    )
    return output


def execute_token_relabel_invariance_case(
    bank,
    target_mapping,
    permutation,
    *,
    initial_token_index: int,
    median_convention: str,
    bank_role_id: str,
) -> dict[str, Any]:
    canonical_bank = _validate_bank(bank)
    target = _validate_mapping(target_mapping)
    permutation = _validate_permutation(permutation, name='token permutation')
    initial = _strict_int(
        initial_token_index, name='initial token', minimum=0, maximum=4,
    )
    scope = next(
        row['scope_arms']
        for row in _frozen_design()['ablation_registry']['records']
        if row['ablation_id'] == 'INV_TOKEN_RELABEL'
    )
    scope_roles = next(
        row['scope_roles']
        for row in _frozen_design()['ablation_registry']['records']
        if row['ablation_id'] == 'INV_TOKEN_RELABEL'
    )
    if bank_role_id not in scope_roles:
        raise ValueError('token-relabel role is outside frozen scope')
    _validate_bank_role_provenance([bank_role_id], canonical_bank)
    relabelled_bank = tuple(
        _relabel_mapping_tokens(mapping, permutation) for mapping in canonical_bank
    )
    relabelled_target = _relabel_mapping_tokens(target, permutation)
    relabelled_initial = permutation[initial]

    baseline = []
    inverse_mapped = []
    receipts = []
    for arm_id in scope:
        h1 = [{'token_index': initial, 'prototype_index': target[initial]}]
        lexical = query_decision(
            arm_id, canonical_bank, h1, median_convention=median_convention,
        )
        selected = lexical['selected_token']
        if selected is None:
            raise AssertionError('token-relabel scope requires an H2 query')
        first, first_receipt = _run_live_semantic_trace(
            arm_id,
            canonical_bank,
            target,
            initial_token_index=initial,
            median_convention=median_convention,
            query_policy=selected,
        )
        second, second_receipt = _run_live_semantic_trace(
            arm_id,
            relabelled_bank,
            relabelled_target,
            initial_token_index=relabelled_initial,
            median_convention=median_convention,
            query_policy=permutation[selected],
        )
        baseline.append(first)
        inverse_mapped.append(_inverse_map_token_trace(second, permutation))
        receipts.extend((first_receipt, second_receipt))
    invocation = _sum_invocation_receipts(*receipts)
    invocation['query_decision_calls'] += len(scope)  # lexical exact-minimizer discovery
    baseline_hash = _semantic_sha256(baseline)
    inverse_hash = _semantic_sha256(inverse_mapped)
    return {
        'scope_arm_ids': list(scope),
        'bank_role_id': bank_role_id,
        'permutation_old_to_new': list(permutation),
        'initial_token_index': initial,
        'relabelled_initial_token_index': relabelled_initial,
        'baseline_semantic_sha256': baseline_hash,
        'inverse_mapped_semantic_sha256': inverse_hash,
        'semantic_hashes': {
            'baseline': baseline_hash,
            'intervened_inverse_mapped': inverse_hash,
        },
        'semantic_equal': baseline_hash == inverse_hash,
        'semantic_changed': baseline_hash != inverse_hash,
        'invocation_receipts': invocation,
    }


def relabel_prototype_indices_in_mapping(mapping, permutation) -> tuple[int, ...]:
    mapping = _validate_mapping(mapping)
    permutation = _validate_permutation(permutation, name='prototype permutation')
    return tuple(permutation[prototype] for prototype in mapping)


def relabel_prototype_indices_in_bank(bank, permutation) -> tuple[tuple[int, ...], ...]:
    return tuple(
        sorted(
            relabel_prototype_indices_in_mapping(mapping, permutation)
            for mapping in _validate_bank(bank)
        )
    )


def build_relabelled_prototype_table(permutation) -> list[dict[str, Any]]:
    permutation = _validate_permutation(permutation, name='prototype permutation')
    table = _prototype_table()
    return [
        {'prototype_index': permutation[old], 'vector_micro': list(table[old])}
        for old in range(5)
    ]


def _inverse_map_prototype_weight_vector(values, old_to_new) -> list[Any]:
    if len(values) != 120:
        raise ValueError('mapping-indexed vector shape drift')
    old_to_new = _validate_permutation(
        old_to_new, name='prototype permutation',
    )
    index_map = _mapping_index_map()
    return [
        deepcopy(values[index_map[relabel_prototype_indices_in_mapping(mapping, old_to_new)]])
        for mapping in mapping_space()
    ]


def _inverse_map_prototype_state(
    state: dict[str, Any], old_to_new,
) -> dict[str, Any]:
    output = deepcopy(state)
    for family_field in ('incoming_family_contributions', 'sealed_family_contributions'):
        for family in ('scratch', 'source', 'local'):
            output[family_field][family] = _inverse_map_prototype_weight_vector(
                output[family_field][family], old_to_new,
            )
    output['effective_mapping_weights'] = _inverse_map_prototype_weight_vector(
        output['effective_mapping_weights'], old_to_new,
    )
    output['consistency_counts'] = _inverse_map_prototype_weight_vector(
        output['consistency_counts'], old_to_new,
    )
    return output


def _inverse_map_prototype_trace(
    trace: dict[str, Any], old_to_new, new_to_old,
) -> dict[str, Any]:
    old_to_new = _validate_permutation(
        old_to_new, name='prototype permutation',
    )
    new_to_old = _validate_permutation(
        new_to_old, name='inverse prototype permutation',
    )
    output = deepcopy(trace)
    output['public_history'] = [
        dict(row, prototype_index=new_to_old[row['prototype_index']])
        for row in output['public_history']
    ]
    output['state_h1'] = _inverse_map_prototype_state(
        output['state_h1'], old_to_new,
    )
    output['state_final'] = _inverse_map_prototype_state(
        output['state_final'], old_to_new,
    )
    # Query tokens and physical prediction-vector coordinates are not prototype
    # labels and therefore must not be permuted.
    return output


def _validate_relabelled_prototype_table(
    prototype_table,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if type(prototype_table) is not list or len(prototype_table) != 5:
        raise ValueError('prototype relabel table must contain five rows')
    frozen = _prototype_table()
    vector_to_old = {vector: old for old, vector in enumerate(frozen)}
    new_to_old: list[int | None] = [None] * 5
    seen_old: set[int] = set()
    for row in prototype_table:
        if type(row) is not dict or set(row) != {'prototype_index', 'vector_micro'}:
            raise ValueError('prototype relabel table row shape drift')
        new = _strict_int(
            row['prototype_index'], name='prototype relabel index', minimum=0, maximum=4,
        )
        vector_raw = row['vector_micro']
        if type(vector_raw) is not list or len(vector_raw) != 4:
            raise ValueError('prototype relabel table vector shape drift')
        vector = tuple(
            _strict_int(value, name='prototype relabel vector component')
            for value in vector_raw
        )
        if vector not in vector_to_old:
            raise ValueError('prototype table must contain exact frozen vectors')
        old = vector_to_old[vector]
        if new_to_old[new] is not None or old in seen_old:
            raise ValueError('prototype table must be a bijection')
        new_to_old[new] = old
        seen_old.add(old)
    if any(old is None for old in new_to_old) or seen_old != set(range(5)):
        raise ValueError('prototype table must be a bijection')
    canonical_new_to_old = tuple(int(old) for old in new_to_old)
    old_to_new = _inverse_permutation(canonical_new_to_old)
    return old_to_new, canonical_new_to_old


def execute_prototype_relabel_invariance_case(
    relabelled_bank,
    relabelled_target_mapping,
    prototype_table,
    *,
    median_convention: str,
    bank_role_id: str,
) -> dict[str, Any]:
    old_to_new, new_to_old = _validate_relabelled_prototype_table(prototype_table)
    relabelled_bank = _validate_bank(relabelled_bank)
    relabelled_target = _validate_mapping(relabelled_target_mapping)
    canonical_bank = tuple(
        sorted(tuple(new_to_old[value] for value in mapping) for mapping in relabelled_bank)
    )
    canonical_target = tuple(new_to_old[value] for value in relabelled_target)
    registry_record = next(
        row
        for row in _frozen_design()['ablation_registry']['records']
        if row['ablation_id'] == 'INV_PROTOTYPE_RELABEL'
    )
    if bank_role_id not in registry_record['scope_roles']:
        raise ValueError('prototype-relabel role is outside frozen scope')
    _validate_bank_role_provenance([bank_role_id], canonical_bank)
    scope = registry_record['scope_arms']
    active_table_rows = sorted(
        prototype_table, key=lambda row: row['prototype_index'],
    )
    active_table = tuple(
        tuple(int(value) for value in row['vector_micro'])
        for row in active_table_rows
    )
    baseline = []
    controlled = []
    receipts = []
    for arm_id in scope:
        first, first_receipt = _run_live_semantic_trace(
            arm_id,
            canonical_bank,
            canonical_target,
            initial_token_index=0,
            median_convention=median_convention,
        )
        # The controlled path executes the genuinely relabelled bank, target,
        # public history, and table through the same production core.  Only
        # after execution are prototype-indexed receipts inverse-mapped.
        with _controlled_prototype_table_context(active_table):
            second_raw, second_receipt = _run_live_semantic_trace(
                arm_id,
                relabelled_bank,
                relabelled_target,
                initial_token_index=0,
                median_convention=median_convention,
            )
        second = _inverse_map_prototype_trace(
            second_raw, old_to_new, new_to_old,
        )
        baseline.append(first)
        controlled.append(second)
        receipts.extend((first_receipt, second_receipt))
    baseline_hash = _semantic_sha256(baseline)
    controlled_hash = _semantic_sha256(controlled)
    return {
        'scope_arm_ids': list(scope),
        'bank_role_id': bank_role_id,
        'validated_bijection': True,
        'permutation_old_to_new': list(old_to_new),
        'inverse_permutation_new_to_old': list(new_to_old),
        'baseline_semantic_sha256': baseline_hash,
        'inverse_mapped_semantic_sha256': controlled_hash,
        'semantic_hashes': {
            'baseline': baseline_hash,
            'intervened_inverse_mapped': controlled_hash,
        },
        'semantic_equal': baseline_hash == controlled_hash,
        'semantic_changed': baseline_hash != controlled_hash,
        'invocation_receipts': _sum_invocation_receipts(*receipts),
    }


def execute_eig_entropy_alias_invariance(
    bank,
    *,
    initial_token_index: int,
    initial_prototype_index: int,
    median_convention: str,
) -> dict[str, Any]:
    canonical_bank = _validate_bank(bank)
    initial = _strict_int(
        initial_token_index, name='initial token', minimum=0, maximum=4,
    )
    prototype = _strict_int(
        initial_prototype_index, name='initial prototype', minimum=0, maximum=4,
    )
    history = [{'token_index': initial, 'prototype_index': prototype}]
    inference_ids = tuple(
        next(
            row['scope_inference_ids']
            for row in _frozen_design()['ablation_registry']['records']
            if row['ablation_id'] == 'INV_EIG_ENTROPY_ALIAS'
        )
    )
    pairs = {
        'I_TRANSFER': (
            'ARM_I_TRANSFER__A_EIG__D_LCB05_FALLBACK',
            'ARM_I_TRANSFER__A_MAX_OUTCOME_ENTROPY__D_LCB05_FALLBACK',
        ),
        'I_SCRATCH': (
            'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1',
            'ARM_I_SCRATCH__A_MAX_OUTCOME_ENTROPY__D_SCRATCH_L1',
        ),
        'I_CONSISTENCY': (
            'ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN',
            'ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN',
        ),
    }
    if set(pairs) != set(inference_ids):
        raise ValueError('EIG/entropy alias inference registry drift')
    comparisons = []
    for inference_id in inference_ids:
        eig_arm, entropy_arm = pairs[inference_id]
        eig = query_decision(
            eig_arm, canonical_bank, history, median_convention=median_convention,
        )
        entropy = query_decision(
            entropy_arm, canonical_bank, history, median_convention=median_convention,
        )
        comparisons.append({
            'inference_id': inference_id,
            'eig_arm_id': eig_arm,
            'entropy_arm_id': entropy_arm,
            'exact_scores_equal': eig['exact_scores'] == entropy['exact_scores'],
            'minimizers_equal': eig['minimizing_tokens'] == entropy['minimizing_tokens'],
            'choice_equal': eig['selected_token'] == entropy['selected_token'],
            'eig_semantic_sha256': _semantic_sha256({
                'scores': eig['exact_scores'],
                'minimizers': eig['minimizing_tokens'],
                'choice': eig['selected_token'],
            }),
            'entropy_semantic_sha256': _semantic_sha256({
                'scores': entropy['exact_scores'],
                'minimizers': entropy['minimizing_tokens'],
                'choice': entropy['selected_token'],
            }),
        })
    equal = all(
        row['exact_scores_equal'] and row['minimizers_equal'] and row['choice_equal']
        for row in comparisons
    )
    eig_hashes = [row['eig_semantic_sha256'] for row in comparisons]
    entropy_hashes = [row['entropy_semantic_sha256'] for row in comparisons]
    return {
        'inference_ids': list(inference_ids),
        'comparisons': comparisons,
        'semantic_equal': equal,
        'semantic_changed': not equal,
        'semantic_hashes': {
            'eig': eig_hashes,
            'maximum_outcome_entropy': entropy_hashes,
        },
        'invocation_receipts': {
            'eig_query_decision_calls': len(inference_ids),
            'entropy_query_decision_calls': len(inference_ids),
        },
    }


def execute_registered_ablation(
    ablation_id,
    bank,
    target_mapping,
    *,
    median_convention: str,
    permutation=None,
    source_order=None,
    arm_ids=None,
    initial_token_index: int = 0,
    bank_role_id: str = 'HASH_00',
) -> dict[str, Any]:
    ids = registered_ablation_ids()
    if type(ablation_id) is not str or ablation_id not in ids:
        raise ValueError('unknown registered ablation id')
    records = {
        row['ablation_id']: row
        for row in _frozen_design()['ablation_registry']['records']
    }
    ordinary_ids = {
        row_id for row_id, row in records.items() if row['kind'] == 'ablation'
    }
    handler_ids = ordinary_ids | {
        'INV_SOURCE_ORDER', 'INV_TOKEN_RELABEL', 'INV_PROTOTYPE_RELABEL',
        'INV_EIG_ENTROPY_ALIAS',
    }
    if handler_ids != set(ids):
        raise ValueError('registered ablation dispatcher drift')
    target = _validate_mapping(target_mapping)
    default_initial = type(initial_token_index) is int and initial_token_index == 0
    default_role = type(bank_role_id) is str and bank_role_id == 'HASH_00'
    if ablation_id in ordinary_ids:
        if (
            any(value is not None for value in (permutation, source_order, arm_ids))
            or not default_initial
            or not default_role
        ):
            raise ValueError('ordinary ablation option matrix rejects unsupported argument')
        return _execute_ordinary_ablation(
            records[ablation_id],
            bank,
            target,
            median_convention=median_convention,
        )
    if ablation_id == 'INV_SOURCE_ORDER':
        if (
            permutation is not None
            or arm_ids is not None
            or not default_initial
            or not default_role
        ):
            raise ValueError('source-order option matrix requires full frozen trajectory scope')
        if source_order is None:
            source_order = enumerate_unique_source_orders(bank)[-1]
        result = execute_source_order_invariance_case(
            bank,
            target,
            source_order,
            median_convention=median_convention,
            arm_ids=None,
        )
    elif ablation_id == 'INV_TOKEN_RELABEL':
        if source_order is not None or arm_ids is not None:
            raise ValueError('token-relabel option matrix rejects unsupported argument')
        if permutation is None:
            permutation = mapping_space()[1]
        result = execute_token_relabel_invariance_case(
            bank,
            target,
            permutation,
            initial_token_index=initial_token_index,
            median_convention=median_convention,
            bank_role_id=bank_role_id,
        )
    elif ablation_id == 'INV_PROTOTYPE_RELABEL':
        if source_order is not None or arm_ids is not None or not default_initial:
            raise ValueError('prototype-relabel option matrix rejects unsupported argument')
        if permutation is None:
            permutation = mapping_space()[1]
        permutation = _validate_permutation(permutation, name='prototype permutation')
        result = execute_prototype_relabel_invariance_case(
            relabel_prototype_indices_in_bank(bank, permutation),
            relabel_prototype_indices_in_mapping(target, permutation),
            build_relabelled_prototype_table(permutation),
            median_convention=median_convention,
            bank_role_id=bank_role_id,
        )
    else:
        if (
            permutation is not None
            or source_order is not None
            or arm_ids is not None
            or not default_role
        ):
            raise ValueError('EIG/entropy option matrix rejects unsupported argument')
        result = execute_eig_entropy_alias_invariance(
            bank,
            initial_token_index=initial_token_index,
            initial_prototype_index=target[initial_token_index],
            median_convention=median_convention,
        )
    return dict(result, ablation_id=ablation_id, registered=True)


PRIMARY_ARM_ID = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
AMORTIZED_LOOKUP_SCHEMA = 'CANDIDATE_RULE_AMORTIZED_LOOKUP_V1'
PUBLIC_INPUT_SCHEMA = 'ego.v2.active_transfer.public_input.v1'
_VALIDATED_AMORTIZED_CONTENT_DIGESTS: set[str] = set()


def _clear_amortized_validation_cache() -> None:
    """Clear only the process-local verified-content cache (tests/fresh replay)."""
    _VALIDATED_AMORTIZED_CONTENT_DIGESTS.clear()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
    ).encode('ascii')


def _public_payload_from_validated(validated: dict[str, Any]) -> dict[str, Any]:
    """Return the sole canonical JSON form of a validated public input."""
    return {
        'schema_version': validated['schema_version'],
        'prototype_table': [
            {'prototype_index': index, 'vector_micro': list(vector)}
            for index, vector in validated['prototype_table']
        ],
        'source_mappings': [list(mapping) for mapping in validated['source_mappings']],
        'initial_token_index': validated['initial_token_index'],
        'public_history': [
            {
                'ordinal': ordinal,
                'token_index': token,
                'prototype_index': prototype,
            }
            for ordinal, token, prototype in validated['public_history']
        ],
        'query_counts': list(validated['query_counts']),
        'remaining_budget': validated['remaining_budget'],
        'learner_state': deepcopy(validated['learner_state']),
    }


def _canonical_public_input_bytes(public_payload: dict) -> bytes:
    validated = validate_public_input(public_payload)
    return _canonical_json_bytes(_public_payload_from_validated(validated))


def _public_state_key(public_payload_bytes: bytes) -> str:
    if type(public_payload_bytes) is not bytes:
        raise ValueError('canonical public payload must be bytes')
    return sha256(public_payload_bytes).hexdigest()


def _exact_primary_public_payload(bank, public_history) -> dict[str, Any]:
    """Construct, then validate, exact ACTIVE_TRANSFER_PUBLIC_INPUT_V1 bytes."""
    bank = _validate_bank(bank)
    history = _history_key(public_history)
    query_counts = [0] * 5
    for token, _ in history:
        query_counts[token] += 1
    payload = {
        'schema_version': PUBLIC_INPUT_SCHEMA,
        'prototype_table': [
            {'prototype_index': index, 'vector_micro': list(vector)}
            for index, vector in enumerate(_prototype_table())
        ],
        'source_mappings': [list(mapping) for mapping in bank],
        'initial_token_index': history[0][0],
        'public_history': [
            {
                'ordinal': ordinal,
                'token_index': token,
                'prototype_index': prototype,
            }
            for ordinal, (token, prototype) in enumerate(history)
        ],
        'query_counts': query_counts,
        'remaining_budget': 2 - len(history),
        'learner_state': build_state(
            PRIMARY_ARM_ID,
            bank,
            public_history,
            median_convention='midpoint_integer',
        ),
    }
    validate_public_input(payload)
    return payload


def _lookup_states_sha256(states: dict[str, bytes]) -> str:
    if type(states) is not dict:
        raise ValueError('lookup states must be an object')
    digest = sha256()
    for key in sorted(states):
        output = states[key]
        if (
            type(key) is not str or len(key) != 64
            or any(character not in '0123456789abcdef' for character in key)
        ):
            raise ValueError('lookup state key drift')
        if type(output) is not bytes:
            raise ValueError('lookup output must be canonical bytes')
        digest.update(key.encode('ascii'))
        digest.update(len(output).to_bytes(8, 'big'))
        digest.update(output)
    return digest.hexdigest()


def _lookup_table_sha256(table_without_digest: dict[str, Any]) -> str:
    metadata = {key: value for key, value in table_without_digest.items() if key != 'states'}
    digest = sha256(_canonical_json_bytes(metadata))
    digest.update(_lookup_states_sha256(table_without_digest['states']).encode('ascii'))
    return digest.hexdigest()


def _registered_bank_for_role(
    role_id: str,
    property_banks: dict[str, dict[str, Any]],
) -> tuple[tuple[int, ...], ...]:
    design = _frozen_design()
    primary_ids = set(design['bank_suite']['primary_role_ids'])
    property_ids = set(design['bank_suite']['property_predicates'])
    if role_id not in primary_ids | property_ids:
        raise ValueError('lookup role provenance drift')
    if role_id.startswith('HASH_'):
        return build_hash_bank(int(role_id.removeprefix('HASH_')))
    partitions = {
        'MULT_' + '_'.join(str(value) for value in partition): tuple(partition)
        for partition in design['bank_suite']['multiplicity_bank']['partitions']
    }
    if role_id in partitions:
        return build_multiplicity_bank(partitions[role_id])
    if role_id not in property_banks:
        raise ValueError('lookup property role provenance missing')
    return _validate_bank(property_banks[role_id]['bank'])


def _independently_recompute_amortized_states(
    bank: tuple[tuple[int, ...], ...],
) -> dict[str, bytes]:
    """Rebuild all 85 key/output pairs without trusting builder rows/digest."""
    bank = _validate_bank(bank)
    expected: dict[str, bytes] = {}
    preimages: dict[str, bytes] = {}
    for h1_outcome in range(5):
        h1 = [{'token_index': 0, 'prototype_index': h1_outcome}]
        payload = _exact_primary_public_payload(bank, h1)
        payload_bytes = _canonical_public_input_bytes(payload)
        state_key = _public_state_key(payload_bytes)
        output_bytes = _canonical_json_bytes(query_decision(
            PRIMARY_ARM_ID,
            bank,
            h1,
            median_convention='midpoint_integer',
        ))
        if state_key in expected:
            if preimages[state_key] != payload_bytes:
                raise ValueError('independent public state key collision')
            if expected[state_key] != output_bytes:
                raise ValueError('independent duplicate output mismatch')
        else:
            expected[state_key] = output_bytes
            preimages[state_key] = payload_bytes

        for second_token in range(1, 5):
            for h2_outcome in range(5):
                if h2_outcome == h1_outcome:
                    continue
                h2 = h1 + [{
                    'token_index': second_token,
                    'prototype_index': h2_outcome,
                }]
                payload = _exact_primary_public_payload(bank, h2)
                payload_bytes = _canonical_public_input_bytes(payload)
                state_key = _public_state_key(payload_bytes)
                output_bytes = _canonical_json_bytes(prediction_decision(
                    PRIMARY_ARM_ID,
                    bank,
                    h2,
                    median_convention='midpoint_integer',
                ))
                if state_key in expected:
                    if preimages[state_key] != payload_bytes:
                        raise ValueError('independent public state key collision')
                    if expected[state_key] != output_bytes:
                        raise ValueError('independent duplicate output mismatch')
                else:
                    expected[state_key] = output_bytes
                    preimages[state_key] = payload_bytes
    if len(expected) != 85:
        raise ValueError('independent public-domain count drift')
    return expected


def _independently_validate_amortized_content(table: dict[str, Any]) -> None:
    property_ids = set(_frozen_design()['bank_suite']['property_predicates'])
    needs_property_scan = any(
        role_id in property_ids
        for row in table['bank_provenance']
        for role_id in row['role_ids']
    )
    property_banks = scan_property_banks() if needs_property_scan else {}
    expected_states: dict[str, bytes] = {}
    reconstructed_bank_bytes: set[bytes] = set()
    seen_roles: set[str] = set()
    for row in table['bank_provenance']:
        role_ids = row['role_ids']
        if any(role_id in seen_roles for role_id in role_ids):
            raise ValueError('lookup alias provenance duplicated across banks')
        seen_roles.update(role_ids)
        role_banks = [
            _registered_bank_for_role(role_id, property_banks)
            for role_id in role_ids
        ]
        bank = role_banks[0]
        bank_bytes = canonical_bank_bytes(bank)
        if any(canonical_bank_bytes(other) != bank_bytes for other in role_banks[1:]):
            raise ValueError('registered provenance alias set mismatch')
        bank_hash = sha256(bank_bytes).hexdigest()
        if bank_hash != row['canonical_bank_sha256']:
            raise ValueError('registered provenance bank mismatch')
        if bank_bytes in reconstructed_bank_bytes:
            raise ValueError('registered provenance alias groups not deduplicated')
        reconstructed_bank_bytes.add(bank_bytes)

        bank_states = _independently_recompute_amortized_states(bank)
        if len(bank_states) != row['state_count']:
            raise ValueError('independent provenance state count mismatch')
        for state_key, output_bytes in bank_states.items():
            if state_key in expected_states:
                if expected_states[state_key] != output_bytes:
                    raise ValueError('independent cross-bank output mismatch')
                raise ValueError('independent cross-bank state duplication')
            expected_states[state_key] = output_bytes
    if expected_states != table['states']:
        raise ValueError('independent live recomputation mismatch')
    if len(expected_states) != table['state_count']:
        raise ValueError('independent table state count mismatch')


def _validate_amortized_table(table: dict[str, Any]) -> None:
    required = {
        'schema_version', 'builder_id', 'primary_arm_id',
        'public_input_schema_version', 'bank_provenance',
        'phase_state_counts', 'state_count', 'states', 'table_sha256',
    }
    if type(table) is not dict or set(table) != required:
        raise ValueError('lookup table schema drift')
    if table['schema_version'] != AMORTIZED_LOOKUP_SCHEMA:
        raise ValueError('lookup table schema drift')
    if table['builder_id'] != 'CANDIDATE_RULE_AMORTIZED_LOOKUP':
        raise ValueError('lookup builder drift')
    if table['primary_arm_id'] != PRIMARY_ARM_ID:
        raise ValueError('lookup primary arm drift')
    if table['public_input_schema_version'] != PUBLIC_INPUT_SCHEMA:
        raise ValueError('lookup public schema drift')
    phase_counts = table['phase_state_counts']
    if (
        type(phase_counts) is not dict or set(phase_counts) != {'H1', 'H2'}
        or any(type(phase_counts[key]) is not int or phase_counts[key] < 0 for key in phase_counts)
    ):
        raise ValueError('lookup phase counts drift')
    if type(table['states']) is not dict:
        raise ValueError('lookup states must be an object')
    count = _strict_int(table['state_count'], name='lookup state count', minimum=1)
    if count != len(table['states']) or count != phase_counts['H1'] + phase_counts['H2']:
        raise ValueError('lookup state count drift')
    provenance = table['bank_provenance']
    if type(provenance) is not list or not provenance:
        raise ValueError('lookup bank provenance drift')
    previous_hash = ''
    total_expected = 0
    for row in provenance:
        if type(row) is not dict or set(row) != {
            'canonical_bank_sha256', 'role_ids', 'state_count',
        }:
            raise ValueError('lookup bank provenance drift')
        bank_hash = row['canonical_bank_sha256']
        if (
            type(bank_hash) is not str or len(bank_hash) != 64
            or any(character not in '0123456789abcdef' for character in bank_hash)
            or bank_hash <= previous_hash
        ):
            raise ValueError('lookup bank provenance ordering drift')
        previous_hash = bank_hash
        role_ids = row['role_ids']
        registered_roles = set(_frozen_design()['bank_suite']['primary_role_ids']) | set(
            _frozen_design()['bank_suite']['property_predicates']
        )
        if (
            type(role_ids) is not list or not role_ids
            or role_ids != sorted(role_ids) or len(role_ids) != len(set(role_ids))
            or any(
                type(role_id) is not str or role_id not in registered_roles
                for role_id in role_ids
            )
        ):
            raise ValueError('lookup role provenance drift')
        row_count = _strict_int(row['state_count'], name='lookup bank state count', minimum=1)
        if row_count != 85:
            raise ValueError('lookup bank public-domain count drift')
        total_expected += row_count
    if total_expected != count:
        raise ValueError('lookup provenance state count drift')
    if phase_counts != {'H1': 5 * len(provenance), 'H2': 80 * len(provenance)}:
        raise ValueError('lookup phase-domain count drift')
    expected_digest = _lookup_table_sha256({
        key: value for key, value in table.items() if key != 'table_sha256'
    })
    if table['table_sha256'] != expected_digest:
        raise ValueError('lookup table integrity mismatch')
    # The caller-provided digest is only a corruption/content-address receipt.
    # A newly re-signed forgery has a new digest and must survive independent
    # registered-bank reconstruction plus live primary recomputation before it
    # can enter this process-local success cache.
    if expected_digest in _VALIDATED_AMORTIZED_CONTENT_DIGESTS:
        return
    _independently_validate_amortized_content(table)
    _VALIDATED_AMORTIZED_CONTENT_DIGESTS.add(expected_digest)


def _validate_canonical_output_bytes(output: bytes, phase: str) -> dict[str, Any]:
    try:
        decoded = json.loads(output.decode('ascii'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('lookup output decoding failed') from exc
    if _canonical_json_bytes(decoded) != output:
        raise ValueError('lookup output is not canonical bytes')
    if type(decoded) is not dict or decoded.get('arm_id') != PRIMARY_ARM_ID:
        raise ValueError('lookup output primary arm drift')
    expected_schema = 'QUERY_DECISION_V1' if phase == 'H1' else 'PREDICTION_DECISION_V1'
    if decoded.get('schema_version') != expected_schema:
        raise ValueError('lookup output phase drift')
    expected_keys = (
        {
            'schema_version', 'arm_id', 'eligible_tokens', 'score_kind',
            'exact_scores', 'minimizing_tokens', 'selected_token', 'tie_rule',
        }
        if phase == 'H1'
        else {
            'schema_version', 'arm_id', 'prediction_micro',
            'median_endpoints_micro', 'used_transfer', 'lcb05_benefit_micro',
        }
    )
    if set(decoded) != expected_keys:
        raise ValueError('lookup output schema drift')
    if phase == 'H1':
        for name in ('eligible_tokens', 'minimizing_tokens'):
            values = decoded[name]
            if (
                type(values) is not list or len(values) != len(set(values))
                or any(type(value) is not int or value < 0 or value > 4 for value in values)
            ):
                raise ValueError('lookup query token shape drift')
        scores = decoded['exact_scores']
        if (
            type(scores) is not list
            or any(
                type(row) is not dict or set(row) != {'token_index', 'int_score'}
                or type(row['token_index']) is not int
                or row['token_index'] < 0 or row['token_index'] > 4
                or type(row['int_score']) is not int
                for row in scores
            )
            or [row['token_index'] for row in scores] != decoded['eligible_tokens']
        ):
            raise ValueError('lookup query score shape drift')
        if (
            decoded['score_kind'] != 'l1_risk_integer'
            or type(decoded['tie_rule']) is not str
            or type(decoded['selected_token']) is not int
            or decoded['selected_token'] not in decoded['minimizing_tokens']
            or not set(decoded['minimizing_tokens']).issubset(decoded['eligible_tokens'])
        ):
            raise ValueError('lookup query decision drift')
    else:
        predictions = decoded['prediction_micro']
        endpoints = decoded['median_endpoints_micro']
        used_transfer = decoded['used_transfer']
        lcb05 = decoded['lcb05_benefit_micro']
        if (
            type(predictions) is not list or len(predictions) != 5
            or any(
                type(row) is not list or len(row) != 4
                or any(type(value) is not int for value in row)
                for row in predictions
            )
            or type(endpoints) is not list or len(endpoints) != 5
            or any(
                type(row) is not list or len(row) != 4
                or any(
                    type(pair) is not list or len(pair) != 2
                    or any(type(value) is not int for value in pair)
                    or pair[0] > pair[1]
                    for pair in row
                )
                for row in endpoints
            )
            or type(used_transfer) is not list or len(used_transfer) != 5
            or any(type(value) is not bool for value in used_transfer)
            or type(lcb05) is not list or len(lcb05) != 5
            or any(value is not None and type(value) is not int for value in lcb05)
        ):
            raise ValueError('lookup prediction shape drift')
    return decoded


def _amortized_live_query_output(bank, public_history) -> dict[str, Any]:
    return query_decision(
        PRIMARY_ARM_ID,
        bank,
        public_history,
        median_convention='midpoint_integer',
    )


def _amortized_live_prediction_output(bank, public_history) -> dict[str, Any]:
    return prediction_decision(
        PRIMARY_ARM_ID,
        bank,
        public_history,
        median_convention='midpoint_integer',
    )


def build_amortized_lookup(banks) -> dict[str, Any]:
    """Build the tautological primary-rule ceiling over bounded public states."""
    if type(banks) is not dict or not banks:
        raise ValueError('banks must be a nonempty exact role mapping')
    grouped: dict[bytes, dict[str, Any]] = {}
    for role_id, supplied_bank in banks.items():
        if type(role_id) is not str or not role_id:
            raise ValueError('bank role must be an exact registered role id')
        bank = _validate_bank(supplied_bank)
        bank_bytes = canonical_bank_bytes(bank)
        group = grouped.setdefault(bank_bytes, {'bank': bank, 'role_ids': []})
        group['role_ids'].append(role_id)

    canonical_groups = []
    for bank_bytes, group in grouped.items():
        role_ids = sorted(group['role_ids'])
        _validate_bank_role_provenance(role_ids, group['bank'])
        canonical_groups.append((sha256(bank_bytes).hexdigest(), role_ids, group['bank']))
    canonical_groups.sort(key=lambda row: row[0])

    states: dict[str, bytes] = {}
    state_preimages: dict[str, bytes] = {}
    phase_counts = {'H1': 0, 'H2': 0}
    bank_provenance = []
    for bank_hash, role_ids, bank in canonical_groups:
        bank_state_count = 0
        for h1_outcome in range(5):
            h1 = [{'token_index': 0, 'prototype_index': h1_outcome}]
            public_payload = _exact_primary_public_payload(bank, h1)
            public_bytes = _canonical_public_input_bytes(public_payload)
            state_key = _public_state_key(public_bytes)
            output = _amortized_live_query_output(bank, h1)
            output_bytes = _canonical_json_bytes(output)
            if state_key in states:
                if state_preimages[state_key] != public_bytes:
                    raise ValueError('public state key collision')
                if states[state_key] != output_bytes:
                    raise ValueError('public state duplicate output mismatch')
            else:
                states[state_key] = output_bytes
                state_preimages[state_key] = public_bytes
                phase_counts['H1'] += 1
                bank_state_count += 1

            for second_token in range(1, 5):
                for h2_outcome in range(5):
                    # Every hypothesis is a permutation: two distinct tokens
                    # cannot have the same prototype.  These 20 nominal H2
                    # pairs have zero likelihood even under uniform scratch,
                    # so they are not legal public states.
                    if h2_outcome == h1_outcome:
                        continue
                    h2 = h1 + [
                        {
                            'token_index': second_token,
                            'prototype_index': h2_outcome,
                        }
                    ]
                    public_payload = _exact_primary_public_payload(bank, h2)
                    public_bytes = _canonical_public_input_bytes(public_payload)
                    state_key = _public_state_key(public_bytes)
                    output = _amortized_live_prediction_output(bank, h2)
                    output_bytes = _canonical_json_bytes(output)
                    if state_key in states:
                        if state_preimages[state_key] != public_bytes:
                            raise ValueError('public state key collision')
                        if states[state_key] != output_bytes:
                            raise ValueError('public state duplicate output mismatch')
                    else:
                        states[state_key] = output_bytes
                        state_preimages[state_key] = public_bytes
                        phase_counts['H2'] += 1
                        bank_state_count += 1
        if bank_state_count != 85:
            raise ValueError('canonical bank public-domain count drift')
        bank_provenance.append({
            'canonical_bank_sha256': bank_hash,
            'role_ids': role_ids,
            'state_count': bank_state_count,
        })

    table = {
        'schema_version': AMORTIZED_LOOKUP_SCHEMA,
        'builder_id': 'CANDIDATE_RULE_AMORTIZED_LOOKUP',
        'primary_arm_id': PRIMARY_ARM_ID,
        'public_input_schema_version': PUBLIC_INPUT_SCHEMA,
        'bank_provenance': bank_provenance,
        'phase_state_counts': phase_counts,
        'state_count': len(states),
        'states': states,
    }
    table['table_sha256'] = _lookup_table_sha256(table)
    _validate_amortized_table(table)
    return table


def lookup_query_or_prediction(table: dict, public_payload: dict) -> dict[str, Any]:
    validated = validate_public_input(public_payload)
    if validated['learner_state']['arm_id'] != PRIMARY_ARM_ID:
        raise ValueError('lookup requires the canonical primary arm')
    if validated['remaining_budget'] == 1 and len(validated['public_history']) == 1:
        phase = 'H1'
    elif validated['remaining_budget'] == 0 and len(validated['public_history']) == 2:
        phase = 'H2'
    else:
        raise ValueError('lookup public phase drift')
    _validate_amortized_table(table)
    public_bytes = _canonical_json_bytes(_public_payload_from_validated(validated))
    state_key = _public_state_key(public_bytes)
    if state_key not in table['states']:
        raise KeyError('unknown valid public state')
    return _validate_canonical_output_bytes(table['states'][state_key], phase)


_ARM_TARGET_METRIC_KEYS = {
    'schema_version', 'arm_id', 'target_mapping', 'selected_query_token',
    'public_selected_query_token', 'query_decision', 'public_query_decision',
    'prediction_decision', 'public_prediction_decision',
    'same_history_scratch_prediction_decision', 'used_transfer',
    'candidate_own_unqueried_tokens', 'baseline_own_unqueried_tokens',
    'common_unqueried_tokens', 'candidate_token_losses_raw',
    'baseline_token_losses_raw', 'same_history_scratch_token_losses_raw',
    'candidate_full_loss_raw', 'baseline_full_loss_raw',
    'candidate_own_unqueried_loss_raw', 'baseline_own_unqueried_loss_raw',
    'candidate_common_unqueried_loss_raw', 'baseline_common_unqueried_loss_raw',
    'same_history_scratch_loss_raw', 'full_improvement_raw', 'common_raw',
    'query_asymmetry_raw', 'same_history_forward_raw', 'metric_denominators',
    'metric_rationals',
}
_QUERY_DECISION_KEYS = {
    'schema_version', 'arm_id', 'eligible_tokens', 'score_kind', 'exact_scores',
    'minimizing_tokens', 'selected_token', 'tie_rule',
}
_PREDICTION_DECISION_KEYS = {
    'schema_version', 'arm_id', 'prediction_micro', 'median_endpoints_micro',
    'used_transfer', 'lcb05_benefit_micro',
}
_METRIC_DENOMINATOR_KEYS = {
    'full', 'own_unqueried', 'common_unqueried', 'same_history_forward',
}
_METRIC_RATIONAL_KEYS = {
    'candidate_full_endpoint_mae', 'baseline_full_endpoint_mae',
    'full_endpoint_improvement', 'candidate_own_unqueried_forward_mae',
    'baseline_own_unqueried_forward_mae',
    'candidate_common_unqueried_forward_mae',
    'baseline_common_unqueried_forward_mae',
    'common_unqueried_forward_improvement',
    'candidate_same_history_forward_mae',
    'same_history_scratch_forward_mae', 'same_history_forward_improvement',
    'common_contribution_to_full_improvement',
    'query_asymmetry_contribution_to_full_improvement',
}


def _strict_optional_token(value: Any, *, name: str) -> int | None:
    if value is None:
        return None
    return _strict_int(value, name=name, minimum=0, maximum=4)


def _validate_query_decision_metric_object(value: Any, *, expected_arm_id: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _QUERY_DECISION_KEYS:
        raise ValueError('query decision metric keys drift')
    if value['schema_version'] != 'QUERY_DECISION_V1' or value['arm_id'] != expected_arm_id:
        raise ValueError('query decision metric identity drift')
    eligible = value['eligible_tokens']
    minimizing = value['minimizing_tokens']
    if type(eligible) is not list or type(minimizing) is not list:
        raise ValueError('query token list shape drift')
    eligible_tuple = tuple(
        _strict_int(token, name='eligible token', minimum=0, maximum=4)
        for token in eligible
    )
    minimizing_tuple = tuple(
        _strict_int(token, name='minimizing token', minimum=0, maximum=4)
        for token in minimizing
    )
    if len(set(eligible_tuple)) != len(eligible_tuple) or tuple(sorted(eligible_tuple)) != eligible_tuple:
        raise ValueError('eligible query tokens drift')
    if len(set(minimizing_tuple)) != len(minimizing_tuple) or any(
        token not in eligible_tuple for token in minimizing_tuple
    ):
        raise ValueError('minimizing query tokens drift')
    scores = value['exact_scores']
    if type(scores) is not list:
        raise ValueError('query exact scores shape drift')
    score_tokens = []
    for row in scores:
        if type(row) is not dict or set(row) != {'token_index', 'int_score'}:
            raise ValueError('query score row keys drift')
        score_tokens.append(
            _strict_int(row['token_index'], name='score token', minimum=0, maximum=4)
        )
        _strict_int(row['int_score'], name='integer query score', minimum=0)
    if score_tokens != list(eligible_tuple):
        raise ValueError('query score token ordering drift')
    if scores:
        minimum = min(row['int_score'] for row in scores)
        expected_minimizing = tuple(
            row['token_index'] for row in scores if row['int_score'] == minimum
        )
        if minimizing_tuple != expected_minimizing:
            raise ValueError('minimizing query tokens do not match exact scores')
    selected = _strict_optional_token(value['selected_token'], name='selected query token')
    if selected is None:
        if minimizing_tuple or eligible_tuple or scores:
            raise ValueError('null query selection semantic drift')
    elif selected not in minimizing_tuple:
        raise ValueError('selected query is not minimizing')
    score_kinds = set(_frozen_design()['closed_schemas']['QUERY_DECISION_V1']['score_kinds'])
    if value['score_kind'] not in score_kinds or value['tie_rule'] not in {
        'none', 'lexical_minimum', 'enumerated_exact_minimizer',
    }:
        raise ValueError('query string field drift')
    return value


def _validate_prediction_decision_metric_object(value: Any, *, expected_arm_id: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PREDICTION_DECISION_KEYS:
        raise ValueError('prediction decision metric keys drift')
    if value['schema_version'] != 'PREDICTION_DECISION_V1' or value['arm_id'] != expected_arm_id:
        raise ValueError('prediction decision metric identity drift')
    predictions = value['prediction_micro']
    endpoints = value['median_endpoints_micro']
    used_transfer = value['used_transfer']
    lcb = value['lcb05_benefit_micro']
    if type(predictions) is not list or len(predictions) != 5:
        raise ValueError('prediction shape drift')
    if type(endpoints) is not list or len(endpoints) != 5:
        raise ValueError('prediction endpoint shape drift')
    for prediction_row, endpoint_row in zip(predictions, endpoints):
        if type(prediction_row) is not list or len(prediction_row) != 4:
            raise ValueError('prediction shape drift')
        if type(endpoint_row) is not list or len(endpoint_row) != 4:
            raise ValueError('prediction endpoint shape drift')
        for prediction_component, endpoint in zip(prediction_row, endpoint_row):
            prediction_component = _strict_int(prediction_component, name='prediction component')
            if type(endpoint) is not list or len(endpoint) != 2:
                raise ValueError('prediction endpoint shape drift')
            lower = _strict_int(endpoint[0], name='lower median endpoint')
            upper = _strict_int(endpoint[1], name='upper median endpoint')
            if not lower <= prediction_component <= upper:
                raise ValueError('prediction outside median endpoints')
    if type(used_transfer) is not list or len(used_transfer) != 5 or any(
        type(flag) is not bool for flag in used_transfer
    ):
        raise ValueError('used-transfer shape drift')
    if type(lcb) is not list or len(lcb) != 5:
        raise ValueError('LCB shape drift')
    for value_or_null in lcb:
        if value_or_null is not None:
            _strict_int(value_or_null, name='LCB benefit')
    return value


def _validate_token_index_list(value: Any, *, name: str) -> list[int]:
    if type(value) is not list:
        raise ValueError(f'{name} shape drift')
    tokens = [
        _strict_int(token, name=name, minimum=0, maximum=4) for token in value
    ]
    if len(set(tokens)) != len(tokens) or tokens != sorted(tokens):
        raise ValueError(f'{name} ordering drift')
    return tokens


def _validate_loss_vector(value: Any, *, name: str) -> list[int]:
    if type(value) is not list or len(value) != 5:
        raise ValueError(f'{name} loss vector shape drift')
    return [_strict_int(row, name=name, minimum=0) for row in value]


def validate_arm_target_metric(metric: Any) -> dict[str, Any]:
    """Recursively validate and arithmetically recompute one trajectory metric.

    This is a shared C3 primitive, not an evidence verdict. C3B must still bind
    the row to an execution-plan ledger and formal prerequisite packet.
    """
    if type(metric) is not dict or set(metric) != _ARM_TARGET_METRIC_KEYS:
        raise ValueError('ARM target metric keys drift')
    if metric['schema_version'] != 'ARM_TARGET_METRIC_V1':
        raise ValueError('ARM target metric schema drift')
    arm_id = metric['arm_id']
    if type(arm_id) is not str or _arm_record(arm_id)['kind'] != 'trajectory':
        raise ValueError('ARM target metric arm drift')
    target = _validate_mapping(metric['target_mapping'])
    q_candidate = _strict_optional_token(
        metric['selected_query_token'], name='candidate selected query',
    )
    q_public = _strict_optional_token(
        metric['public_selected_query_token'], name='PUBLIC selected query',
    )
    if q_candidate == 0 or q_public is None or q_public == 0:
        raise ValueError('metric selected query semantic drift')
    query = _validate_query_decision_metric_object(
        metric['query_decision'], expected_arm_id=arm_id,
    )
    public_query = _validate_query_decision_metric_object(
        metric['public_query_decision'], expected_arm_id=PUBLIC_ARM_ID,
    )
    if query['selected_token'] != q_candidate or public_query['selected_token'] != q_public:
        raise ValueError('metric/query selected token mismatch')
    candidate_prediction = _validate_prediction_decision_metric_object(
        metric['prediction_decision'], expected_arm_id=arm_id,
    )
    public_prediction = _validate_prediction_decision_metric_object(
        metric['public_prediction_decision'], expected_arm_id=PUBLIC_ARM_ID,
    )
    same_history_prediction = _validate_prediction_decision_metric_object(
        metric['same_history_scratch_prediction_decision'], expected_arm_id=PUBLIC_ARM_ID,
    )
    if metric['used_transfer'] != candidate_prediction['used_transfer']:
        raise ValueError('metric used-transfer semantic drift')

    candidate_own = _validate_token_index_list(
        metric['candidate_own_unqueried_tokens'], name='candidate own token',
    )
    baseline_own = _validate_token_index_list(
        metric['baseline_own_unqueried_tokens'], name='baseline own token',
    )
    common = _validate_token_index_list(
        metric['common_unqueried_tokens'], name='common token',
    )
    expected_candidate_own = [token for token in range(1, 5) if token != q_candidate]
    expected_baseline_own = [token for token in range(1, 5) if token != q_public]
    expected_common = [
        token for token in range(1, 5) if token != q_candidate and token != q_public
    ]
    if candidate_own != expected_candidate_own or baseline_own != expected_baseline_own or common != expected_common:
        raise ValueError('metric forward token set semantic drift')

    candidate_losses = _validate_loss_vector(
        metric['candidate_token_losses_raw'], name='candidate token',
    )
    baseline_losses = _validate_loss_vector(
        metric['baseline_token_losses_raw'], name='baseline token',
    )
    same_history_losses = _validate_loss_vector(
        metric['same_history_scratch_token_losses_raw'], name='same-history token',
    )
    expected_candidate_losses = _token_losses(candidate_prediction, target)
    expected_baseline_losses = _token_losses(public_prediction, target)
    expected_same_history_losses = _token_losses(same_history_prediction, target)
    if candidate_losses != expected_candidate_losses or baseline_losses != expected_baseline_losses or same_history_losses != expected_same_history_losses:
        raise ValueError('metric raw loss semantic drift')
    observed_candidate = {0} | ({q_candidate} if q_candidate is not None else set())
    observed_public = {0, q_public}
    for token in observed_candidate:
        if tuple(candidate_prediction['prediction_micro'][token]) != _prototype_table()[target[token]]:
            raise ValueError('candidate observed copy semantic drift')
        if tuple(same_history_prediction['prediction_micro'][token]) != _prototype_table()[target[token]]:
            raise ValueError('same-history observed copy semantic drift')
    for token in observed_public:
        if tuple(public_prediction['prediction_micro'][token]) != _prototype_table()[target[token]]:
            raise ValueError('PUBLIC observed copy semantic drift')

    expected_raw = {
        'candidate_full_loss_raw': sum(candidate_losses),
        'baseline_full_loss_raw': sum(baseline_losses),
        'candidate_own_unqueried_loss_raw': sum(candidate_losses[token] for token in candidate_own),
        'baseline_own_unqueried_loss_raw': sum(baseline_losses[token] for token in baseline_own),
        'candidate_common_unqueried_loss_raw': sum(candidate_losses[token] for token in common),
        'baseline_common_unqueried_loss_raw': sum(baseline_losses[token] for token in common),
        'same_history_scratch_loss_raw': sum(same_history_losses[token] for token in candidate_own),
    }
    expected_raw['full_improvement_raw'] = (
        expected_raw['baseline_full_loss_raw'] - expected_raw['candidate_full_loss_raw']
    )
    expected_raw['common_raw'] = (
        expected_raw['baseline_common_unqueried_loss_raw']
        - expected_raw['candidate_common_unqueried_loss_raw']
    )
    expected_raw['query_asymmetry_raw'] = (
        0 if q_candidate == q_public else
        (0 if q_candidate is None else baseline_losses[q_candidate])
        - candidate_losses[q_public]
    )
    expected_raw['same_history_forward_raw'] = (
        expected_raw['same_history_scratch_loss_raw']
        - expected_raw['candidate_own_unqueried_loss_raw']
    )
    for field, expected in expected_raw.items():
        if _strict_int(metric[field], name=field) != expected:
            raise ValueError('metric raw loss semantic drift')
    if expected_raw['full_improvement_raw'] != expected_raw['common_raw'] + expected_raw['query_asymmetry_raw']:
        raise ValueError('metric decomposition identity drift')

    denominators = metric['metric_denominators']
    if type(denominators) is not dict or set(denominators) != _METRIC_DENOMINATOR_KEYS:
        raise ValueError('metric denominator keys drift')
    expected_denominators = {
        'full': 20,
        'own_unqueried': 4 * len(candidate_own),
        'common_unqueried': 4 * len(common),
        'same_history_forward': 4 * len(candidate_own),
    }
    if denominators != expected_denominators:
        raise ValueError('metric denominator semantic drift')
    rationals = metric['metric_rationals']
    if type(rationals) is not dict or set(rationals) != _METRIC_RATIONAL_KEYS:
        raise ValueError('metric rational keys drift')
    for row in rationals.values():
        _decode_rational(row)
    d = expected_denominators
    expected_rationals = {
        'candidate_full_endpoint_mae': _normalized_rational(expected_raw['candidate_full_loss_raw'], d['full']),
        'baseline_full_endpoint_mae': _normalized_rational(expected_raw['baseline_full_loss_raw'], d['full']),
        'full_endpoint_improvement': _normalized_rational(expected_raw['full_improvement_raw'], d['full']),
        'candidate_own_unqueried_forward_mae': _normalized_rational(expected_raw['candidate_own_unqueried_loss_raw'], d['own_unqueried']),
        'baseline_own_unqueried_forward_mae': _normalized_rational(expected_raw['baseline_own_unqueried_loss_raw'], 12),
        'candidate_common_unqueried_forward_mae': _normalized_rational(expected_raw['candidate_common_unqueried_loss_raw'], d['common_unqueried']),
        'baseline_common_unqueried_forward_mae': _normalized_rational(expected_raw['baseline_common_unqueried_loss_raw'], d['common_unqueried']),
        'common_unqueried_forward_improvement': _normalized_rational(expected_raw['common_raw'], d['common_unqueried']),
        'candidate_same_history_forward_mae': _normalized_rational(expected_raw['candidate_own_unqueried_loss_raw'], d['same_history_forward']),
        'same_history_scratch_forward_mae': _normalized_rational(expected_raw['same_history_scratch_loss_raw'], d['same_history_forward']),
        'same_history_forward_improvement': _normalized_rational(expected_raw['same_history_forward_raw'], d['same_history_forward']),
        'common_contribution_to_full_improvement': _normalized_rational(expected_raw['common_raw'], 20),
        'query_asymmetry_contribution_to_full_improvement': _normalized_rational(expected_raw['query_asymmetry_raw'], 20),
    }
    if rationals != expected_rationals:
        raise ValueError('metric rational semantic drift')
    return metric


def _validate_and_live_recompute_metric(
    stored_metric: Any,
    *,
    bank,
    target_mapping,
    arm_id: str,
    median_convention: str,
    query_policy=None,
) -> dict[str, Any]:
    validated = validate_arm_target_metric(stored_metric)
    canonical_target = _validate_mapping(target_mapping)
    if validated['arm_id'] != arm_id or tuple(validated['target_mapping']) != canonical_target:
        raise ValueError('live metric context mismatch')
    live = evaluate_target(
        _validate_bank(bank), canonical_target, arm_id,
        median_convention=median_convention, query_policy=query_policy,
    )
    validate_arm_target_metric(live)
    if _canonical_json_bytes(validated) != _canonical_json_bytes(live):
        raise ValueError('live metric recomputation mismatch')
    return live


def _pairwise_common_mae(left_metric: Any, right_metric: Any) -> dict[str, Any]:
    left = validate_arm_target_metric(left_metric)
    right = validate_arm_target_metric(right_metric)
    return _pairwise_common_mae_validated(left, right)


def _pairwise_common_mae_validated(
    left: dict[str, Any], right: dict[str, Any],
) -> dict[str, Any]:
    if left['target_mapping'] != right['target_mapping']:
        raise ValueError('pairwise target mismatch')
    excluded = {
        token for token in (
            left['selected_query_token'], right['selected_query_token'],
        ) if token is not None
    }
    tokens = [token for token in range(1, 5) if token not in excluded]
    denominator = 4 * len(tokens)
    if denominator <= 0:
        raise ValueError('empty pairwise common set')
    left_raw = sum(left['candidate_token_losses_raw'][token] for token in tokens)
    right_raw = sum(right['candidate_token_losses_raw'][token] for token in tokens)
    return {
        'common_tokens': tokens,
        'component_denominator': denominator,
        'left_mae': _normalized_rational(left_raw, denominator),
        'right_mae': _normalized_rational(right_raw, denominator),
        'left_advantage': _normalized_rational(right_raw - left_raw, denominator),
    }


def _threshold_fraction(name: str) -> Fraction:
    value = _frozen_design()['thresholds'][name]
    if type(value) is not str:
        raise ValueError('threshold representation drift')
    return Fraction(value)


LEXICAL_QUERY_POLICY = 'LEXICAL_RECOMPUTE'
_ADMITTED_LIVE_BOUND_DIGESTS: set[str] = set()


class LiveBoundMetricIndex:
    """Opaque content-addressed handle returned only by the canonical builder."""

    __slots__ = ('payload_bytes', 'digest_sha256')

    def __new__(cls, *args, **kwargs):
        raise ValueError('live-bound metric indexes require the canonical builder')


class _ValidatedLiveBoundMetricView:
    __slots__ = (
        'expected_arm_id', 'median_convention', 'role_banks',
        'candidate_query_policies', 'public_query_policies', 'rows_by_role',
        'digest_sha256',
    )

    def __init__(
        self,
        *,
        expected_arm_id: str,
        median_convention: str,
        role_banks: dict[str, tuple[tuple[int, ...], ...]],
        candidate_query_policies: dict[str, tuple[int | None, ...]],
        public_query_policies: dict[str, tuple[int | None, ...]],
        rows_by_role: dict[str, dict[tuple[int, ...], dict[str, Any]]],
        digest_sha256: str,
    ) -> None:
        self.expected_arm_id = expected_arm_id
        self.median_convention = median_convention
        self.role_banks = role_banks
        self.candidate_query_policies = candidate_query_policies
        self.public_query_policies = public_query_policies
        self.rows_by_role = rows_by_role
        self.digest_sha256 = digest_sha256


def _clear_live_bound_metric_index_admission_cache_for_tests() -> None:
    _ADMITTED_LIVE_BOUND_DIGESTS.clear()


def _new_admitted_live_bound_metric_index(
    payload_bytes: bytes,
    digest_sha256: str,
) -> LiveBoundMetricIndex:
    index = object.__new__(LiveBoundMetricIndex)
    object.__setattr__(index, 'payload_bytes', payload_bytes)
    object.__setattr__(index, 'digest_sha256', digest_sha256)
    return index


def _primary_role_ids() -> tuple[str, ...]:
    role_ids = tuple(_frozen_design()['bank_suite']['primary_role_ids'])
    if len(role_ids) != 75 or len(set(role_ids)) != 75:
        raise ValueError('exact 75 frozen primary roles required')
    return role_ids


def _reconstruct_primary_role_bank(role_id: str) -> tuple[tuple[int, ...], ...]:
    primary_ids = _primary_role_ids()
    if type(role_id) is not str or role_id not in primary_ids:
        raise ValueError('exact registered primary role id required')
    if role_id.startswith('HASH_'):
        return build_hash_bank(int(role_id.removeprefix('HASH_')))
    partitions = {
        'MULT_' + '_'.join(str(value) for value in partition): tuple(partition)
        for partition in _frozen_design()['bank_suite']['multiplicity_bank']['partitions']
    }
    if role_id not in partitions:
        raise ValueError('registered primary role reconstruction drift')
    return build_multiplicity_bank(partitions[role_id])


def _resolve_role_query_policy(
    role_id: str,
    bank: tuple[tuple[int, ...], ...],
    arm_id: str,
    policy_spec: Any,
    *,
    median_convention: str,
) -> tuple[int | None, ...]:
    if policy_spec == LEXICAL_QUERY_POLICY:
        # Exercise every lexical leaf now, but retain ``None`` as the exact
        # evaluator input. An explicit integer has different tie provenance.
        for outcome in range(5):
            decision = query_decision(
                arm_id,
                bank,
                [{'token_index': 0, 'prototype_index': outcome}],
                median_convention=median_convention,
            )
            if decision['selected_token'] is None:
                raise ValueError('live-bound gate arm must have a five-leaf query policy')
        return (None, None, None, None, None)
    if not isinstance(policy_spec, (list, tuple)) or len(policy_spec) != 5:
        raise ValueError('complete five-leaf query policy required for every role')
    choices = tuple(
        _strict_int(value, name=f'{role_id} query policy leaf', minimum=0, maximum=4)
        for value in policy_spec
    )
    for outcome, selected in enumerate(choices):
        query_decision(
            arm_id,
            bank,
            [{'token_index': 0, 'prototype_index': outcome}],
            median_convention=median_convention,
            query_policy=selected,
        )
    return choices


def _live_recompute_role_metric_rows(
    role_id: str,
    bank: Any,
    stored_rows: dict[Any, Any],
    *,
    expected_arm_id: str,
    median_convention: str,
    candidate_query_policy_spec: Any,
    public_query_policy_spec: Any,
) -> dict[str, Any]:
    """Single production per-role path used by the full-suite builder."""
    if type(role_id) is not str or role_id not in _primary_role_ids():
        raise ValueError('exact registered primary role id required')
    canonical_bank = _validate_bank(bank)
    if canonical_bank_bytes(canonical_bank) != canonical_bank_bytes(
        _reconstruct_primary_role_bank(role_id)
    ):
        raise ValueError('registered primary role canonical bank provenance mismatch')
    candidate_query_policy = _resolve_role_query_policy(
        role_id, canonical_bank, expected_arm_id, candidate_query_policy_spec,
        median_convention=median_convention,
    )
    public_query_policy = _resolve_role_query_policy(
        role_id, canonical_bank, PUBLIC_ARM_ID, public_query_policy_spec,
        median_convention=median_convention,
    )
    normalized = _normalize_role_metric_rows(
        {role_id: canonical_bank}, {role_id: stored_rows}, require_all_targets=True,
    )[role_id]
    live_rows = {}
    for target in mapping_space():
        outcome = target[0]
        live_rows[target] = _validate_and_live_recompute_metric(
            normalized[target],
            bank=canonical_bank,
            target_mapping=target,
            arm_id=expected_arm_id,
            median_convention=median_convention,
            query_policy={
                'candidate': candidate_query_policy[outcome],
                'public': public_query_policy[outcome],
            },
        )
    return {
        'candidate_query_policy': candidate_query_policy,
        'public_query_policy': public_query_policy,
        'rows': live_rows,
    }


def _live_bound_payload_header(
    *,
    expected_arm_id: str,
    median_convention: str,
    role_banks: dict[str, tuple[tuple[int, ...], ...]],
    candidate_query_policies: dict[str, tuple[int | None, ...]],
    public_query_policies: dict[str, tuple[int | None, ...]],
) -> dict[str, Any]:
    role_ids = _primary_role_ids()
    return {
        'schema_version': 'LIVE_BOUND_METRIC_INDEX_C3A_NON_EVIDENCE_V2',
        'expected_arm_id': expected_arm_id,
        'median_convention': median_convention,
        'metric_row_count': len(role_ids) * len(mapping_space()),
        'role_banks': [
            {'role_id': role_id, 'canonical_bank': [list(row) for row in role_banks[role_id]]}
            for role_id in role_ids
        ],
        'candidate_query_policies': [
            {'role_id': role_id, 'choices': list(candidate_query_policies[role_id])}
            for role_id in role_ids
        ],
        'public_query_policies': [
            {'role_id': role_id, 'choices': list(public_query_policies[role_id])}
            for role_id in role_ids
        ],
    }


def _canonical_live_bound_payload_bytes(
    header: dict[str, Any],
    rows_by_role: dict[str, dict[tuple[int, ...], dict[str, Any]]],
) -> bytes:
    # Canonical newline framing permits fresh, recursive row validation without
    # materializing a second 9,000-row JSON object in memory.
    output = bytearray(_canonical_json_bytes(header))
    output.extend(b'\n')
    for role_id in _primary_role_ids():
        for target in mapping_space():
            output.extend(_canonical_json_bytes({
                'role_id': role_id,
                'target_mapping': list(target),
                'metric': rows_by_role[role_id][target],
            }))
            output.extend(b'\n')
    return bytes(output)

def _validate_payload_policy_entries(
    entries: Any,
    *,
    role_ids: tuple[str, ...],
    role_banks: dict[str, tuple[tuple[int, ...], ...]],
    arm_id: str,
    median_convention: str,
    label: str,
) -> dict[str, tuple[int | None, ...]]:
    if type(entries) is not list or len(entries) != len(role_ids):
        raise ValueError(f'live-bound {label} policy coverage mismatch')
    policies = {}
    for expected_role, entry in zip(role_ids, entries):
        if type(entry) is not dict or set(entry) != {'role_id', 'choices'}:
            raise ValueError(f'live-bound {label} policy schema drift')
        if entry['role_id'] != expected_role:
            raise ValueError(f'live-bound {label} policy role order drift')
        choices = entry['choices']
        if type(choices) is not list or len(choices) != 5:
            raise ValueError(f'live-bound {label} five-leaf policy required')
        validated_choices = []
        for choice in choices:
            if choice is not None:
                choice = _strict_int(
                    choice, name=f'{label} query policy leaf', minimum=0, maximum=4,
                )
            validated_choices.append(choice)
        policies[expected_role] = tuple(validated_choices)
    return policies


def _gate_metric_projection(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        'arm_id': metric['arm_id'],
        'target_mapping': list(metric['target_mapping']),
        'selected_query_token': metric['selected_query_token'],
        'candidate_token_losses_raw': list(metric['candidate_token_losses_raw']),
        'metric_rationals': deepcopy(metric['metric_rationals']),
    }


def _decode_and_validate_live_bound_payload(
    payload_bytes: Any,
    *,
    digest_sha256: str,
) -> _ValidatedLiveBoundMetricView:
    if type(payload_bytes) is not bytes:
        raise ValueError('live-bound payload must be canonical bytes')
    header_end = payload_bytes.find(b'\n')
    if header_end <= 0:
        raise ValueError('live-bound framed payload header missing')
    header_bytes = payload_bytes[:header_end]
    try:
        payload = json.loads(header_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('live-bound payload decode failed') from exc
    if type(payload) is not dict or _canonical_json_bytes(payload) != header_bytes:
        raise ValueError('live-bound payload header is not canonical JSON')
    expected_keys = {
        'schema_version', 'expected_arm_id', 'median_convention', 'metric_row_count',
        'role_banks', 'candidate_query_policies', 'public_query_policies',
    }
    if set(payload) != expected_keys:
        raise ValueError('live-bound payload schema drift')
    if payload['schema_version'] != 'LIVE_BOUND_METRIC_INDEX_C3A_NON_EVIDENCE_V2':
        raise ValueError('live-bound payload version drift')
    expected_arm_id = payload['expected_arm_id']
    if type(expected_arm_id) is not str or _arm_record(expected_arm_id)['kind'] != 'trajectory':
        raise ValueError('live-bound expected arm must be a registered trajectory arm')
    median_convention = payload['median_convention']
    if median_convention not in {'lower', 'midpoint_integer', 'upper'}:
        raise ValueError('unknown median convention')

    role_ids = _primary_role_ids()
    targets = mapping_space()
    expected_metric_count = len(role_ids) * len(targets)
    if payload['metric_row_count'] != expected_metric_count:
        raise ValueError('all 120 target metrics required for all 75 roles')
    bank_entries = payload['role_banks']
    if type(bank_entries) is not list or len(bank_entries) != len(role_ids):
        raise ValueError('exact all 75 frozen primary roles required')
    role_banks = {}
    for expected_role, entry in zip(role_ids, bank_entries):
        if type(entry) is not dict or set(entry) != {'role_id', 'canonical_bank'}:
            raise ValueError('live-bound bank entry schema drift')
        if entry['role_id'] != expected_role:
            raise ValueError('exact all 75 frozen primary roles required')
        bank = _validate_bank(entry['canonical_bank'])
        if canonical_bank_bytes(bank) != canonical_bank_bytes(
            _reconstruct_primary_role_bank(expected_role)
        ):
            raise ValueError('registered primary role canonical bank provenance mismatch')
        role_banks[expected_role] = bank

    candidate_policies = _validate_payload_policy_entries(
        payload['candidate_query_policies'], role_ids=role_ids, role_banks=role_banks,
        arm_id=expected_arm_id, median_convention=median_convention, label='candidate',
    )
    public_policies = _validate_payload_policy_entries(
        payload['public_query_policies'], role_ids=role_ids, role_banks=role_banks,
        arm_id=PUBLIC_ARM_ID, median_convention=median_convention, label='PUBLIC',
    )

    rows_by_role = {role_id: {} for role_id in role_ids}
    cursor = header_end + 1
    for role_id in role_ids:
        for target in targets:
            line_end = payload_bytes.find(b'\n', cursor)
            if line_end < 0:
                raise ValueError('live-bound metric framing truncated')
            entry_bytes = payload_bytes[cursor:line_end]
            cursor = line_end + 1
            try:
                entry = json.loads(entry_bytes.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError('live-bound metric row decode failed') from exc
            if type(entry) is not dict or _canonical_json_bytes(entry) != entry_bytes:
                raise ValueError('live-bound metric row is not canonical JSON')
            if set(entry) != {'role_id', 'target_mapping', 'metric'}:
                raise ValueError('live-bound metric entry schema drift')
            if entry['role_id'] != role_id or _validate_mapping(entry['target_mapping']) != target:
                raise ValueError('live-bound metric role/target order drift')
            metric = validate_arm_target_metric(entry['metric'])
            if metric['arm_id'] != expected_arm_id or tuple(metric['target_mapping']) != target:
                raise ValueError('live-bound metric context mismatch')
            outcome = target[0]
            for label, choice, selected_key, decision_key in (
                (
                    'candidate', candidate_policies[role_id][outcome],
                    'selected_query_token', 'query_decision',
                ),
                (
                    'PUBLIC', public_policies[role_id][outcome],
                    'public_selected_query_token', 'public_query_decision',
                ),
            ):
                expected_tie_rule = (
                    'lexical_minimum' if choice is None
                    else 'enumerated_exact_minimizer'
                )
                if metric[decision_key]['tie_rule'] != expected_tie_rule:
                    raise ValueError(f'live-bound {label} policy tie provenance mismatch')
                if choice is not None and metric[selected_key] != choice:
                    raise ValueError(f'live-bound {label} policy selection mismatch')
            rows_by_role[role_id][target] = _gate_metric_projection(metric)
    if cursor != len(payload_bytes):
        raise ValueError('live-bound metric framing has trailing rows or bytes')

    return _ValidatedLiveBoundMetricView(
        expected_arm_id=expected_arm_id,
        median_convention=median_convention,
        role_banks=role_banks,
        candidate_query_policies=candidate_policies,
        public_query_policies=public_policies,
        rows_by_role=rows_by_role,
        digest_sha256=digest_sha256,
    )

def _require_live_bound_metric_index(
    index: Any,
    *,
    expected_arm_id: str | None = None,
) -> _ValidatedLiveBoundMetricView:
    if type(index) is not LiveBoundMetricIndex:
        raise ValueError('gate primitives require a live-bound metric index')
    payload_bytes = index.payload_bytes
    digest_sha256 = index.digest_sha256
    if type(digest_sha256) is not str or len(digest_sha256) != 64:
        raise ValueError('live-bound metric index digest drift')
    recomputed = sha256(payload_bytes).hexdigest() if type(payload_bytes) is bytes else ''
    if recomputed != digest_sha256:
        raise ValueError('live-bound metric index digest mismatch')
    if digest_sha256 not in _ADMITTED_LIVE_BOUND_DIGESTS:
        raise ValueError('live-bound metric index digest was not admitted')
    view = _decode_and_validate_live_bound_payload(
        payload_bytes, digest_sha256=digest_sha256,
    )
    if expected_arm_id is not None and view.expected_arm_id != expected_arm_id:
        raise ValueError('live-bound index arm mismatch')
    return view


def build_live_bound_metric_index(
    role_banks: dict[str, Any],
    stored_rows_by_role: dict[str, dict[Any, Any]],
    *,
    expected_arm_id: str,
    median_convention: str,
    candidate_query_policies: dict[str, Any],
    public_query_policies: dict[str, Any],
) -> LiveBoundMetricIndex:
    """Live-recompute and admit exactly the frozen 75-role primary suite."""
    role_ids = _primary_role_ids()
    expected_role_set = set(role_ids)
    for label, value in (
        ('bank', role_banks), ('stored row', stored_rows_by_role),
        ('candidate policy', candidate_query_policies),
        ('PUBLIC policy', public_query_policies),
    ):
        if type(value) is not dict or set(value) != expected_role_set:
            raise ValueError(f'exact all 75 frozen primary roles required for {label}')
    if median_convention not in {'lower', 'midpoint_integer', 'upper'}:
        raise ValueError('unknown median convention')
    if type(expected_arm_id) is not str or _arm_record(expected_arm_id)['kind'] != 'trajectory':
        raise ValueError('live-bound expected arm must be a registered trajectory arm')

    canonical_banks = {}
    for role_id in role_ids:
        canonical = _validate_bank(role_banks[role_id])
        expected_bank = _reconstruct_primary_role_bank(role_id)
        if canonical_bank_bytes(canonical) != canonical_bank_bytes(expected_bank):
            raise ValueError('registered primary role canonical bank provenance mismatch')
        canonical_banks[role_id] = canonical

    candidate_policies = {}
    public_policies = {}
    live_rows = {}
    for role_id in role_ids:
        role_result = _live_recompute_role_metric_rows(
            role_id,
            canonical_banks[role_id],
            stored_rows_by_role[role_id],
            expected_arm_id=expected_arm_id,
            median_convention=median_convention,
            candidate_query_policy_spec=candidate_query_policies[role_id],
            public_query_policy_spec=public_query_policies[role_id],
        )
        if type(role_result) is not dict or set(role_result) != {
            'candidate_query_policy', 'public_query_policy', 'rows',
        }:
            raise ValueError('live role recomputation result schema drift')
        candidate_policies[role_id] = tuple(role_result['candidate_query_policy'])
        public_policies[role_id] = tuple(role_result['public_query_policy'])
        live_rows[role_id] = role_result['rows']
    header = _live_bound_payload_header(
        expected_arm_id=expected_arm_id,
        median_convention=median_convention,
        role_banks=canonical_banks,
        candidate_query_policies=candidate_policies,
        public_query_policies=public_policies,
    )
    payload_bytes = _canonical_live_bound_payload_bytes(header, live_rows)
    digest_sha256 = sha256(payload_bytes).hexdigest()
    _decode_and_validate_live_bound_payload(payload_bytes, digest_sha256=digest_sha256)
    _ADMITTED_LIVE_BOUND_DIGESTS.add(digest_sha256)
    return _new_admitted_live_bound_metric_index(payload_bytes, digest_sha256)


def _normalize_role_metric_rows(
    role_banks: dict[str, Any],
    rows_by_role: dict[str, dict[Any, Any]],
    *,
    require_all_targets: bool,
) -> dict[str, dict[tuple[int, ...], dict[str, Any]]]:
    if type(role_banks) is not dict or not role_banks or type(rows_by_role) is not dict:
        raise ValueError('role metric inputs must be nonempty dictionaries')
    if set(rows_by_role) != set(role_banks):
        raise ValueError('role metric coverage mismatch')
    normalized = {}
    all_targets = set(mapping_space())
    for role_id, bank in role_banks.items():
        _validate_bank(bank)
        role_rows = rows_by_role[role_id]
        if type(role_rows) is not dict or not role_rows:
            raise ValueError('empty role metric rows')
        target_rows = {}
        for target_key, metric in role_rows.items():
            target = _validate_mapping(target_key)
            validated = validate_arm_target_metric(metric)
            if tuple(validated['target_mapping']) != target:
                raise ValueError('role metric target mismatch')
            target_rows[target] = validated
        if require_all_targets and set(target_rows) != all_targets:
            raise ValueError('all 120 target metrics required')
        normalized[role_id] = target_rows
    return normalized


def _member_and_forward_for_role(
    bank,
    target_rows: dict[tuple[int, ...], dict[str, Any]],
) -> dict[str, Any]:
    support = tuple(sorted(set(_validate_bank(bank))))
    if any(target not in target_rows for target in support):
        raise ValueError('distinct exact-member coverage incomplete')
    full_min = _threshold_fraction('member_full_improvement_min')
    common_min = _threshold_fraction('member_common_forward_min')
    same_min = _threshold_fraction('member_same_history_forward_min')
    canonical_common_min = _threshold_fraction('canonical_member_common_forward_min')
    canonical_same_min = _threshold_fraction('canonical_member_same_history_forward_min')
    pointwise = []
    for target in support:
        row = target_rows[target]
        full = _decode_rational(row['metric_rationals']['full_endpoint_improvement'])
        common = _decode_rational(row['metric_rationals']['common_unqueried_forward_improvement'])
        same = _decode_rational(row['metric_rationals']['same_history_forward_improvement'])
        pointwise.append({
            'target_mapping': list(target),
            'full_improvement': _rational(full),
            'common_improvement': _rational(common),
            'same_history_improvement': _rational(same),
            'passes': full >= full_min and common >= common_min and same >= same_min,
        })
    canonical = support[0]
    canonical_row = target_rows[canonical]
    canonical_common = _decode_rational(
        canonical_row['metric_rationals']['common_unqueried_forward_improvement']
    )
    canonical_same = _decode_rational(
        canonical_row['metric_rationals']['same_history_forward_improvement']
    )
    canonical_passes = (
        canonical_common >= canonical_common_min and canonical_same >= canonical_same_min
    )
    return {
        'canonical_member': list(canonical),
        'pointwise_member_rows': pointwise,
        'all_distinct_members_pass': all(row['passes'] for row in pointwise),
        'canonical_member_passes': canonical_passes,
        'member_and_forward': all(row['passes'] for row in pointwise) and canonical_passes,
    }


def _require_metric_arm(
    normalized_rows: dict[str, dict[tuple[int, ...], dict[str, Any]]],
    expected_arm_id: str,
    *,
    label: str,
) -> None:
    for role_rows in normalized_rows.values():
        if any(row['arm_id'] != expected_arm_id for row in role_rows.values()):
            raise ValueError(f'{label} arm mismatch')


def _full_safety_for_role(
    bank,
    target_rows: dict[tuple[int, ...], dict[str, Any]],
    *,
    regret_max: Fraction,
) -> bool:
    if set(target_rows) != set(mapping_space()):
        raise ValueError('all 120 target metrics required for safety')
    nonmember_rows = []
    for target, row in target_rows.items():
        if classify_target(bank, target)['distance'] in {2, 3, 4, 5}:
            improvement = _decode_rational(
                row['metric_rationals']['full_endpoint_improvement']
            )
            nonmember_rows.append(-improvement <= regret_max)
    if not nonmember_rows:
        raise ValueError('nonmember safety coverage empty')
    return all(nonmember_rows)


def _require_compatible_live_views(
    left: Any,
    right: Any,
) -> tuple[_ValidatedLiveBoundMetricView, _ValidatedLiveBoundMetricView]:
    if not isinstance(left, _ValidatedLiveBoundMetricView) or not isinstance(
        right, _ValidatedLiveBoundMetricView
    ):
        raise ValueError('compatible reductions require fresh validated views')
    if set(left.role_banks) != set(right.role_banks):
        raise ValueError('live-bound role coverage mismatch between indexes')
    if left.median_convention != right.median_convention:
        raise ValueError('live-bound median convention mismatch between indexes')
    for role_id in left.role_banks:
        if canonical_bank_bytes(left.role_banks[role_id]) != canonical_bank_bytes(
            right.role_banks[role_id]
        ):
            raise ValueError('live-bound canonical bank mismatch between indexes')
    return left, right


def _require_compatible_live_indexes(
    left: Any,
    right: Any,
) -> tuple[_ValidatedLiveBoundMetricView, _ValidatedLiveBoundMetricView]:
    return _require_compatible_live_views(
        _require_live_bound_metric_index(left),
        _require_live_bound_metric_index(right),
    )


def _reduce_candidate_and_raw_primitives(
    conservative_index: LiveBoundMetricIndex,
    raw_index: LiveBoundMetricIndex,
) -> dict[str, Any]:
    conservative_id = _frozen_design()['arm_registry']['primary_conservative']
    raw_id = _frozen_design()['arm_registry']['raw_upside']
    conservative_view = _require_live_bound_metric_index(
        conservative_index, expected_arm_id=conservative_id,
    )
    raw_view = _require_live_bound_metric_index(raw_index, expected_arm_id=raw_id)
    return _reduce_candidate_and_raw_validated_views(conservative_view, raw_view)


def _reduce_candidate_and_raw_validated_views(
    conservative_index: _ValidatedLiveBoundMetricView,
    raw_index: _ValidatedLiveBoundMetricView,
) -> dict[str, Any]:
    conservative_index, raw_index = _require_compatible_live_views(
        conservative_index, raw_index,
    )
    role_banks = conservative_index.role_banks
    conservative = conservative_index.rows_by_role
    raw = raw_index.rows_by_role
    bounded = _threshold_fraction('nonmember_bounded_full_regret_max')
    strict = _threshold_fraction('nonmember_strict_full_regret_max')
    receipts = {}
    for role_id, bank in role_banks.items():
        receipts[role_id] = {
            'conservative_member': _member_and_forward_for_role(bank, conservative[role_id]),
            'raw_member': _member_and_forward_for_role(bank, raw[role_id]),
            'conservative_bounded_safety': _full_safety_for_role(
                bank, conservative[role_id], regret_max=bounded,
            ),
            'conservative_strict_safety': _full_safety_for_role(
                bank, conservative[role_id], regret_max=strict,
            ),
            'raw_bounded_safety': _full_safety_for_role(
                bank, raw[role_id], regret_max=bounded,
            ),
        }
    return {
        'raw_upside': all(row['raw_member']['member_and_forward'] for row in receipts.values()),
        'raw_bounded_safety': all(row['raw_bounded_safety'] for row in receipts.values()),
        'conservative_member_and_forward': all(
            row['conservative_member']['member_and_forward'] for row in receipts.values()
        ),
        'conservative_bounded_safety': all(
            row['conservative_bounded_safety'] for row in receipts.values()
        ),
        'conservative_strict_safety': all(
            row['conservative_strict_safety'] for row in receipts.values()
        ),
        'role_receipts': receipts,
    }


def _pareto_match_control(
    candidate_index: LiveBoundMetricIndex,
    control_index: LiveBoundMetricIndex,
) -> dict[str, Any]:
    candidate_index, control_index = _require_compatible_live_indexes(
        candidate_index, control_index,
    )
    return _pareto_match_validated_views(candidate_index, control_index)


def _pareto_match_validated_views(
    candidate_index: _ValidatedLiveBoundMetricView,
    control_index: _ValidatedLiveBoundMetricView,
) -> dict[str, Any]:
    candidate_index, control_index = _require_compatible_live_views(
        candidate_index, control_index,
    )
    role_banks = candidate_index.role_banks
    candidate = candidate_index.rows_by_role
    control = control_index.rows_by_role
    full_no_worse = True
    member_common_no_worse = True
    strict = False
    byte_identical = True
    for role_id, bank in role_banks.items():
        support = set(_validate_bank(bank))
        for target in mapping_space():
            candidate_row = candidate[role_id][target]
            control_row = control[role_id][target]
            candidate_full = _decode_rational(
                candidate_row['metric_rationals']['candidate_full_endpoint_mae']
            )
            control_full = _decode_rational(
                control_row['metric_rationals']['candidate_full_endpoint_mae']
            )
            full_no_worse = full_no_worse and control_full <= candidate_full
            strict = strict or control_full < candidate_full
            byte_identical = byte_identical and (
                _canonical_json_bytes(control_row['metric_rationals'])
                == _canonical_json_bytes(candidate_row['metric_rationals'])
            )
            if target in support:
                pair = _pairwise_common_mae_validated(candidate_row, control_row)
                candidate_common = _decode_rational(pair['left_mae'])
                control_common = _decode_rational(pair['right_mae'])
                member_common_no_worse = (
                    member_common_no_worse and control_common <= candidate_common
                )
                strict = strict or control_common < candidate_common
    matches = full_no_worse and member_common_no_worse and (strict or byte_identical)
    return {
        'full_no_worse_everywhere': full_no_worse,
        'member_common_no_worse_everywhere': member_common_no_worse,
        'strict_improvement_found': strict,
        'byte_identical_metric_rationals_everywhere': byte_identical,
        'matches': matches,
    }


def _invalidating_control_ids() -> tuple[str, ...]:
    ids = tuple(_frozen_design()['gates']['invalidating_control_ids'])
    if len(ids) != 19 or len(set(ids)) != 19:
        raise ValueError('exact 19 invalidating controls required')
    if any(_arm_record(arm_id)['kind'] != 'trajectory' for arm_id in ids):
        raise ValueError('invalidating control registry drift')
    return ids


def _reduce_exact_control_pareto(
    candidate_index: LiveBoundMetricIndex,
    controls_by_arm: dict[str, LiveBoundMetricIndex],
) -> dict[str, Any]:
    ids = _invalidating_control_ids()
    if type(controls_by_arm) is not dict or set(controls_by_arm) != set(ids):
        raise ValueError('exact 19 invalidating control rows required')
    candidate_view = _require_live_bound_metric_index(
        candidate_index,
        expected_arm_id=_frozen_design()['arm_registry']['primary_conservative'],
    )
    receipts = {}
    for arm_id in ids:
        control_view = _require_live_bound_metric_index(
            controls_by_arm[arm_id], expected_arm_id=arm_id,
        )
        candidate_compatible, control_compatible = _require_compatible_live_views(
            candidate_view, control_view,
        )
        receipts[arm_id] = _pareto_match_validated_views(
            candidate_compatible, control_compatible,
        )
    return {
        'pareto_match_arm_ids': [arm_id for arm_id in ids if receipts[arm_id]['matches']],
        'control_receipts': receipts,
    }


def _consistency_positive_non_equivalence(
    candidate_index: LiveBoundMetricIndex,
    consistency_index: LiveBoundMetricIndex,
) -> dict[str, Any]:
    candidate_index = _require_live_bound_metric_index(
        candidate_index,
        expected_arm_id=_frozen_design()['arm_registry']['primary_conservative'],
    )
    consistency_id = _frozen_design()['arm_registry']['BANK_CONSISTENCY_L1_RISK_DP']
    consistency_index = _require_live_bound_metric_index(
        consistency_index, expected_arm_id=consistency_id,
    )
    return _consistency_positive_non_equivalence_validated_views(
        candidate_index, consistency_index,
    )


def _consistency_positive_non_equivalence_validated_views(
    candidate_index: _ValidatedLiveBoundMetricView,
    consistency_index: _ValidatedLiveBoundMetricView,
) -> dict[str, Any]:
    candidate_index, consistency_index = _require_compatible_live_views(
        candidate_index, consistency_index,
    )
    role_banks = candidate_index.role_banks
    candidate = candidate_index.rows_by_role
    consistency = consistency_index.rows_by_role
    effect_min = _threshold_fraction('consistency_member_common_forward_advantage_min')
    no_full_regression = True
    member_effect = False
    for role_id, bank in role_banks.items():
        support = set(_validate_bank(bank))
        for target in mapping_space():
            candidate_row = candidate[role_id][target]
            consistency_row = consistency[role_id][target]
            candidate_full = _decode_rational(
                candidate_row['metric_rationals']['candidate_full_endpoint_mae']
            )
            consistency_full = _decode_rational(
                consistency_row['metric_rationals']['candidate_full_endpoint_mae']
            )
            no_full_regression = no_full_regression and candidate_full <= consistency_full
            if target in support:
                advantage = _decode_rational(
                    _pairwise_common_mae_validated(
                        candidate_row, consistency_row,
                    )['left_advantage']
                )
                member_effect = member_effect or advantage >= effect_min
    positive = no_full_regression and member_effect
    return {
        'no_positive_full_regression': no_full_regression,
        'member_common_effect_found': member_effect,
        'positive_non_equivalence': positive,
        'control_match': not positive,
    }


def _no_update_arm_ids() -> tuple[str, ...]:
    records = [
        row for row in _frozen_design()['ablation_registry']['records']
        if row['ablation_id'] == 'ABL_NO_UPDATE'
    ]
    if len(records) != 1:
        raise ValueError('no-update ablation registry drift')
    ids = tuple(records[0]['registered_arm_ids'])
    if len(ids) != 2 or len(set(ids)) != 2:
        raise ValueError('both registered no-update arms required')
    return ids


def _reduce_no_update_group(
    conservative_index: LiveBoundMetricIndex,
    no_update_rows_by_arm: dict[str, LiveBoundMetricIndex],
) -> dict[str, Any]:
    ids = _no_update_arm_ids()
    if type(no_update_rows_by_arm) is not dict or set(no_update_rows_by_arm) != set(ids):
        raise ValueError('both registered no-update arms are required')
    conservative_index = _require_live_bound_metric_index(
        conservative_index,
        expected_arm_id=_frozen_design()['arm_registry']['primary_conservative'],
    )
    ablated_views = {
        arm_id: _require_live_bound_metric_index(
            no_update_rows_by_arm[arm_id], expected_arm_id=arm_id,
        )
        for arm_id in ids
    }
    return _reduce_no_update_validated_views(conservative_index, ablated_views)


def _reduce_no_update_validated_views(
    conservative_index: _ValidatedLiveBoundMetricView,
    no_update_rows_by_arm: dict[str, _ValidatedLiveBoundMetricView],
) -> dict[str, Any]:
    ids = _no_update_arm_ids()
    if type(no_update_rows_by_arm) is not dict or set(no_update_rows_by_arm) != set(ids):
        raise ValueError('both registered no-update arms are required')
    role_banks = conservative_index.role_banks
    conservative = conservative_index.rows_by_role
    effect_min = _threshold_fraction('canonical_member_common_forward_min')
    per_arm = {}
    for arm_id in ids:
        ablated_index = no_update_rows_by_arm[arm_id]
        _, ablated_index = _require_compatible_live_views(
            conservative_index, ablated_index,
        )
        ablated = ablated_index.rows_by_role
        role_member = {}
        effect_found = False
        for role_id, bank in role_banks.items():
            conservative_member = _member_and_forward_for_role(
                bank, conservative[role_id],
            )
            ablated_member = _member_and_forward_for_role(bank, ablated[role_id])
            role_member[role_id] = ablated_member
            canonical = tuple(conservative_member['canonical_member'])
            conservative_row = conservative[role_id][canonical]
            ablated_row = ablated[role_id][canonical]
            common_reduction = (
                _decode_rational(conservative_row['metric_rationals']['common_unqueried_forward_improvement'])
                - _decode_rational(ablated_row['metric_rationals']['common_unqueried_forward_improvement'])
            )
            same_reduction = (
                _decode_rational(conservative_row['metric_rationals']['same_history_forward_improvement'])
                - _decode_rational(ablated_row['metric_rationals']['same_history_forward_improvement'])
            )
            effect_found = effect_found or max(common_reduction, same_reduction) >= effect_min
        complete = all(row['member_and_forward'] for row in role_member.values())
        per_arm[arm_id] = {
            'complete_member_and_forward': complete,
            'canonical_effect_reduction_found': effect_found,
            'passes_no_update_predicate': (not complete) and effect_found,
            'role_member_receipts': role_member,
        }
    return {
        'per_arm': per_arm,
        'group_passes': all(row['passes_no_update_predicate'] for row in per_arm.values()),
    }



_GATE_VARIANTS = (
    ('MEDIAN_LOWER__LEXICAL', 'lower', 'lexical'),
    ('MEDIAN_LOWER__SYMBOLIC_GLOBAL_POLICY_DP_V1', 'lower', 'symbolic_global_policy_dp_v1'),
    ('MEDIAN_MIDPOINT_INTEGER__LEXICAL', 'midpoint_integer', 'lexical'),
    ('MEDIAN_MIDPOINT_INTEGER__SYMBOLIC_GLOBAL_POLICY_DP_V1', 'midpoint_integer', 'symbolic_global_policy_dp_v1'),
    ('MEDIAN_UPPER__LEXICAL', 'upper', 'lexical'),
    ('MEDIAN_UPPER__SYMBOLIC_GLOBAL_POLICY_DP_V1', 'upper', 'symbolic_global_policy_dp_v1'),
)

_GATE_GENERATOR_SPECS = (
    ('GEN_AUTHORITY_HASH','AUTHORITY_HASH','FROZEN_AUTHORITY',['ordinal'],'COUNT_AUTHORITY_3_V1',['AUTHORITY_HASH_RECOMPUTE'],'authority_receipts'),
    ('GEN_BANK_COVERAGE','BANK_COVERAGE','BANK_COVERAGE',['canonical_bank_sha256','ordinal'],'COUNT_BANKS_V1',['BANK_CONSTRUCTOR_RECOMPUTE'],'bank_receipts'),
    ('GEN_ARM_ROW_COVERAGE','ARM_ROW_COVERAGE','ARM_ROW_COVERAGE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_ARM_ROWS_V1',['ARM_ROW_LIVE_RECOMPUTE'],'arm_coverage_receipts'),
    ('GEN_ABL_SOURCE_DELETE','ABLATION_SEMANTIC','ABL_SOURCE_DELETE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_LOCAL_SHIFT_DELETE','ABLATION_SEMANTIC','ABL_LOCAL_SHIFT_DELETE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_NO_UPDATE','ABLATION_SEMANTIC','ABL_NO_UPDATE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_ACTIVE_DELETE','ABLATION_SEMANTIC','ABL_ACTIVE_DELETE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_QUERY_OUTCOME_MASK','ABLATION_SEMANTIC','ABL_QUERY_OUTCOME_MASK',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_POSTQUERY_SOURCE_DELETE','ABLATION_SEMANTIC','ABL_POSTQUERY_SOURCE_DELETE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_SHAM_ROTATION','ABLATION_SEMANTIC','ABL_SHAM_ROTATION',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_ABL_MULTIPLICITY_FLATTEN','ABLATION_SEMANTIC','ABL_MULTIPLICITY_FLATTEN',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_MATRIX_PRODUCT_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_INV_SOURCE_ORDER_ENUM','INVARIANCE_SEMANTIC','INV_SOURCE_ORDER',['canonical_bank_sha256','transformation_id','ordinal'],'COUNT_UNIQUE_SOURCE_ORDERS_V1',['INVARIANCE_REFERENCE_RECOMPUTE','INVARIANCE_TRANSFORM_RECOMPUTE'],'invariance_records'),
    ('GEN_INV_SOURCE_ORDER_LINEAGE','INVARIANCE_SEMANTIC','INV_SOURCE_ORDER',['arm_ids','ordinal'],'COUNT_TRAJECTORY_ARMS_42_V1',['SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE','SOURCE_ORDER_AST_DATAFLOW_AUDIT'],'invariance_records'),
    ('GEN_INV_SOURCE_ORDER_SABOTAGE','INVARIANCE_SEMANTIC','INV_SOURCE_ORDER',['ordinal'],'COUNT_ONE_V1',['SOURCE_ORDER_SABOTAGE_PROBE'],'invariance_records'),
    ('GEN_INV_TOKEN_RELABEL','INVARIANCE_SEMANTIC','INV_TOKEN_RELABEL',['variant_id','canonical_bank_sha256','arm_ids','target_mapping','transformation_id','ordinal'],'COUNT_TOKEN_RELABEL_V1',['INVARIANCE_REFERENCE_RECOMPUTE','INVARIANCE_TRANSFORM_RECOMPUTE'],'invariance_records'),
    ('GEN_INV_PROTOTYPE_RELABEL','INVARIANCE_SEMANTIC','INV_PROTOTYPE_RELABEL',['variant_id','canonical_bank_sha256','arm_ids','target_mapping','transformation_id','ordinal'],'COUNT_PROTOTYPE_RELABEL_V1',['INVARIANCE_REFERENCE_RECOMPUTE','INVARIANCE_TRANSFORM_RECOMPUTE'],'invariance_records'),
    ('GEN_INV_EIG_ENTROPY_ALIAS','INVARIANCE_SEMANTIC','INV_EIG_ENTROPY_ALIAS',['variant_id','canonical_bank_sha256','arm_ids','transformation_id','ordinal'],'COUNT_EIG_ALIAS_V1',['INVARIANCE_REFERENCE_RECOMPUTE','INVARIANCE_TRANSFORM_RECOMPUTE'],'invariance_records'),
    ('GEN_ABL_NO_QUERY','ABLATION_SEMANTIC','ABL_NO_QUERY',['variant_id','canonical_bank_sha256','arm_ids','target_mapping','ordinal'],'COUNT_NO_QUERY_V1',['ABLATION_LIVE_RECOMPUTE'],'ablation_semantic_records'),
    ('GEN_PROPERTY_B_SEPARABLE','PROPERTY_WITNESS','B_SEPARABLE',['variant_id','canonical_bank_sha256','transformation_id','ordinal'],'COUNT_PROPERTY_POLICY_V1',['PROPERTY_WITNESS_RECOMPUTE'],'property_records'),
    ('GEN_PROPERTY_B_COLLISION','PROPERTY_WITNESS','B_COLLISION',['variant_id','canonical_bank_sha256','transformation_id','ordinal'],'COUNT_PROPERTY_POLICIES_V1',['PROPERTY_WITNESS_RECOMPUTE'],'property_records'),
    ('GEN_PROPERTY_B_DECOY','PROPERTY_WITNESS','B_DECOY',['variant_id','canonical_bank_sha256','arm_ids','transformation_id','ordinal'],'COUNT_PROPERTY_H1_V1',['PROPERTY_WITNESS_RECOMPUTE'],'property_records'),
    ('GEN_PROPERTY_B_BALANCED_MARGINAL','PROPERTY_WITNESS','B_BALANCED_MARGINAL',['variant_id','canonical_bank_sha256','arm_ids','transformation_id','ordinal'],'COUNT_PROPERTY_H1_V1',['PROPERTY_WITNESS_RECOMPUTE'],'property_records'),
    ('GEN_PROPERTY_MULT_6','PROPERTY_WITNESS','MULT_6',['variant_id','canonical_bank_sha256','arm_ids','target_mapping','ordinal'],'COUNT_PROPERTY_MULT6_V1',['PROPERTY_WITNESS_RECOMPUTE'],'property_records'),
    ('GEN_LEAKAGE_POSITIVE_CONTROL','LEAKAGE_POSITIVE_CONTROL','LEAKAGE_POSITIVE_CONTROL',['transformation_id','ordinal'],'COUNT_LEAKAGE_24_V1',['LEAKAGE_VALIDATOR_PROBE'],'leakage_records'),
    ('GEN_AMORTIZED_PUBLIC_STATE','AMORTIZED_PUBLIC_STATE','AMORTIZED_PUBLIC_STATE',['canonical_bank_sha256','public_state_key','ordinal'],'COUNT_AMORTIZED_85B_V1',['LIVE_PRIMARY_OUTPUT_RECOMPUTE','AMORTIZED_LOOKUP_RECOMPUTE'],'amortized_records'),
    ('GEN_FRESH_TRAJECTORY_RECOMPUTE','FRESH_PROCESS_TRAJECTORY_RECOMPUTE','FRESH_PROCESS_TRAJECTORY_RECOMPUTE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_LEXICAL_TRAJECTORY_ROWS_V1',['FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE'],'replay_records'),
    ('GEN_FRESH_AGGREGATE_RECOMPUTE','FRESH_PROCESS_AGGREGATE_RECOMPUTE','FRESH_PROCESS_AGGREGATE_RECOMPUTE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_LEXICAL_AGGREGATE_ROWS_V1',['FRESH_PROCESS_AGGREGATE_RECOMPUTE'],'replay_records'),
    ('GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE','INDEPENDENT_TRAJECTORY_RECOMPUTE','INDEPENDENT_TRAJECTORY_RECOMPUTE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_LEXICAL_TRAJECTORY_ROWS_V1',['INDEPENDENT_PATH_TRAJECTORY_ROW_RECOMPUTE'],'independent_recompute_records'),
    ('GEN_INDEPENDENT_AGGREGATE_RECOMPUTE','INDEPENDENT_AGGREGATE_RECOMPUTE','INDEPENDENT_AGGREGATE_RECOMPUTE',['variant_id','canonical_bank_sha256','target_mapping','arm_ids','ordinal'],'COUNT_LEXICAL_AGGREGATE_ROWS_V1',['INDEPENDENT_PATH_AGGREGATE_RECOMPUTE'],'independent_recompute_records'),
    ('GEN_SYMBOLIC_LOCAL_CONTRIBUTION','SYMBOLIC_LOCAL_CONTRIBUTION','SYMBOLIC_LOCAL_CONTRIBUTION',['variant_id','canonical_bank_sha256','ordinal'],'COUNT_SYMBOLIC_BANK_BUNDLES_V1',['FRESH_PROCESS_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE','INDEPENDENT_PATH_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE'],'replay_records'),
    ('GEN_SYMBOLIC_LOCAL_AGGREGATE','SYMBOLIC_LOCAL_AGGREGATE','SYMBOLIC_LOCAL_AGGREGATE',['variant_id','ordinal'],'COUNT_SYMBOLIC_GLOBAL_BUNDLES_V1',['FRESH_PROCESS_SYMBOLIC_DP_AGGREGATE_RECOMPUTE','INDEPENDENT_PATH_SYMBOLIC_DP_AGGREGATE_RECOMPUTE'],'replay_records'),
)


def _gate_role_banks() -> dict[str, tuple[tuple[int, ...], ...]]:
    banks = {role_id: _reconstruct_primary_role_bank(role_id) for role_id in _primary_role_ids()}
    properties = scan_property_banks()
    for role_id in sorted(_frozen_design()['bank_suite']['property_predicates']):
        banks[role_id] = _validate_bank(properties[role_id]['bank'])
    return banks


def _gate_bank_groups() -> list[dict[str, Any]]:
    grouped: dict[bytes, dict[str, Any]] = {}
    for role_id, bank in _gate_role_banks().items():
        bank_bytes = canonical_bank_bytes(bank)
        row = grouped.setdefault(bank_bytes, {'bank': bank, 'role_ids': []})
        row['role_ids'].append(role_id)
    rows = []
    targets = [list(target) for target in mapping_space()]
    for bank_bytes, group in grouped.items():
        bank = group['bank']
        rows.append({
            'canonical_bank_sha256': sha256(bank_bytes).hexdigest(),
            'canonical_bank': [list(mapping) for mapping in bank],
            'role_ids': sorted(group['role_ids']),
            'canonical_member': list(min(set(bank))),
            'target_mappings': targets,
        })
    rows.sort(key=lambda row: row['canonical_bank_sha256'])
    return rows


def _gate_variants() -> list[dict[str, str]]:
    return [
        {'variant_id': variant_id, 'median_convention': median, 'variant_kind': kind}
        for variant_id, median, kind in _GATE_VARIANTS
    ]


def _query_pair_id(gate_ids, left, right, roles) -> str:
    preimage = '\x1f'.join((
        'QPAIR', json.dumps(sorted(gate_ids), separators=(',', ':')),
        left, right, json.dumps(sorted(roles), separators=(',', ':')),
    )).encode('utf-8')
    return sha256(preimage).hexdigest()


def _gate_query_pairs(primary_ids: list[str], property_ids: list[str]) -> list[dict[str, Any]]:
    design = _frozen_design()
    c = design['arm_registry']['primary_conservative']
    r = design['arm_registry']['raw_upside']
    p = design['arm_registry']['PUBLIC_L1_RISK_DP']
    rows = []
    def add(gates, left, right, roles):
        roles = sorted(roles); gates = list(gates)
        rows.append({'pair_id': _query_pair_id(gates,left,right,roles), 'gate_ids': gates,
                     'left_arm_id': left, 'right_arm_id': right, 'role_ids': roles})
    add(['MEMBER_FORWARD_CONSERVATIVE','SOURCE_DELETE'],c,p,primary_ids)
    add(['MEMBER_FORWARD_RAW'],r,p,primary_ids)
    consistency = design['arm_registry']['BANK_CONSISTENCY_L1_RISK_DP']
    for arm in _invalidating_control_ids():
        gates=[f'CONTROL_PARETO:{arm}']
        if arm == consistency: gates.append('CONSISTENCY_POSITIVE_NON_EQUIVALENCE')
        add(gates,c,arm,primary_ids)
    effects = [
      ('ABL_LOCAL_SHIFT_DELETE','ARM_I_TRANSFER_NO_LOCAL__A_L1_EVSI__D_LCB05_FALLBACK',primary_ids),
      ('ABL_NO_UPDATE','ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK',primary_ids),
      ('ABL_NO_UPDATE','ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK',primary_ids),
      ('ABL_ACTIVE_DELETE','ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK',['B_SEPARABLE']),
      ('ABL_QUERY_OUTCOME_MASK','ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK',primary_ids),
      ('ABL_POSTQUERY_SOURCE_DELETE','ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1',primary_ids),
      ('ABL_SHAM_ROTATION','ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK',primary_ids),
      ('ABL_SHAM_ROTATION','ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN',primary_ids),
      ('ABL_MULTIPLICITY_FLATTEN','ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK',['MULT_6']),
    ]
    for gate, arm, roles in effects: add([f'CAUSAL_EFFECT:{gate}'],c,arm,roles)
    failures = [
      ('ABL_NO_UPDATE','ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK'),
      ('ABL_NO_UPDATE','ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK'),
      ('ABL_QUERY_OUTCOME_MASK','ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK'),
      ('ABL_POSTQUERY_SOURCE_DELETE','ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1'),
      ('ABL_SHAM_ROTATION','ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK'),
      ('ABL_SHAM_ROTATION','ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN'),
    ]
    for gate, arm in failures: add([f'MEMBER_FAILURE:{gate}'],arm,p,primary_ids)
    add(['PROPERTY_B_DECOY'],'ARM_I_TRANSFER__A_EIG__D_L1_MEDIAN',r,['B_DECOY'])
    add(['PROPERTY_B_BALANCED_MARGINAL'],'ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN','ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN',['B_BALANCED_MARGINAL'])
    add(['PROPERTY_MULT_6'],c,'ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK',['MULT_6'])
    unique = {_canonical_json_bytes({k:v for k,v in row.items() if k!='pair_id'}):row for row in rows}
    return sorted(unique.values(), key=lambda row: row['pair_id'])


def _generator_descriptor(generator_id: str, *, arm_ids, bank_groups, variants) -> dict[str, Any]:
    spec=next(row for row in _GATE_GENERATOR_SPECS if row[0]==generator_id)
    dimension_keys=spec[3]
    special_domains={
      'GEN_AUTHORITY_HASH':{'ordinal':'FROZEN_AUTHORITY_PATH_ORDER_V1'},
      'GEN_INV_SOURCE_ORDER_ENUM':{'transformation_id':'UNIQUE_SOURCE_ORDER_RANKS_BY_BANK_V1'},
      'GEN_INV_SOURCE_ORDER_LINEAGE':{'arm_ids':'TRAJECTORY_ARMS_42_V1'},
      'GEN_INV_SOURCE_ORDER_SABOTAGE':{'ordinal':'SINGLE_SABOTAGE_CASE_V1'},
      'GEN_INV_TOKEN_RELABEL':{'canonical_bank_sha256':'NAMED_ROLE_CANONICAL_GROUPS_V1','transformation_id':'TOKEN_PERMUTATIONS_120_V1'},
      'GEN_INV_PROTOTYPE_RELABEL':{'canonical_bank_sha256':'NAMED_ROLE_CANONICAL_GROUPS_V1','transformation_id':'PROTOTYPE_PERMUTATIONS_120_V1'},
      'GEN_INV_EIG_ENTROPY_ALIAS':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'EIG_ENTROPY_INFERENCE_PAIRS_3_V1','transformation_id':'EIG_ENTROPY_H1_OUTCOMES_5_V1'},
      'GEN_ABL_NO_QUERY':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'NO_QUERY_ARMS_3_V1'},
      'GEN_LEAKAGE_POSITIVE_CONTROL':{'transformation_id':'FORBIDDEN_CLASSES_X_DIRECT_ENCODED_V1'},
      'GEN_AMORTIZED_PUBLIC_STATE':{'public_state_key':'CANONICAL_PUBLIC_STATES_85_PER_BANK_V1'},
      'GEN_FRESH_TRAJECTORY_RECOMPUTE':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'TRAJECTORY_ARMS_42_V1'},
      'GEN_FRESH_AGGREGATE_RECOMPUTE':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'AGGREGATE_ARMS_3_V1'},
      'GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'TRAJECTORY_ARMS_42_V1'},
      'GEN_INDEPENDENT_AGGREGATE_RECOMPUTE':{'variant_id':'LEXICAL_VARIANTS_3_V1','arm_ids':'AGGREGATE_ARMS_3_V1'},
      'GEN_SYMBOLIC_LOCAL_CONTRIBUTION':{'variant_id':'SYMBOLIC_VARIANTS_3_V1','arm_ids':'QUERY_PAIR_ARM_UNION_V1'},
      'GEN_SYMBOLIC_LOCAL_AGGREGATE':{'variant_id':'SYMBOLIC_VARIANTS_3_V1'},
    }
    if generator_id.startswith('GEN_PROPERTY_'):
      special_domains[generator_id]={'variant_id':'LEXICAL_VARIANTS_3_V1'}
    defaults={'variant_id':'EXACT_SIX_VARIANTS_V1','canonical_bank_sha256':'DERIVED_CANONICAL_BANK_GROUPS_SHA256_ORDER_V1',
      'target_mapping':'LEXICOGRAPHIC_MAPPING_SPACE_120_V1','arm_ids':'GENERATOR_EXACT_ARM_ENUM_V1',
      'transformation_id':'GENERATOR_EXACT_TRANSFORMATION_ENUM_V1','public_state_key':'GENERATOR_PUBLIC_STATE_KEYS_V1',
      'ordinal':'ZERO_BASED_GENERATOR_ORDINAL_V1'}
    overrides=special_domains.get(generator_id,{})
    return {
        'schema_version': 'COMPACT_GATE_GENERATOR_DESCRIPTOR_V2',
        'generator_id': generator_id,
        'dimensions': [
          {'dimension_key':key,'domain_id':overrides.get(key,defaults[key])}
          for key in dimension_keys
        ],
    }


def _generator_expected_counts(bank_groups, variants, arm_records, properties) -> dict[str, int]:
    B=len(bank_groups); L=len(variants); T=sum(r['kind']=='trajectory' for r in arm_records); G=sum(r['kind']=='aggregate' for r in arm_records)
    lex=sum(v['variant_kind']=='lexical' for v in variants)
    symbolic=sum(v['variant_kind']=='symbolic_global_policy_dp_v1' for v in variants)
    target=len(mapping_space()); relabel=len(mapping_space())
    unique_orders=sum(factorial(6)//__import__('math').prod(factorial(n) for n in sorted(__import__('collections').Counter(map(tuple,g['canonical_bank'])).values())) for g in bank_groups)
    collision_policies=len(properties['B_COLLISION']['witness']['policy_witnesses'])
    named_roles={'HASH_00','B_SEPARABLE','B_COLLISION','B_DECOY','B_BALANCED_MARGINAL'}
    named_group_count=sum(bool(named_roles & set(group['role_ids'])) for group in bank_groups)
    counts={
      'GEN_AUTHORITY_HASH':len(EXPECTED_AUTHORITY),'GEN_BANK_COVERAGE':B,'GEN_ARM_ROW_COVERAGE':L*B*target*(T+G),
      'GEN_ABL_SOURCE_DELETE':L*B*target,'GEN_ABL_LOCAL_SHIFT_DELETE':L*B*target,
      'GEN_ABL_NO_UPDATE':L*B*target*2,'GEN_ABL_ACTIVE_DELETE':L*B*target,
      'GEN_ABL_QUERY_OUTCOME_MASK':L*B*target,'GEN_ABL_POSTQUERY_SOURCE_DELETE':L*B*target,
      'GEN_ABL_SHAM_ROTATION':L*B*target*2,'GEN_ABL_MULTIPLICITY_FLATTEN':L*B*target,
      'GEN_INV_SOURCE_ORDER_ENUM':unique_orders,'GEN_INV_SOURCE_ORDER_LINEAGE':T,
      'GEN_INV_SOURCE_ORDER_SABOTAGE':1,
      'GEN_INV_TOKEN_RELABEL':L*named_group_count*3*target*relabel,
      'GEN_INV_PROTOTYPE_RELABEL':L*named_group_count*3*target*relabel,
      'GEN_INV_EIG_ENTROPY_ALIAS':lex*B*3*5,'GEN_ABL_NO_QUERY':lex*B*3*target,
      'GEN_PROPERTY_B_SEPARABLE':lex,'GEN_PROPERTY_B_COLLISION':lex*collision_policies,
      'GEN_PROPERTY_B_DECOY':lex,'GEN_PROPERTY_B_BALANCED_MARGINAL':lex,
      'GEN_PROPERTY_MULT_6':lex*target,
      'GEN_LEAKAGE_POSITIVE_CONTROL':len(_frozen_design()['leakage']['forbidden_classes'])*2,
      'GEN_AMORTIZED_PUBLIC_STATE':85*B,
      'GEN_FRESH_TRAJECTORY_RECOMPUTE':lex*B*target*T,
      'GEN_FRESH_AGGREGATE_RECOMPUTE':lex*B*target*G,
      'GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE':lex*B*target*T,
      'GEN_INDEPENDENT_AGGREGATE_RECOMPUTE':lex*B*target*G,
      'GEN_SYMBOLIC_LOCAL_CONTRIBUTION':symbolic*B,
      'GEN_SYMBOLIC_LOCAL_AGGREGATE':symbolic,
    }
    return counts


_FACTOR_KEYS = {
    'factor_id', 'factor_kind', 'canonical_bank_sha256', 'role_id',
    'target_mapping', 'h1_outcome', 'gate_ids', 'scope_variable_keys',
    'table_rows', 'factor_sha256',
}
_FACTOR_TABLE_KEYS = {
    'assignment_bytes', 'assignment_sha256',
    'partial_contribution_bytes', 'partial_contribution_sha256',
}


def _leaf_variable_key_non_evidence(bank_hash: str, arm_id: str, outcome: int) -> str:
    _hex_digest(bank_hash, 'bank hash')
    _arm_record(arm_id)
    outcome = _strict_int(outcome, name='H1 outcome', minimum=0, maximum=4)
    return f'{bank_hash}\x1f{arm_id}\x1f{outcome}'


@lru_cache(maxsize=None)
def _leaf_domain_cached_non_evidence(
    bank: tuple[tuple[int, ...], ...], arm_id: str, outcome: int, median: str,
) -> tuple[int, ...]:
    decision = query_decision(
        arm_id, bank, [{'token_index': 0, 'prototype_index': outcome}],
        median_convention=median,
    )
    domain = tuple(decision['minimizing_tokens'])
    if not domain or len(domain) > 4 or domain != tuple(sorted(set(domain))):
        raise ValueError('leaf domain must be the complete sorted exact minimizer set')
    return domain


def _leaf_variable_row_non_evidence(
    bank_row: dict[str, Any], arm_id: str, outcome: int, median: str,
) -> dict[str, Any]:
    bank = tuple(map(tuple, bank_row['canonical_bank']))
    bank_hash = bank_row['canonical_bank_sha256']
    return {
        'variable_key': _leaf_variable_key_non_evidence(bank_hash, arm_id, outcome),
        'canonical_bank_sha256': bank_hash,
        'arm_id': arm_id,
        'h1_outcome': outcome,
        'domain_tokens': list(_leaf_domain_cached_non_evidence(
            bank, arm_id, outcome, median,
        )),
    }


def _factor_scope_arms_non_evidence(
    gate_ids: list[str], left_arm_id: str, right_arm_id: str,
) -> list[str]:
    c = _frozen_design()['arm_registry']['primary_conservative']
    p = PUBLIC_ARM_ID
    arms = set()
    for gate_id in gate_ids:
        known = False
        if gate_id in {'MEMBER_FORWARD_CONSERVATIVE', 'SOURCE_DELETE'}:
            arms.update((c, p)); known = True
        elif gate_id == 'MEMBER_FORWARD_RAW':
            arms.update((left_arm_id, p)); known = True
        elif gate_id.startswith('CONTROL_PARETO:'):
            arms.update((c, right_arm_id, p)); known = True
        elif gate_id == 'CONSISTENCY_POSITIVE_NON_EQUIVALENCE':
            arms.update((c, right_arm_id)); known = True
        elif gate_id.startswith('MEMBER_FAILURE:'):
            arms.update((left_arm_id, p)); known = True
        elif gate_id in {
            'CAUSAL_EFFECT:ABL_NO_UPDATE',
            'CAUSAL_EFFECT:ABL_QUERY_OUTCOME_MASK',
        }:
            arms.update((c, right_arm_id, p)); known = True
        elif gate_id.startswith('CAUSAL_EFFECT:') or gate_id.startswith('PROPERTY_'):
            arms.update((left_arm_id, right_arm_id)); known = True
        if not known:
            raise ValueError(f'unmapped gate ID: {gate_id}')
    return sorted(arms)


def _factor_id_non_evidence(
    gate_ids, role_id, target_mapping, h1_outcome, scope_variable_keys,
) -> str:
    compact = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'))
    preimage = '\x1f'.join((
        'FACTOR', compact(gate_ids), role_id, compact(target_mapping),
        compact(h1_outcome), compact(scope_variable_keys),
    )).encode('utf-8')
    return sha256(preimage).hexdigest()


def _property_h1_outcome_non_evidence(role_id: str) -> int:
    witness = scan_property_banks()[role_id]['witness']
    outcome = witness.get('h1_outcome')
    return _strict_int(outcome, name='property H1 outcome', minimum=0, maximum=4)


def _real_factor_descriptors_non_evidence(
    bank_row: dict[str, Any], median: str,
) -> list[dict[str, Any]]:
    if median not in {'lower', 'midpoint_integer', 'upper'}:
        raise ValueError('unknown median convention')
    bank_hash = bank_row['canonical_bank_sha256']
    bank_roles = set(bank_row['role_ids'])
    primary = sorted(_frozen_design()['bank_suite']['primary_role_ids'])
    properties = sorted(_frozen_design()['bank_suite']['property_predicates'])
    descriptors = []
    for pair in _gate_query_pairs(primary, properties):
        for role_id in sorted(bank_roles & set(pair['role_ids'])):
            gates = list(pair['gate_ids'])
            if gates == ['PROPERTY_B_DECOY']:
                points = [(None, _property_h1_outcome_non_evidence('B_DECOY'))]
            elif gates == ['PROPERTY_B_BALANCED_MARGINAL']:
                points = [(None, _property_h1_outcome_non_evidence('B_BALANCED_MARGINAL'))]
            elif gates == ['CAUSAL_EFFECT:ABL_ACTIVE_DELETE']:
                points = [(list(target), None) for target in sorted(set(map(
                    tuple, bank_row['canonical_bank'],
                )))]
            else:
                points = [(list(target), None) for target in mapping_space()]
            for target_mapping, named_h1 in points:
                outcome = named_h1 if target_mapping is None else target_mapping[0]
                arms = _factor_scope_arms_non_evidence(
                    gates, pair['left_arm_id'], pair['right_arm_id'],
                )
                scope = [
                    _leaf_variable_key_non_evidence(bank_hash, arm_id, outcome)
                    for arm_id in arms
                ]
                scope = sorted(set(scope))
                if len(scope) not in (1, 2, 3):
                    raise ValueError('real factor scope must be unary, pair, or ternary')
                descriptors.append({
                    'factor_id': _factor_id_non_evidence(
                        gates, role_id, target_mapping, named_h1, scope,
                    ),
                    'factor_kind': {1: 'UNARY_GATE', 2: 'PAIR_GATE', 3: 'TERNARY_GATE'}[len(scope)],
                    'canonical_bank_sha256': bank_hash,
                    'role_id': role_id,
                    'target_mapping': target_mapping,
                    'h1_outcome': named_h1,
                    'gate_ids': gates,
                    'scope_variable_keys': scope,
                    'left_arm_id': pair['left_arm_id'],
                    'right_arm_id': pair['right_arm_id'],
                })
    applicable_pairs = [
        pair for pair in _gate_query_pairs(primary, properties)
        if bank_roles & set(pair['role_ids'])
    ]
    all_arms = sorted({
        arm for pair in applicable_pairs
        for arm in (pair['left_arm_id'], pair['right_arm_id'], PUBLIC_ARM_ID)
    })
    anchor_candidates = [
        _leaf_variable_key_non_evidence(bank_hash, arm_id, outcome)
        for arm_id in all_arms for outcome in range(5)
    ]
    if anchor_candidates:
        anchor = min(anchor_candidates)
        anchor_outcome = int(anchor.rsplit('\x1f', 1)[1])
        for role_id, gate_id in (
            ('B_SEPARABLE', 'PROPERTY_B_SEPARABLE'),
            ('B_COLLISION', 'PROPERTY_B_COLLISION'),
        ):
            if role_id in bank_roles:
                scope = [anchor]
                gates = [gate_id]
                descriptors.append({
                    'factor_id': _factor_id_non_evidence(
                        gates, role_id, None, anchor_outcome, scope,
                    ),
                    'factor_kind': 'UNARY_GATE',
                    'canonical_bank_sha256': bank_hash,
                    'role_id': role_id,
                    'target_mapping': None,
                    'h1_outcome': anchor_outcome,
                    'gate_ids': gates,
                    'scope_variable_keys': scope,
                    'left_arm_id': anchor.split('\x1f')[1],
                    'right_arm_id': anchor.split('\x1f')[1],
                })
    unique = {}
    for row in descriptors:
        key = row['factor_id']
        if key in unique and unique[key] != row:
            raise ValueError('factor ID collision')
        unique[key] = row
    return [unique[key] for key in sorted(unique)]


def _metric_value_non_evidence(metric: dict[str, Any], key: str) -> Fraction:
    return _decode_rational(metric['metric_rationals'][key])


def _factor_metric_non_evidence(
    context: dict[str, Any], arm_id: str, target: tuple[int, ...],
    candidate_token: int, public_token: int,
) -> dict[str, Any]:
    key = (arm_id, target, candidate_token, public_token)
    if key not in context['metrics']:
        context['metrics'][key] = validate_arm_target_metric(evaluate_target(
            context['bank'], target, arm_id,
            median_convention=context['median'],
            query_policy={'candidate': candidate_token, 'public': public_token},
        ))
    return context['metrics'][key]


def _member_predicate_non_evidence(
    metric: dict[str, Any], public_metric: dict[str, Any], *, canonical: bool,
) -> bool:
    tau_f = _threshold_fraction('member_full_improvement_min')
    tau = _threshold_fraction('canonical_member_common_forward_min')
    full = _metric_value_non_evidence(public_metric, 'candidate_full_endpoint_mae') - _metric_value_non_evidence(metric, 'candidate_full_endpoint_mae') >= tau_f
    common = _metric_value_non_evidence(metric, 'common_unqueried_forward_improvement') >= (tau if canonical else 0)
    same = _metric_value_non_evidence(metric, 'same_history_forward_improvement') >= (tau if canonical else 0)
    return full and common and same


def _set_and_non_evidence(value: dict[str, Any], key: str, predicate: bool) -> None:
    value[key] = value[key] and bool(predicate)


def _set_or_non_evidence(value: dict[str, Any], key: str, predicate: bool) -> None:
    value[key] = value[key] or bool(predicate)


def _factor_cell_contribution_non_evidence(
    descriptor: dict[str, Any], assignment: dict[str, int],
    bank_row: dict[str, Any], median: str, context: dict[str, Any],
) -> dict[str, Any]:
    bank_hash = bank_row['canonical_bank_sha256']
    result = _local_contribution_identity_non_evidence(bank_hash, bank_row['role_ids'])
    bank = context['bank']
    outcome = (
        descriptor['h1_outcome'] if descriptor['target_mapping'] is None
        else descriptor['target_mapping'][0]
    )
    arm_tokens = {
        key.split('\x1f')[1]: assignment[key]
        for key in descriptor['scope_variable_keys']
    }
    def token(arm_id: str) -> int:
        if arm_id in arm_tokens:
            return arm_tokens[arm_id]
        return _leaf_domain_cached_non_evidence(bank, arm_id, outcome, median)[0]
    p_token = token(PUBLIC_ARM_ID)
    target = None if descriptor['target_mapping'] is None else tuple(descriptor['target_mapping'])
    metric_cache = {}
    def metric(arm_id: str):
        if arm_id not in metric_cache:
            metric_cache[arm_id] = _factor_metric_non_evidence(
                context, arm_id, target, token(arm_id), p_token,
            )
        return metric_cache[arm_id]
    c = _frozen_design()['arm_registry']['primary_conservative']
    support = set(map(tuple, bank_row['canonical_bank']))
    canonical = tuple(bank_row['canonical_member'])
    is_member = target in support if target is not None else False
    is_canonical = target == canonical if target is not None else False
    classification = classify_target(bank, target) if target is not None else None
    tau_f = _threshold_fraction('member_full_improvement_min')
    tau = _threshold_fraction('canonical_member_common_forward_min')
    for gate_id in descriptor['gate_ids']:
        if gate_id in {'MEMBER_FORWARD_CONSERVATIVE', 'MEMBER_FORWARD_RAW'}:
            arm = descriptor['left_arm_id']
            prefix = 'conservative' if gate_id.endswith('CONSERVATIVE') else 'raw'
            row, public = metric(arm), metric(PUBLIC_ARM_ID)
            if is_member:
                f_ok = _metric_value_non_evidence(public, 'candidate_full_endpoint_mae') - _metric_value_non_evidence(row, 'candidate_full_endpoint_mae') >= tau_f
                _set_and_non_evidence(result, f'{prefix}_member_full_all', f_ok)
                _set_and_non_evidence(result, f'{prefix}_member_common_all', _metric_value_non_evidence(row, 'common_unqueried_forward_improvement') >= 0)
                _set_and_non_evidence(result, f'{prefix}_member_same_history_all', _metric_value_non_evidence(row, 'same_history_forward_improvement') >= 0)
            if is_canonical:
                _set_and_non_evidence(result, f'{prefix}_canonical_common_all', _metric_value_non_evidence(row, 'common_unqueried_forward_improvement') >= tau)
                _set_and_non_evidence(result, f'{prefix}_canonical_same_history_all', _metric_value_non_evidence(row, 'same_history_forward_improvement') >= tau)
            if classification['distance'] in (2, 3, 4, 5):
                regret = _metric_value_non_evidence(row, 'candidate_full_endpoint_mae') - _metric_value_non_evidence(public, 'candidate_full_endpoint_mae')
                _set_and_non_evidence(result, f'{prefix}_bounded_safety_all', regret <= tau)
                if prefix == 'conservative':
                    _set_and_non_evidence(result, 'conservative_strict_safety_all', regret <= 0)
        elif gate_id == 'SOURCE_DELETE':
            row, public = metric(c), metric(PUBLIC_ARM_ID)
            if is_member:
                _set_or_non_evidence(result, 'source_delete_member_failure_seen', not _member_predicate_non_evidence(public, public, canonical=is_canonical))
                reduction = (_metric_value_non_evidence(public, 'candidate_full_endpoint_mae') - _metric_value_non_evidence(row, 'candidate_full_endpoint_mae'))
                _set_and_non_evidence(result, 'source_delete_reduction_all', reduction >= tau_f)
            semantic_cache = context.setdefault('source_delete_semantics', {})
            semantic_key = (target, median)
            if semantic_key not in semantic_cache:
                registered = execute_registered_ablation(
                    'ABL_SOURCE_DELETE', bank, target,
                    median_convention=median,
                )
                if (
                    registered.get('ablation_id') != 'ABL_SOURCE_DELETE'
                    or registered.get('registered') is not True
                    or registered.get('executed_arm_ids') != [PUBLIC_ARM_ID]
                    or registered.get('public_byte_identity') is not True
                ):
                    raise ValueError('source-delete registered producer mismatch')
                semantic_output = registered.get('semantic_output')
                if (
                    type(semantic_output) is not list
                    or len(semantic_output) != 1
                    or semantic_output[0].get('arm_id') != PUBLIC_ARM_ID
                    or type(semantic_output[0].get('trace')) is not dict
                ):
                    raise ValueError('source-delete registered trace mismatch')
                canonical_public, _ = _run_live_semantic_trace(
                    PUBLIC_ARM_ID, bank, target,
                    initial_token_index=0,
                    median_convention=median,
                )
                ablation_trace = semantic_output[0]['trace']
                if _canonical_json_bytes(ablation_trace) != _canonical_json_bytes(
                    canonical_public
                ):
                    raise ValueError('source-delete semantic callable identity mismatch')
                hashes = registered.get('semantic_hashes')
                if (
                    type(hashes) is not dict
                    or hashes.get('ablation') != _semantic_sha256(ablation_trace)
                    or hashes.get('canonical_public') != _semantic_sha256(canonical_public)
                ):
                    raise ValueError('source-delete semantic hash mismatch')
                semantic_cache[semantic_key] = True
        elif gate_id.startswith('CONTROL_PARETO:'):
            k = gate_id.split(':', 1)[1]
            cm, km = metric(c), metric(k)
            control = next(row for row in result['control_relations'] if row['control_arm_id'] == k)
            fc = _metric_value_non_evidence(cm, 'candidate_full_endpoint_mae'); fk = _metric_value_non_evidence(km, 'candidate_full_endpoint_mae')
            control['full_no_worse_all'] &= fk <= fc
            control['strict_witness_seen'] |= fk < fc
            control['metric_rationals_equal_all'] &= _canonical_json_bytes(km['metric_rationals']) == _canonical_json_bytes(cm['metric_rationals'])
            if is_member:
                pair = _pairwise_common_mae(km, cm)
                pkc = _decode_rational(pair['left_mae']); pck = _decode_rational(pair['right_mae'])
                control['member_common_no_worse_all'] &= pkc <= pck
                control['strict_witness_seen'] |= pkc < pck
        elif gate_id == 'CONSISTENCY_POSITIVE_NON_EQUIVALENCE':
            k = descriptor['right_arm_id']; cm, km = metric(c), metric(k)
            _set_and_non_evidence(result, 'consistency_full_no_regression_all', _metric_value_non_evidence(cm, 'candidate_full_endpoint_mae') <= _metric_value_non_evidence(km, 'candidate_full_endpoint_mae'))
            if is_member:
                pair = _pairwise_common_mae(km, cm)
                _set_or_non_evidence(result, 'consistency_common_advantage_witness_seen', _decode_rational(pair['left_mae']) - _decode_rational(pair['right_mae']) >= tau)
        elif gate_id.startswith('MEMBER_FAILURE:'):
            a = descriptor['left_arm_id']
            if is_member:
                failed = not _member_predicate_non_evidence(metric(a), metric(PUBLIC_ARM_ID), canonical=is_canonical)
                field = {
                    'ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK': 'no_update_evsi_member_failure_seen',
                    'ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK': 'no_update_passive_member_failure_seen',
                    'ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK': 'mask_member_failure_seen',
                    'ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1': 'postquery_member_failure_seen',
                    'ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK': 'sham_lcb_member_failure_seen',
                    'ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN': 'sham_raw_member_failure_seen',
                }[a]
                _set_or_non_evidence(result, field, failed)
        elif gate_id in {'CAUSAL_EFFECT:ABL_NO_UPDATE', 'CAUSAL_EFFECT:ABL_QUERY_OUTCOME_MASK'}:
            if is_canonical:
                a = descriptor['right_arm_id']; cm, am = metric(c), metric(a)
                effect = (
                    _metric_value_non_evidence(cm, 'common_unqueried_forward_improvement') - _metric_value_non_evidence(am, 'common_unqueried_forward_improvement') >= tau
                    or _metric_value_non_evidence(cm, 'same_history_forward_improvement') - _metric_value_non_evidence(am, 'same_history_forward_improvement') >= tau
                )
                field = 'mask_effect_witness_seen' if gate_id.endswith('QUERY_OUTCOME_MASK') else ('no_update_passive_effect_witness_seen' if 'PASSIVE' in a else 'no_update_evsi_effect_witness_seen')
                _set_or_non_evidence(result, field, effect)
        elif gate_id == 'CAUSAL_EFFECT:ABL_POSTQUERY_SOURCE_DELETE':
            if is_canonical:
                cm, am = metric(c), metric(descriptor['right_arm_id'])
                _set_or_non_evidence(result, 'postquery_effect_witness_seen', _metric_value_non_evidence(cm, 'same_history_forward_improvement') - _metric_value_non_evidence(am, 'same_history_forward_improvement') >= tau)
        elif gate_id == 'CAUSAL_EFFECT:ABL_ACTIVE_DELETE':
            if is_member:
                cm, am = metric(c), metric(descriptor['right_arm_id'])
                pair = _pairwise_common_mae(am, cm)
                q1, q2 = cm['query_decision'], am['query_decision']
                witness = len(q1['minimizing_tokens']) == len(q2['minimizing_tokens']) == 1 and q1['selected_token'] != q2['selected_token'] and _decode_rational(pair['left_mae']) - _decode_rational(pair['right_mae']) >= tau
                _set_or_non_evidence(result, 'active_delete_witness_seen', witness)
        elif gate_id == 'CAUSAL_EFFECT:ABL_LOCAL_SHIFT_DELETE':
            if classification['distance'] == 2:
                a = descriptor['right_arm_id']
                ct, _ = _run_live_semantic_trace(c, bank, target, initial_token_index=0, median_convention=median, query_policy=token(c))
                at, _ = _run_live_semantic_trace(a, bank, target, initial_token_index=0, median_convention=median, query_policy=token(a))
                cp, ap = _behavior_semantic_payload(ct), _behavior_semantic_payload(at)
                state_change = cp['state_h1'] != ap['state_h1'] or cp['state_final'] != ap['state_final']
                qc, qa = cp['query_decision']['selected_token'], ap['query_decision']['selected_token']
                unqueried = set(range(1, 5)) - {qc, qa}
                behavior = cp['query_decision'] != ap['query_decision'] or any(cp['prediction_decision']['prediction_micro'][i] != ap['prediction_decision']['prediction_micro'][i] for i in unqueried)
                _set_or_non_evidence(result, 'local_delete_witness_seen', state_change and behavior)
        elif gate_id in {'CAUSAL_EFFECT:ABL_MULTIPLICITY_FLATTEN', 'PROPERTY_MULT_6'}:
            a = descriptor['right_arm_id']
            ct, _ = _run_live_semantic_trace(c, bank, target, initial_token_index=0, median_convention=median, query_policy=token(c))
            at, _ = _run_live_semantic_trace(a, bank, target, initial_token_index=0, median_convention=median, query_policy=token(a))
            _set_and_non_evidence(result, 'property_mult6_all', _canonical_json_bytes(_behavior_semantic_payload(ct)) == _canonical_json_bytes(_behavior_semantic_payload(at)))
        elif gate_id == 'CAUSAL_EFFECT:ABL_SHAM_ROTATION':
            pass
        elif gate_id == 'PROPERTY_B_DECOY':
            left = query_decision(descriptor['left_arm_id'], bank, [{'token_index': 0, 'prototype_index': outcome}], median_convention=median, query_policy=token(descriptor['left_arm_id']))
            right = query_decision(descriptor['right_arm_id'], bank, [{'token_index': 0, 'prototype_index': outcome}], median_convention=median, query_policy=token(descriptor['right_arm_id']))
            _set_and_non_evidence(result, 'property_decoy_all', len(left['minimizing_tokens']) == len(right['minimizing_tokens']) == 1 and left['selected_token'] != right['selected_token'])
        elif gate_id == 'PROPERTY_B_BALANCED_MARGINAL':
            left = query_decision(descriptor['left_arm_id'], bank, [{'token_index': 0, 'prototype_index': outcome}], median_convention=median, query_policy=token(descriptor['left_arm_id']))
            right = query_decision(descriptor['right_arm_id'], bank, [{'token_index': 0, 'prototype_index': outcome}], median_convention=median, query_policy=token(descriptor['right_arm_id']))
            comparable = lambda q: {k: q[k] for k in ('exact_scores', 'minimizing_tokens', 'selected_token')}
            witness = _balanced_marginal_witness(bank)
            _set_and_non_evidence(result, 'property_balanced_all', witness is not None and len(left['minimizing_tokens']) == 4 and comparable(left) == comparable(right))
        elif gate_id == 'PROPERTY_B_SEPARABLE':
            _set_and_non_evidence(result, 'property_separable_all', _separable_witness(bank) == scan_property_banks()['B_SEPARABLE']['witness'])
        elif gate_id == 'PROPERTY_B_COLLISION':
            _set_and_non_evidence(result, 'property_collision_all', _collision_witnesses(bank) == scan_property_banks()['B_COLLISION']['witness'])
        else:
            raise ValueError(f'unmapped gate ID: {gate_id}')
    return _validate_local_contribution_non_evidence(result)


def _factor_wire_non_evidence(factor: dict[str, Any], *, omit_hash: bool = False) -> dict[str, Any]:
    keys = _FACTOR_KEYS - ({'factor_sha256'} if omit_hash else set())
    if type(factor) is not dict or set(factor) != _FACTOR_KEYS:
        raise ValueError('real factor schema drift')
    wire = {}
    for key in keys:
        if key == 'table_rows':
            wire[key] = [{
                'assignment_bytes': row['assignment_bytes'].decode('ascii'),
                'assignment_sha256': row['assignment_sha256'],
                'partial_contribution_bytes': row['partial_contribution_bytes'].decode('ascii'),
                'partial_contribution_sha256': row['partial_contribution_sha256'],
            } for row in factor['table_rows']]
        else:
            wire[key] = deepcopy(factor[key])
    return wire


def _validate_real_factor_non_evidence(
    factor: Any, leaf_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if type(factor) is not dict or set(factor) != _FACTOR_KEYS:
        raise ValueError('real factor schema drift')
    _hex_digest(factor['factor_id'], 'factor ID')
    _hex_digest(factor['canonical_bank_sha256'], 'factor bank hash')
    scope = factor['scope_variable_keys']
    if type(scope) is not list or scope != sorted(set(scope)) or len(scope) not in (1, 2, 3):
        raise ValueError('factor scope drift')
    if factor['factor_kind'] != {1: 'UNARY_GATE', 2: 'PAIR_GATE', 3: 'TERNARY_GATE'}[len(scope)]:
        raise ValueError('factor kind/scope drift')
    if any(key not in leaf_rows for key in scope):
        raise ValueError('factor scope leaf missing')
    if (factor['target_mapping'] is None) == (factor['h1_outcome'] is None):
        raise ValueError('exactly one factor point selector required')
    expected_id = _factor_id_non_evidence(
        factor['gate_ids'], factor['role_id'], factor['target_mapping'],
        factor['h1_outcome'], scope,
    )
    if factor['factor_id'] != expected_id:
        raise ValueError('factor ID mismatch')
    rows = factor['table_rows']
    expected_count = 1
    for key in scope:
        expected_count *= len(leaf_rows[key]['domain_tokens'])
    if type(rows) is not list or len(rows) != expected_count or len(rows) > 64:
        raise ValueError('factor table must enumerate the complete <=64 domain')
    expected_assignments = [
        _assignment_bytes_non_evidence(dict(zip(scope, values)))
        for values in product(*(leaf_rows[key]['domain_tokens'] for key in scope))
    ]
    if [row.get('assignment_bytes') for row in rows] != expected_assignments:
        raise ValueError('factor table assignment order/domain drift')
    for row in rows:
        if type(row) is not dict or set(row) != _FACTOR_TABLE_KEYS:
            raise ValueError('factor table row schema drift')
        if row['assignment_sha256'] != sha256(row['assignment_bytes']).hexdigest():
            raise ValueError('factor assignment hash mismatch')
        value = row['partial_contribution_bytes']
        if type(value) is not bytes or row['partial_contribution_sha256'] != sha256(value).hexdigest():
            raise ValueError('factor contribution hash mismatch')
        decoded = json.loads(value.decode('ascii'))
        if _canonical_json_bytes(decoded) != value:
            raise ValueError('factor contribution bytes not canonical')
        contribution = _validate_local_contribution_non_evidence(decoded)
        if contribution['canonical_bank_sha256'] != factor['canonical_bank_sha256']:
            raise ValueError('factor contribution bank mismatch')
    expected_hash = sha256(_canonical_json_bytes(
        _factor_wire_non_evidence(factor, omit_hash=True)
    )).hexdigest()
    if factor['factor_sha256'] != expected_hash:
        raise ValueError('factor hash mismatch')
    return deepcopy(factor)


def _build_real_factor_non_evidence(
    descriptor: dict[str, Any], bank_row: dict[str, Any], median: str,
    context: dict[str, Any], leaf_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scope = descriptor['scope_variable_keys']
    for key in scope:
        if key not in leaf_rows:
            arm_id, outcome = key.split('\x1f')[1:]
            leaf_rows[key] = _leaf_variable_row_non_evidence(
                bank_row, arm_id, int(outcome), median,
            )
    table_rows = []
    for values in product(*(leaf_rows[key]['domain_tokens'] for key in scope)):
        assignment = dict(zip(scope, values))
        assignment_bytes = _assignment_bytes_non_evidence(assignment)
        contribution = _factor_cell_contribution_non_evidence(
            descriptor, assignment, bank_row, median, context,
        )
        contribution_bytes = _canonical_json_bytes(contribution)
        table_rows.append({
            'assignment_bytes': assignment_bytes,
            'assignment_sha256': sha256(assignment_bytes).hexdigest(),
            'partial_contribution_bytes': contribution_bytes,
            'partial_contribution_sha256': sha256(contribution_bytes).hexdigest(),
        })
    factor = {
        **{key: deepcopy(descriptor[key]) for key in (
            'factor_id', 'factor_kind', 'canonical_bank_sha256', 'role_id',
            'target_mapping', 'h1_outcome', 'gate_ids', 'scope_variable_keys',
        )},
        'table_rows': table_rows,
        'factor_sha256': '',
    }
    factor['factor_sha256'] = sha256(_canonical_json_bytes(
        _factor_wire_non_evidence(factor, omit_hash=True)
    )).hexdigest()
    return _validate_real_factor_non_evidence(factor, leaf_rows)


def _factor_relation_non_evidence(factor: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for table_row in factor['table_rows']:
        assignment = {
            item['variable_key']: item['query_token']
            for item in json.loads(table_row['assignment_bytes'].decode('ascii'))
        }
        contribution = json.loads(table_row['partial_contribution_bytes'].decode('ascii'))
        rows.append(_relation_row_non_evidence(assignment, contribution))
    return _relation_factor_non_evidence(rows, factor['scope_variable_keys'])


def _factor_changes_class_non_evidence(
    factor: dict[str, Any], field_class: str,
) -> bool:
    for row in factor['table_rows']:
        value = json.loads(row['partial_contribution_bytes'].decode('ascii'))
        if field_class == 'all':
            if any(not value[key] for key in _LOCAL_ALL_FIELDS) or any(
                not control[key]
                for control in value['control_relations']
                for key in _CONTROL_ALL_FIELDS
            ):
                return True
        elif field_class == 'seen':
            if any(value[key] for key in _LOCAL_SEEN_FIELDS) or any(
                control[key]
                for control in value['control_relations']
                for key in _CONTROL_SEEN_FIELDS
            ):
                return True
        else:
            raise ValueError('unknown contribution field class')
    return False


def _compatibility_receipt_non_evidence(left: dict, right: dict) -> dict[str, Any]:
    shared = set(left['scope_variable_keys']) & set(right['scope_variable_keys'])
    compatible = incompatible = False
    hashes = set()
    for factor in (left, right):
        hashes.update(row['partial_contribution_sha256'] for row in factor['table_rows'])
    for left_row in left['table_rows']:
        la = {x['variable_key']: x['query_token'] for x in json.loads(left_row['assignment_bytes'].decode('ascii'))}
        for right_row in right['table_rows']:
            ra = {x['variable_key']: x['query_token'] for x in json.loads(right_row['assignment_bytes'].decode('ascii'))}
            match = all(la[key] == ra[key] for key in shared)
            compatible |= match
            incompatible |= not match
    return {
        'compatible_pair_seen': compatible,
        'incompatible_pair_seen': incompatible,
        'distinct_partial_contribution_count': len(hashes),
    }


def _eligible_bank_motif_non_evidence(
    bank_row: dict[str, Any], median: str,
) -> dict[str, Any] | None:
    started = __import__('time').perf_counter()
    descriptors = _real_factor_descriptors_non_evidence(bank_row, median)
    leaf_rows: dict[str, dict[str, Any]] = {}
    context = {
        'bank': tuple(map(tuple, bank_row['canonical_bank'])),
        'median': median, 'metrics': {},
    }
    binary = []
    for descriptor in descriptors:
        if descriptor['factor_kind'] != 'PAIR_GATE':
            continue
        product_size = 1
        for key in descriptor['scope_variable_keys']:
            if key not in leaf_rows:
                arm_id, outcome = key.split('\x1f')[1:]
                leaf_rows[key] = _leaf_variable_row_non_evidence(
                    bank_row, arm_id, int(outcome), median,
                )
            product_size *= len(leaf_rows[key]['domain_tokens'])
        if product_size > 1:
            binary.append(descriptor)
    if not binary:
        return None
    f0 = _build_real_factor_non_evidence(
        binary[0], bank_row, median, context, leaf_rows,
    )
    f1 = None; compatibility = None
    f0_scope = set(f0['scope_variable_keys'])
    for descriptor in binary[1:]:
        scope = set(descriptor['scope_variable_keys'])
        if len(scope & f0_scope) != 1 or len(scope | f0_scope) != 3:
            continue
        f1 = _build_real_factor_non_evidence(
            descriptor, bank_row, median, context, leaf_rows,
        )
        compatibility = _compatibility_receipt_non_evidence(f0, f1)
        break
    if f1 is None:
        return None
    if not (
        compatibility['compatible_pair_seen']
        and compatibility['incompatible_pair_seen']
        and compatibility['distinct_partial_contribution_count'] >= 2
    ):
        return None
    retained_scope = sorted(f0_scope | set(f1['scope_variable_keys']))
    selected = [f0, f1]
    selected_ids = {f0['factor_id'], f1['factor_id']}
    for field_class in ('all', 'seen'):
        for descriptor in descriptors:
            if descriptor['factor_id'] in selected_ids:
                continue
            if not set(descriptor['scope_variable_keys']) <= set(retained_scope):
                continue
            factor = _build_real_factor_non_evidence(
                descriptor, bank_row, median, context, leaf_rows,
            )
            if _factor_changes_class_non_evidence(factor, field_class):
                selected.append(factor); selected_ids.add(factor['factor_id']); break
    for descriptor in descriptors:
        if descriptor['factor_id'] in selected_ids:
            continue
        scope = set(descriptor['scope_variable_keys'])
        if len(scope & set(retained_scope)) != 1 or scope <= set(retained_scope):
            continue
        outside = scope - set(retained_scope)
        factor = _build_real_factor_non_evidence(
            descriptor, bank_row, median, context, leaf_rows,
        )
        projected_rows = []
        for row in factor['table_rows']:
            assignment = {x['variable_key']: x['query_token'] for x in json.loads(row['assignment_bytes'].decode('ascii'))}
            if any(assignment[key] != leaf_rows[key]['domain_tokens'][0] for key in outside):
                continue
            kept = {key: assignment[key] for key in scope & set(retained_scope)}
            contribution = json.loads(row['partial_contribution_bytes'].decode('ascii'))
            projected_rows.append(_relation_row_non_evidence(kept, contribution))
        relation = _relation_factor_non_evidence(projected_rows, sorted(scope & set(retained_scope)))
        projected_table = []
        for row in relation['relation_rows']:
            projected_table.append({
                'assignment_bytes': row['assignment_bytes'],
                'assignment_sha256': sha256(row['assignment_bytes']).hexdigest(),
                'partial_contribution_bytes': row['contribution_bytes'],
                'partial_contribution_sha256': row['contribution_sha256'],
            })
        projected_descriptor = deepcopy(descriptor)
        projected_descriptor['scope_variable_keys'] = sorted(scope & set(retained_scope))
        projected_descriptor['factor_kind'] = 'UNARY_GATE'
        projected_descriptor['factor_id'] = _factor_id_non_evidence(
            projected_descriptor['gate_ids'], projected_descriptor['role_id'],
            projected_descriptor['target_mapping'], projected_descriptor['h1_outcome'],
            projected_descriptor['scope_variable_keys'],
        )
        projected = {
            **{key: projected_descriptor[key] for key in (
                'factor_id', 'factor_kind', 'canonical_bank_sha256', 'role_id',
                'target_mapping', 'h1_outcome', 'gate_ids', 'scope_variable_keys',
            )},
            'table_rows': projected_table, 'factor_sha256': '',
        }
        projected['factor_sha256'] = sha256(_canonical_json_bytes(
            _factor_wire_non_evidence(projected, omit_hash=True)
        )).hexdigest()
        _validate_real_factor_non_evidence(projected, leaf_rows)
        selected.append(projected); break
    unique_selected = {}
    for factor in selected:
        unique_selected[_canonical_json_bytes(_factor_wire_non_evidence(factor))] = factor
    selected = [unique_selected[key] for key in sorted(unique_selected)]
    # F0/F1 are normative positional rows even though the final set is otherwise
    # canonical; restore them first and canonicalize only the optional suffix.
    optional = [factor for factor in selected if factor['factor_id'] not in {f0['factor_id'], f1['factor_id']}]
    selected = [f0, f1] + sorted(optional, key=lambda factor: factor['factor_id'])
    return {
        'canonical_bank_sha256': bank_row['canonical_bank_sha256'],
        'role_ids': list(bank_row['role_ids']),
        'retained_leaf_variable_rows': [leaf_rows[key] for key in retained_scope],
        'retained_factor_rows': selected,
        'authority_factor_descriptors': descriptors,
        **compatibility,
        'build_seconds': __import__('time').perf_counter() - started,
    }


def _explicit_local_assignment_oracle_non_evidence(
    layer: dict[str, Any],
) -> list[bytes]:
    leaf_rows = layer['retained_leaf_variable_rows']
    keys = [row['variable_key'] for row in leaf_rows]
    if keys != sorted(keys) or len(keys) != 3:
        raise ValueError('explicit toy oracle requires exactly three sorted leaves')
    factors = sorted(layer['retained_factor_rows'], key=lambda row: row['factor_sha256'])
    reachable = {}
    for values in product(*(row['domain_tokens'] for row in leaf_rows)):
        assignment = dict(zip(keys, values))
        state = _local_contribution_identity_non_evidence(
            layer['canonical_bank_sha256'], layer['role_ids'],
        )
        for factor in factors:
            matches = []
            for table_row in factor['table_rows']:
                row_assignment = {
                    item['variable_key']: item['query_token']
                    for item in json.loads(table_row['assignment_bytes'].decode('ascii'))
                }
                if all(assignment[key] == value for key, value in row_assignment.items()):
                    matches.append(table_row)
            if len(matches) != 1:
                raise ValueError('explicit factor lookup must select exactly one cell')
            state = _merge_local_contributions_non_evidence(
                state,
                json.loads(matches[0]['partial_contribution_bytes'].decode('ascii')),
            )
        state_bytes = _canonical_json_bytes(state)
        reachable[state_bytes] = state_bytes
    return sorted(reachable)


def _symbolic_local_elimination_non_evidence(layer: dict[str, Any]) -> list[bytes]:
    retained = layer['retained_factor_rows']
    factors = [_factor_relation_non_evidence(factor) for factor in retained]
    result = _eliminate_factor_graph_non_evidence(
        factors,
        [row['variable_key'] for row in layer['retained_leaf_variable_rows']],
        factor_sha256s=[factor['factor_sha256'] for factor in retained],
    )
    return sorted({
        row['contribution_bytes'] for row in result['output_factor']['relation_rows']
    })


def _independent_outer_oracle_non_evidence(
    bank_local_bytes: list[tuple[str, list[bytes]]],
) -> dict[str, Any]:
    reach = {_canonical_json_bytes(_global_state_identity_non_evidence())}
    for bank_hash, local_rows in sorted(bank_local_bytes):
        _hex_digest(bank_hash, 'bank hash')
        next_reach = set()
        for state_bytes in sorted(reach):
            state = json.loads(state_bytes.decode('ascii'))
            for local_bytes in sorted(set(local_rows)):
                local = json.loads(local_bytes.decode('ascii'))
                if local['canonical_bank_sha256'] != bank_hash:
                    raise ValueError('explicit outer local bank mismatch')
                next_reach.add(_canonical_json_bytes(
                    _merge_global_local_non_evidence(state, local)
                ))
        reach = next_reach
    terminal = [{
        'state_bytes': state_bytes,
        'state_sha256': sha256(state_bytes).hexdigest(),
        'ordinary_branch': _terminal_ordinary_branch_non_evidence(
            json.loads(state_bytes.decode('ascii'))
        ),
    } for state_bytes in sorted(reach)]
    return {
        'terminal_state_rows': terminal,
        'reachable_ordinary_verdicts': sorted({row['ordinary_branch'] for row in terminal}),
    }


def _toy_instance_wire_non_evidence(
    median: str, layers: list[dict[str, Any]],
) -> dict[str, Any]:
    leaf_rows = sorted(
        (deepcopy(row) for layer in layers for row in layer['retained_leaf_variable_rows']),
        key=lambda row: row['variable_key'],
    )
    factors = sorted(
        (factor for layer in layers for factor in layer['retained_factor_rows']),
        key=lambda row: row['factor_id'],
    )
    return {
        'schema_version': 'TOY_FACTOR_INSTANCE_V1',
        'median_convention': median,
        'bank_group_sha256s': sorted(
            layer['canonical_bank_sha256'] for layer in layers
        ),
        'leaf_variable_rows': leaf_rows,
        'factor_rows': [_factor_wire_non_evidence(factor) for factor in factors],
    }


@lru_cache(maxsize=1)
def _small_instance_equivalence_receipt_cached_non_evidence() -> dict[str, Any]:
    started = __import__('time').perf_counter()
    forbidden = {
        '_join_relation_factors_non_evidence',
        '_eliminate_relation_variable_non_evidence',
        '_min_fill_selection_non_evidence',
        '_eliminate_factor_graph_non_evidence',
    }
    if forbidden & set(_explicit_local_assignment_oracle_non_evidence.__code__.co_names):
        raise AssertionError('explicit oracle calls a forbidden VE helper')
    banks = _gate_bank_groups()
    selected_by_median = {}
    suite = []
    maximum_scope = maximum_rows = 0
    per_median_seconds = {}
    for median in ('lower', 'midpoint_integer', 'upper'):
        median_started = __import__('time').perf_counter()
        selected = []
        for bank_row in banks:
            layer = _eligible_bank_motif_non_evidence(bank_row, median)
            if layer is not None:
                selected.append(layer)
                if len(selected) == 3:
                    break
        if len(selected) < 3:
            raise ValueError(f'fewer than three eligible toy banks for median {median}')
        selected_by_median[median] = selected
        per_median_seconds[median] = __import__('time').perf_counter() - median_started
        explicit_local = {}
        symbolic_local = {}
        for layer in selected:
            bank_hash = layer['canonical_bank_sha256']
            explicit_local[bank_hash] = _explicit_local_assignment_oracle_non_evidence(layer)
            symbolic_local[bank_hash] = _symbolic_local_elimination_non_evidence(layer)
            if explicit_local[bank_hash] != symbolic_local[bank_hash]:
                raise AssertionError('explicit and symbolic local contributions differ')
            maximum_scope = max(maximum_scope, *(len(row['scope_variable_keys']) for row in layer['retained_factor_rows']))
            maximum_rows = max(maximum_rows, *(len(row['table_rows']) for row in layer['retained_factor_rows']))
        for count in (1, 2, 3):
            layers = selected[:count]
            toy = _toy_instance_wire_non_evidence(median, layers)
            toy_bytes = _canonical_json_bytes(toy)
            toy_hash = sha256(toy_bytes).hexdigest()
            suite_id = sha256(
                f'DPEQ\x1f{median}\x1f{count}\x1f'.encode('utf-8') + toy_bytes
            ).hexdigest()
            explicit_outer = _independent_outer_oracle_non_evidence([
                (layer['canonical_bank_sha256'], explicit_local[layer['canonical_bank_sha256']])
                for layer in layers
            ])
            symbolic_outer = _outer_gate_dp_non_evidence([{
                'canonical_bank_sha256': layer['canonical_bank_sha256'],
                'local_contributions': [
                    json.loads(value.decode('ascii'))
                    for value in symbolic_local[layer['canonical_bank_sha256']]
                ],
            } for layer in layers])
            if (
                explicit_outer['terminal_state_rows'] != symbolic_outer['terminal_state_rows']
                or explicit_outer['reachable_ordinary_verdicts'] != symbolic_outer['reachable_ordinary_verdicts']
            ):
                raise AssertionError('explicit and symbolic outer DP results differ')
            suite.append({
                'suite_id': suite_id,
                'median_convention': median,
                'bank_count': count,
                'leaf_variable_keys': [row['variable_key'] for row in toy['leaf_variable_rows']],
                'toy_instance_sha256': toy_hash,
                'explicit_algorithm_id': 'explicit_toy_assignment_enumeration_v1',
                'symbolic_algorithm_id': 'symbolic_leaf_factor_elimination_plus_global_dp_v1',
            })
    suite_sha = sha256(_canonical_json_bytes(suite)).hexdigest()
    return {
        'schema_version': 'SMALL_INSTANCE_EQUIVALENCE_RECEIPT_NON_EVIDENCE_V1',
        'suite_rows': suite,
        'suite_sha256': suite_sha,
        'eligible_bank_counts_by_median': {median: 3 for median in selected_by_median},
        'selected_bank_layers_by_median': selected_by_median,
        'all_nine_equivalent': True,
        'maximum_factor_scope_size': maximum_scope,
        'maximum_factor_table_rows': maximum_rows,
        'explicit_oracle_called_ve_helpers': False,
        'per_median_seconds': per_median_seconds,
        'total_seconds': __import__('time').perf_counter() - started,
    }


def _small_instance_equivalence_receipt_non_evidence() -> dict[str, Any]:
    return deepcopy(_small_instance_equivalence_receipt_cached_non_evidence())


def _construct_gate_execution_plan() -> dict[str, Any]:
    validate_authority_hashes()
    design=_frozen_design(); banks=_gate_bank_groups(); variants=_gate_variants()
    primary=sorted(design['bank_suite']['primary_role_ids']); properties=sorted(design['bank_suite']['property_predicates'])
    arm_records=design['arm_registry']['records']; arm_ids=sorted(r['arm_id'] for r in arm_records)
    property_scan=scan_property_banks(); counts=_generator_expected_counts(banks,variants,arm_records,property_scan)
    generator_rows=[]
    for gid,kind,scope,keys,formula,producers,collection in _GATE_GENERATOR_SPECS:
        generator_rows.append({'generator_id':gid,'case_kind':kind,'scope_id':scope,
          'dimension_descriptor':_generator_descriptor(gid,arm_ids=arm_ids,bank_groups=banks,variants=variants),
          'dimension_keys':keys,'count_formula_id':formula,'expected_count':counts[gid],
          'expected_producer_ids':producers,'packet_collection':collection})
    authority_preimage=sorted(({'path':r['path'],'sha256':r['sha256']} for r in authority_receipts()),key=lambda r:r['path'])
    equivalence=_small_instance_equivalence_receipt_non_evidence()
    suite=equivalence['suite_rows']
    prereq={'schema_version':'PREREQUISITE_CASE_PLAN_V1','generator_rows':generator_rows,
      'expected_case_count':sum(counts.values()),
      'case_order':'generator_rows list order, then lexicographic product in descriptor dimension order',
      'case_id_digest_algorithm':'SHA256_LENGTH_PREFIXED_CASE_IDS_V1'}
    return {'schema_version':'GATE_EXECUTION_PLAN_V1',
      'authority_sha256':sha256(_canonical_json_bytes(authority_preimage)).hexdigest(),
      'primary_role_ids':primary,'property_role_ids':properties,'arm_ids':arm_ids,
      'ablation_ids':sorted(registered_ablation_ids()),'bank_groups':banks,
      'median_conventions':['lower','midpoint_integer','upper'],
      'query_sensitivity_execution_mode':'symbolic_global_policy_dp_v1',
      'variant_registry':variants,'query_sensitivity_pairs':_gate_query_pairs(primary,properties),
      'small_instance_equivalence_suite':suite,
      'small_instance_equivalence_suite_sha256':equivalence['suite_sha256'],
      'prerequisite_case_plan':prereq,
      'thresholds':{k:_rational(Fraction(v)) for k,v in sorted(design['thresholds'].items())},
      'ordinary_branch_ids':[5,6,7,8,9,10,11]}


def build_gate_execution_plan() -> dict[str, Any]:
    return _construct_gate_execution_plan()


def validate_gate_execution_plan(plan: dict) -> dict[str, Any]:
    if type(plan) is not dict or _canonical_json_bytes(plan) != _canonical_json_bytes(_construct_gate_execution_plan()):
        raise ValueError('normative execution plan mismatch')
    return deepcopy(plan)



def _case_row(generator_row: dict[str, Any], values: dict[str, Any], ordinal: int) -> dict[str, Any]:
    payload={k:None for k in ('canonical_bank_sha256','role_ids','arm_ids','target_mapping','variant_id','transformation_id','public_state_key')}
    payload.update({'schema_version':'PREREQUISITE_CASE_INPUT_V1','generator_id':generator_row['generator_id'],
      'case_kind':generator_row['case_kind'],'scope_id':generator_row['scope_id'],'ordinal':ordinal})
    payload.update(values)
    canonical=_canonical_json_bytes(payload)
    case_id=sha256((generator_row['generator_id']+'\x1f'+generator_row['case_kind']+'\x1f').encode()+canonical).hexdigest()
    return {'case_id':case_id,'case_kind':generator_row['case_kind'],'scope_id':generator_row['scope_id'],
      'canonical_input_bytes':canonical,'input_sha256':sha256(canonical).hexdigest(),
      'expected_producer_ids':list(generator_row['expected_producer_ids'])}


def _mixed_radix_indices(ordinal: int, lengths: tuple[int, ...]) -> tuple[int, ...]:
    total=1
    for length in lengths:
      if type(length) is not int or length<=0: raise ValueError('mixed-radix domain length drift')
      total*=length
    if type(ordinal) is not int or ordinal<0 or ordinal>=total:
      raise ValueError('generator ordinal outside exact domain')
    values=[0]*len(lengths); remainder=ordinal
    for position in range(len(lengths)-1,-1,-1):
      values[position]=remainder%lengths[position]; remainder//=lengths[position]
    return tuple(values)


def _generator_expected_nonnull_input_fields(generator_id: str) -> set[str]:
    base={'schema_version','generator_id','case_kind','scope_id','ordinal'}
    groups={
      'GEN_AUTHORITY_HASH':set(),
      'GEN_BANK_COVERAGE':{'canonical_bank_sha256','role_ids'},
      'GEN_ARM_ROW_COVERAGE':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping'},
      'GEN_INV_SOURCE_ORDER_ENUM':{'canonical_bank_sha256','role_ids','transformation_id'},
      'GEN_INV_SOURCE_ORDER_LINEAGE':{'arm_ids','transformation_id'},
      'GEN_INV_SOURCE_ORDER_SABOTAGE':{'transformation_id'},
      'GEN_INV_TOKEN_RELABEL':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping','transformation_id'},
      'GEN_INV_PROTOTYPE_RELABEL':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping','transformation_id'},
      'GEN_INV_EIG_ENTROPY_ALIAS':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','transformation_id'},
      'GEN_ABL_NO_QUERY':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping','transformation_id'},
      'GEN_PROPERTY_B_SEPARABLE':{'variant_id','canonical_bank_sha256','role_ids','transformation_id'},
      'GEN_PROPERTY_B_COLLISION':{'variant_id','canonical_bank_sha256','role_ids','transformation_id'},
      'GEN_PROPERTY_B_DECOY':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','transformation_id'},
      'GEN_PROPERTY_B_BALANCED_MARGINAL':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','transformation_id'},
      'GEN_PROPERTY_MULT_6':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping','transformation_id'},
      'GEN_LEAKAGE_POSITIVE_CONTROL':{'transformation_id'},
      'GEN_AMORTIZED_PUBLIC_STATE':{'canonical_bank_sha256','role_ids','arm_ids','public_state_key','transformation_id'},
      'GEN_FRESH_TRAJECTORY_RECOMPUTE':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping'},
      'GEN_FRESH_AGGREGATE_RECOMPUTE':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping'},
      'GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping'},
      'GEN_INDEPENDENT_AGGREGATE_RECOMPUTE':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping'},
      'GEN_SYMBOLIC_LOCAL_CONTRIBUTION':{'variant_id','canonical_bank_sha256','role_ids','arm_ids','transformation_id'},
      'GEN_SYMBOLIC_LOCAL_AGGREGATE':{'variant_id','transformation_id'},
    }
    ablations={spec[0] for spec in _GATE_GENERATOR_SPECS[3:11]}
    if generator_id in ablations:
      return base|{'variant_id','canonical_bank_sha256','role_ids','arm_ids','target_mapping','transformation_id'}
    if generator_id not in groups: raise ValueError('unknown prerequisite generator')
    return base|groups[generator_id]


def _generator_case_at_ordinal_non_evidence(plan: dict[str, Any], row: dict[str, Any], ordinal: int) -> dict[str, Any]:
    gid=row['generator_id']; count=row['expected_count']
    if type(ordinal) is not int or ordinal<0 or ordinal>=count:
      raise ValueError('generator ordinal outside exact domain')
    banks=plan['bank_groups']; variants=plan['variant_registry']; targets=plan['bank_groups'][0]['target_mappings']
    records={r['arm_id']:r for r in _frozen_design()['arm_registry']['records']}
    trajectory=sorted(a for a in plan['arm_ids'] if records[a]['kind']=='trajectory')
    aggregate=sorted(a for a in plan['arm_ids'] if records[a]['kind']=='aggregate')
    lexical=[v for v in variants if v['variant_kind']=='lexical']
    symbolic=[v for v in variants if v['variant_kind']=='symbolic_global_policy_dp_v1']
    values={}
    if gid=='GEN_AUTHORITY_HASH':
      pass
    elif gid=='GEN_BANK_COVERAGE':
      bank=banks[ordinal]; values={'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids']}
    elif gid=='GEN_ARM_ROW_COVERAGE':
      vi,bi,ti,ai=_mixed_radix_indices(ordinal,(len(variants),len(banks),len(targets),len(plan['arm_ids'])))
      bank=banks[bi]; values={'variant_id':variants[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'target_mapping':targets[ti],'arm_ids':[sorted(plan['arm_ids'])[ai]]}
    else:
      ablation_arms={
       'GEN_ABL_SOURCE_DELETE':['ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1'],
       'GEN_ABL_LOCAL_SHIFT_DELETE':['ARM_I_TRANSFER_NO_LOCAL__A_L1_EVSI__D_LCB05_FALLBACK'],
       'GEN_ABL_NO_UPDATE':['ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK','ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK'],
       'GEN_ABL_ACTIVE_DELETE':['ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK'],
       'GEN_ABL_QUERY_OUTCOME_MASK':['ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK'],
       'GEN_ABL_POSTQUERY_SOURCE_DELETE':['ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1'],
       'GEN_ABL_SHAM_ROTATION':['ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK','ARM_I_SHAM__A_L1_EVSI__D_L1_MEDIAN'],
       'GEN_ABL_MULTIPLICITY_FLATTEN':['ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK']}
      if gid in ablation_arms:
       arms=sorted(ablation_arms[gid]);vi,bi,ti,ai=_mixed_radix_indices(ordinal,(len(variants),len(banks),len(targets),len(arms)));bank=banks[bi]
       values={'variant_id':variants[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'target_mapping':targets[ti],'arm_ids':[arms[ai]],'transformation_id':'NONE'}
      elif gid=='GEN_INV_SOURCE_ORDER_ENUM':
       remaining=ordinal
       for bank in banks:
        multiplicities=__import__('collections').Counter(map(tuple,bank['canonical_bank'])).values();length=factorial(6)//__import__('math').prod(factorial(n) for n in multiplicities)
        if remaining<length:
         values={'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'transformation_id':f'SOURCE_ORDER:{remaining}'};break
        remaining-=length
      elif gid=='GEN_INV_SOURCE_ORDER_LINEAGE':
       arm=trajectory[ordinal];values={'arm_ids':[arm],'transformation_id':f'SOURCE_ORDER_CALL_CHAIN:{arm}'}
      elif gid=='GEN_INV_SOURCE_ORDER_SABOTAGE': values={'transformation_id':'SOURCE_ORDER_SABOTAGE'}
      elif gid in {'GEN_INV_TOKEN_RELABEL','GEN_INV_PROTOTYPE_RELABEL'}:
       named={'HASH_00','B_SEPARABLE','B_COLLISION','B_DECOY','B_BALANCED_MARGINAL'};groups=[b for b in banks if named&set(b['role_ids'])]
       scoped=sorted(_frozen_design()['ablation_registry']['records'][9 if gid=='GEN_INV_TOKEN_RELABEL' else 10]['scope_arms'])
       vi,bi,ai,ti,pi=_mixed_radix_indices(ordinal,(len(variants),len(groups),len(scoped),len(targets),len(mapping_space())));bank=groups[bi];prefix='TOKEN_PERM' if gid=='GEN_INV_TOKEN_RELABEL' else 'PROTOTYPE_PERM'
       values={'variant_id':variants[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'arm_ids':[scoped[ai]],'target_mapping':targets[ti],'transformation_id':f'{prefix}:{pi}'}
      elif gid=='GEN_INV_EIG_ENTROPY_ALIAS':
       pairs=[('I_TRANSFER','ARM_I_TRANSFER__A_EIG__D_LCB05_FALLBACK','ARM_I_TRANSFER__A_MAX_OUTCOME_ENTROPY__D_LCB05_FALLBACK'),('I_SCRATCH','ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1','ARM_I_SCRATCH__A_MAX_OUTCOME_ENTROPY__D_SCRATCH_L1'),('I_CONSISTENCY','ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN','ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN')]
       vi,bi,pi,outcome=_mixed_radix_indices(ordinal,(len(lexical),len(banks),len(pairs),5));bank=banks[bi];inference,left,right=pairs[pi]
       values={'variant_id':lexical[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'arm_ids':[left,right],'transformation_id':f'EIG_ENTROPY:{inference}:{outcome}'}
      elif gid=='GEN_ABL_NO_QUERY':
       arms=sorted(['ARM_I_TRANSFER__A_NO_QUERY__D_LCB05_FALLBACK','ARM_I_SCRATCH__A_NO_QUERY__D_SCRATCH_L1','ARM_I_CONSISTENCY__A_NO_QUERY__D_L1_MEDIAN']);vi,bi,ai,ti=_mixed_radix_indices(ordinal,(len(lexical),len(banks),len(arms),len(targets)));bank=banks[bi]
       values={'variant_id':lexical[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'arm_ids':[arms[ai]],'target_mapping':targets[ti],'transformation_id':'NONE'}
      elif gid.startswith('GEN_PROPERTY_'):
       role=row['scope_id'];bank=next(b for b in banks if role in b['role_ids']);w=(scan_property_banks()[role]['witness'] if role!='MULT_6' else None);c=_frozen_design()['arm_registry']['primary_conservative']
       if role=='B_COLLISION': policies=[x['policy'] for x in w['policy_witnesses']];vi,pi=_mixed_radix_indices(ordinal,(len(lexical),len(policies)));transform=f'PROPERTY_POLICY:{sha256(_canonical_json_bytes(policies[pi])).hexdigest()}';arms=None;target=None
       elif role=='B_SEPARABLE': vi=ordinal;transform=f"PROPERTY_POLICY:{sha256(_canonical_json_bytes(w['policy'])).hexdigest()}";arms=None;target=None
       elif role=='B_DECOY': vi=ordinal;transform=f"PROPERTY_H1:{role}:{w['h1_outcome']}";arms=sorted(['ARM_I_TRANSFER__A_EIG__D_L1_MEDIAN',_frozen_design()['arm_registry']['raw_upside']]);target=None
       elif role=='B_BALANCED_MARGINAL': vi=ordinal;transform=f"PROPERTY_H1:{role}:{w['h1_outcome']}";arms=sorted(['ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN','ARM_I_CONSISTENCY__A_MAX_OUTCOME_ENTROPY__D_L1_MEDIAN']);target=None
       else: vi,ti=_mixed_radix_indices(ordinal,(len(lexical),len(targets)));transform='NONE';arms=sorted([c,'ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK']);target=targets[ti]
       values={'variant_id':lexical[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'transformation_id':transform}
       if arms is not None: values['arm_ids']=arms
       if target is not None: values['target_mapping']=target
      elif gid=='GEN_LEAKAGE_POSITIVE_CONTROL':
       classes=_frozen_design()['leakage']['forbidden_classes'];ci,ki=_mixed_radix_indices(ordinal,(len(classes),2));values={'transformation_id':f"LEAKAGE:{classes[ci]}:{('DIRECT','ENCODED')[ki]}"}
      elif gid=='GEN_AMORTIZED_PUBLIC_STATE':
       bi,local=_mixed_radix_indices(ordinal,(len(banks),85));bank=banks[bi];h1=local//17;sub=local%17
       if sub==0: phase='H1';history=[{'token_index':0,'prototype_index':h1}]
       else:
        legal=[(token,outcome) for token in range(1,5) for outcome in range(5) if outcome!=h1];token,outcome=legal[sub-1];phase='H2';history=[{'token_index':0,'prototype_index':h1},{'token_index':token,'prototype_index':outcome}]
       canonical=tuple(map(tuple,bank['canonical_bank']));public_bytes=_canonical_public_input_bytes(_exact_primary_public_payload(canonical,history))
       values={'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'arm_ids':[PRIMARY_ARM_ID],'public_state_key':_public_state_key(public_bytes),'transformation_id':f'AMORTIZED:{phase}:{sha256(public_bytes).hexdigest()}'}
      elif gid in {'GEN_FRESH_TRAJECTORY_RECOMPUTE','GEN_INDEPENDENT_TRAJECTORY_RECOMPUTE','GEN_FRESH_AGGREGATE_RECOMPUTE','GEN_INDEPENDENT_AGGREGATE_RECOMPUTE'}:
       arms=trajectory if 'TRAJECTORY' in gid else aggregate;vi,bi,ti,ai=_mixed_radix_indices(ordinal,(len(lexical),len(banks),len(targets),len(arms)));bank=banks[bi]
       values={'variant_id':lexical[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'target_mapping':targets[ti],'arm_ids':[arms[ai]]}
      elif gid=='GEN_SYMBOLIC_LOCAL_CONTRIBUTION':
       vi,bi=_mixed_radix_indices(ordinal,(len(symbolic),len(banks)));bank=banks[bi];arms=sorted({p[k] for p in plan['query_sensitivity_pairs'] for k in ('left_arm_id','right_arm_id')});bundle=sha256(_canonical_json_bytes({'variant_id':symbolic[vi]['variant_id'],'bank':bank['canonical_bank_sha256']})).hexdigest()
       values={'variant_id':symbolic[vi]['variant_id'],'canonical_bank_sha256':bank['canonical_bank_sha256'],'role_ids':bank['role_ids'],'arm_ids':arms,'transformation_id':f'SYMBOLIC_LOCAL_BUNDLE:{bundle}'}
      elif gid=='GEN_SYMBOLIC_LOCAL_AGGREGATE':
       variant=symbolic[ordinal];bundle=sha256(_canonical_json_bytes({'variant_id':variant['variant_id'],'global':True})).hexdigest();values={'variant_id':variant['variant_id'],'transformation_id':f'SYMBOLIC_GLOBAL_DP_BUNDLE:{bundle}'}
      else: raise ValueError('unsupported prerequisite generator')
    result=_case_row(row,values,ordinal)
    decoded=json.loads(result['canonical_input_bytes'].decode('utf-8'))
    if {k for k,v in decoded.items() if v is not None}!=_generator_expected_nonnull_input_fields(gid):
      raise ValueError('generator case non-null field mapping drift')
    return result


def _iter_generator_cases(plan: dict[str, Any], row: dict[str, Any]):
    for ordinal in range(row['expected_count']):
      yield _generator_case_at_ordinal_non_evidence(plan,row,ordinal)

def iter_expected_prerequisite_cases(plan: dict):
    validated=validate_gate_execution_plan(plan)
    for row in validated['prerequisite_case_plan']['generator_rows']:
      yield from _iter_generator_cases(validated,row)


def _reject_stored_decisions(value: Any) -> None:
    forbidden={'verdict','stored_verdict','winner','stored_winner','passes','gate_pass'}
    if isinstance(value,dict):
      if forbidden & set(value): raise ValueError('stored verdict/winner fields are forbidden')
      for child in value.values(): _reject_stored_decisions(child)
    elif isinstance(value,list):
      for child in value: _reject_stored_decisions(child)


def _hex_digest(value: Any, name: str) -> str:
    if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
      raise ValueError(f'{name} must be lowercase SHA-256')
    return value


_LEDGER_HEADER_KEYS = {
    'variant_id', 'median_convention', 'variant_kind', 'query_policy_sha256',
    'symbolic_dp_sha256', 'envelope_rows_sha256',
}


def _validate_query_policy_row_non_evidence(
    plan: dict[str, Any],
    row: Any,
    *,
    median_convention: str,
) -> dict[str, Any]:
    """Validate one normative lexical policy anchor row.

    Alternative exact minimizers belong only in the symbolic factor/DP state.
    Every ledger row is the same-median lexical anchor, including symbolic
    ledgers; accepting any exact minimizer here would silently turn the wrapper
    into a concrete-policy ledger.
    """
    if type(row) is not dict or set(row) != {
        'canonical_bank_sha256', 'arm_id', 'choices_by_h1_outcome',
    }:
        raise ValueError('query policy row schema drift')
    bank_rows = {
        item['canonical_bank_sha256']: item for item in plan['bank_groups']
    }
    bank_row = bank_rows.get(row['canonical_bank_sha256'])
    if bank_row is None:
        raise ValueError('query policy bank domain drift')
    arm_id = row['arm_id']
    record = _arm_record(arm_id)
    if record['kind'] != 'trajectory' or record['acquisition_id'] == 'A_NO_QUERY':
        raise ValueError('query policy arm domain drift')
    choices = row['choices_by_h1_outcome']
    if type(choices) is not list or len(choices) != 5:
        raise ValueError('complete five-leaf query policy required')
    bank = tuple(map(tuple, bank_row['canonical_bank']))
    for outcome, supplied in enumerate(choices):
        supplied = _strict_int(
            supplied, name='query policy choice', minimum=0, maximum=4,
        )
        decision = query_decision(
            arm_id, bank,
            [{'token_index': 0, 'prototype_index': outcome}],
            median_convention=median_convention,
        )
        if supplied != decision['selected_token']:
            raise ValueError('query policy row must use the recomputed lexical choice')
    return deepcopy(row)


def _validate_envelope_row_non_evidence(
    plan: dict[str, Any],
    envelope: Any,
    *,
    expected_bank_row: dict[str, Any],
    expected_target_mapping: list[int],
    expected_arm_id: str,
    median_convention: str,
    query_policy_rows: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    expected_keys = set(
        _frozen_design()['closed_schemas']['VERIFIER_PRIVATE_ENVELOPE_V1']['keys']
    )
    if type(envelope) is not dict or set(envelope) != expected_keys:
        raise ValueError('verifier-private envelope schema drift')
    if envelope['schema_version'] != 'VERIFIER_PRIVATE_ENVELOPE_V1':
        raise ValueError('verifier-private envelope version drift')
    bank_hash = expected_bank_row['canonical_bank_sha256']
    if (
        envelope['bank_role_ids'] != expected_bank_row['role_ids']
        or envelope['canonical_bank_sha256'] != bank_hash
    ):
        raise ValueError('verifier-private envelope bank provenance drift')
    target = _validate_mapping(expected_target_mapping)
    if tuple(envelope['target_mapping']) != target:
        raise ValueError('verifier-private envelope target order drift')
    bank = tuple(map(tuple, expected_bank_row['canonical_bank']))
    classification = classify_target(bank, target)
    if any(envelope[key] != classification[key] for key in (
        'stratum', 'source_occurrence', 'distance',
    )):
        raise ValueError('verifier-private envelope classification drift')
    scorer_truth = [
        list(_prototype_table()[target[token]]) for token in range(5)
    ]
    if envelope['scorer_truth'] != scorer_truth:
        raise ValueError('verifier-private envelope scorer truth drift')
    if envelope['artifact_receipts'] != []:
        raise ValueError('verifier-private envelope artifact receipts must be empty')
    rows = envelope['metric_rows']
    if type(rows) is not list or len(rows) != 1:
        raise ValueError('verifier-private envelope requires one metric row')
    arm_record = _arm_record(expected_arm_id)
    public_row = query_policy_rows.get((bank_hash, PUBLIC_ARM_ID))
    public_leaf = (
        None if public_row is None
        else public_row['choices_by_h1_outcome'][target[0]]
    )
    candidate_row = query_policy_rows.get((bank_hash, expected_arm_id))
    candidate_leaf = (
        None if candidate_row is None
        else candidate_row['choices_by_h1_outcome'][target[0]]
    )
    if arm_record['kind'] == 'trajectory':
        stored = validate_arm_target_metric(rows[0])
    elif arm_record['kind'] == 'aggregate':
        stored = rows[0]
        keys = set(_frozen_design()['closed_schemas']['AGGREGATE_METRIC_V1']['keys'])
        if (
            type(stored) is not dict or set(stored) != keys
            or stored.get('schema_version') != 'AGGREGATE_METRIC_V1'
        ):
            raise ValueError('aggregate metric schema drift')
    else:
        raise ValueError('verifier-private envelope arm kind drift')
    if stored.get('arm_id') != expected_arm_id:
        raise ValueError('verifier-private envelope metric arm drift')
    live = evaluate_target(
        bank, target, expected_arm_id,
        median_convention=median_convention,
        query_policy={'candidate': candidate_leaf, 'public': public_leaf},
    )
    if _canonical_json_bytes(stored) != _canonical_json_bytes(live):
        raise ValueError('verifier-private envelope live recomputation mismatch')
    return deepcopy(envelope)


def _json_wire_tree_non_evidence(value: Any) -> Any:
    """Convert internal canonical byte leaves to their JSON string wire form."""
    if type(value) is bytes:
        try:
            return value.decode('ascii')
        except UnicodeDecodeError as exc:
            raise ValueError('symbolic wire bytes must be ASCII') from exc
    if type(value) is list:
        return [_json_wire_tree_non_evidence(item) for item in value]
    if type(value) is dict:
        return {
            key: _json_wire_tree_non_evidence(item)
            for key, item in value.items()
        }
    return deepcopy(value)


def _factor_from_json_wire_non_evidence(
    value: Any, leaf_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _FACTOR_KEYS:
        raise ValueError('symbolic factor row schema drift')
    factor = deepcopy(value)
    rows = factor['table_rows']
    if type(rows) is not list:
        raise ValueError('symbolic factor table rows drift')
    converted = []
    for row in rows:
        if type(row) is not dict or set(row) != _FACTOR_TABLE_KEYS:
            raise ValueError('symbolic factor table row schema drift')
        item = deepcopy(row)
        for field in ('assignment_bytes','partial_contribution_bytes'):
            if type(item[field]) is not str:
                raise ValueError('symbolic factor byte field must use JSON string wire form')
            try:
                item[field] = item[field].encode('ascii')
            except UnicodeEncodeError as exc:
                raise ValueError('symbolic factor byte field must be ASCII') from exc
        converted.append(item)
    factor['table_rows'] = converted
    return _validate_real_factor_non_evidence(factor, leaf_rows)


def _validate_symbolic_dp_state_non_evidence(
    plan: dict[str, Any], ledger: dict[str, Any], value: Any,
) -> dict[str, Any]:
    keys = {
        'schema_version', 'median_convention', 'leaf_variable_rows',
        'factor_rows', 've_trace_rows', 'local_state_rows', 'transition_rows',
        'initial_state_bytes', 'initial_state_sha256', 'terminal_state_rows',
        'reachable_ordinary_verdicts', 'equivalence_suite_sha256',
    }
    if type(value) is not dict or set(value) != keys:
        raise ValueError('symbolic DP state schema drift')
    if (
        value['schema_version'] != 'GATE_SYMBOLIC_QUERY_DP_V1'
        or value['median_convention'] != ledger['median_convention']
    ):
        raise ValueError('symbolic DP state identity drift')
    for name in (
        'leaf_variable_rows', 'factor_rows', 've_trace_rows',
        'local_state_rows', 'transition_rows', 'terminal_state_rows',
    ):
        if type(value[name]) is not list or not value[name]:
            raise ValueError(f'symbolic DP {name} must be nonempty')
    if value['equivalence_suite_sha256'] != plan[
        'small_instance_equivalence_suite_sha256'
    ]:
        raise ValueError('symbolic DP equivalence suite hash mismatch')

    leaf_keys = {
        'variable_key','canonical_bank_sha256','arm_id','h1_outcome',
        'domain_tokens',
    }
    observed_leaf_rows = value['leaf_variable_rows']
    if any(type(row) is not dict or set(row) != leaf_keys for row in observed_leaf_rows):
        raise ValueError('symbolic leaf variable row schema drift')
    query_arms = sorted({
        pair[field]
        for pair in plan['query_sensitivity_pairs']
        for field in ('left_arm_id','right_arm_id')
    })
    expected_leaf_rows = []
    leaf_by_key: dict[str, dict[str, Any]] = {}
    for bank_row in plan['bank_groups']:
        for arm_id in query_arms:
            for outcome in range(5):
                row = _leaf_variable_row_non_evidence(
                    bank_row, arm_id, outcome, ledger['median_convention'],
                )
                expected_leaf_rows.append(row)
                leaf_by_key[row['variable_key']] = row
    expected_leaf_rows.sort(key=lambda row: row['variable_key'])
    if observed_leaf_rows != expected_leaf_rows:
        raise ValueError('symbolic leaf variable domain/order/recomputation drift')

    observed_factor_rows = value['factor_rows']
    if (
        any(type(row) is not dict or set(row) != _FACTOR_KEYS for row in observed_factor_rows)
        or [row['factor_id'] for row in observed_factor_rows]
           != sorted(set(row['factor_id'] for row in observed_factor_rows))
    ):
        raise ValueError('symbolic factor row schema/order drift')
    internal_factors = [
        _factor_from_json_wire_non_evidence(row, leaf_by_key)
        for row in observed_factor_rows
    ]
    factors_by_bank: dict[str, list[dict[str, Any]]] = {
        row['canonical_bank_sha256']: [] for row in plan['bank_groups']
    }
    for factor in internal_factors:
        if factor['canonical_bank_sha256'] not in factors_by_bank:
            raise ValueError('symbolic factor bank domain drift')
        factors_by_bank[factor['canonical_bank_sha256']].append(factor)

    expected_factor_wires = []
    expected_ve_trace_rows = []
    expected_local_state_rows = []
    bank_local_rows = []
    global_step_ordinal = 0
    for bank_row in plan['bank_groups']:
        bank_hash = bank_row['canonical_bank_sha256']
        observed_bank_factors = factors_by_bank[bank_hash]
        descriptors = _real_factor_descriptors_non_evidence(
            bank_row, ledger['median_convention'],
        )
        if [row['factor_id'] for row in observed_bank_factors] != [
            row['factor_id'] for row in descriptors
        ]:
            raise ValueError('symbolic factor descriptor coverage drift')
        context = {
            'bank': tuple(map(tuple, bank_row['canonical_bank'])),
            'median': ledger['median_convention'], 'metrics': {},
        }
        recomputed = []
        for descriptor, observed in zip(descriptors, observed_bank_factors):
            live = _build_real_factor_non_evidence(
                descriptor, bank_row, ledger['median_convention'], context,
                leaf_by_key,
            )
            if _factor_wire_non_evidence(live) != _factor_wire_non_evidence(observed):
                raise ValueError('symbolic factor live recomputation mismatch')
            recomputed.append(live)
            expected_factor_wires.append(_factor_wire_non_evidence(live))
        vertices = sorted({
            key for factor in recomputed for key in factor['scope_variable_keys']
        })
        result = _eliminate_factor_graph_non_evidence(
            [_factor_relation_non_evidence(factor) for factor in recomputed],
            vertices,
            factor_sha256s=[factor['factor_sha256'] for factor in recomputed],
        )
        if result['terminal_join_trace_rows']:
            raise ValueError('symbolic factor graph emitted unbound terminal joins')
        for trace in result['ve_trace_rows']:
            trace = deepcopy(trace)
            trace['step_ordinal'] = global_step_ordinal
            global_step_ordinal += 1
            expected_ve_trace_rows.append(_json_wire_tree_non_evidence(trace))
        local_values = []
        for relation_row in result['output_factor']['relation_rows']:
            contribution_bytes = relation_row['contribution_bytes']
            contribution = json.loads(contribution_bytes.decode('ascii'))
            local_values.append(contribution)
            source_hash = sha256(
                _relation_row_bytes_non_evidence(relation_row)
            ).hexdigest()
            expected_local_state_rows.append({
                'canonical_bank_sha256': bank_hash,
                'contribution_bytes': contribution_bytes.decode('ascii'),
                'contribution_sha256': sha256(contribution_bytes).hexdigest(),
                'source_relation_row_sha256s': [source_hash],
            })
        if not local_values:
            raise ValueError('symbolic local state cannot be empty')
        bank_local_rows.append({
            'canonical_bank_sha256': bank_hash,
            'local_contributions': local_values,
        })
    expected_factor_wires.sort(key=lambda row: row['factor_id'])
    if observed_factor_rows != expected_factor_wires:
        raise ValueError('symbolic factor global order drift')
    if value['ve_trace_rows'] != expected_ve_trace_rows:
        raise ValueError('symbolic VE trace recomputation/order drift')
    expected_local_state_rows.sort(
        key=lambda row: (
            row['canonical_bank_sha256'], row['contribution_bytes'],
        )
    )
    if value['local_state_rows'] != expected_local_state_rows:
        raise ValueError('symbolic local state recomputation/order drift')

    outer = _outer_gate_dp_non_evidence(bank_local_rows)
    expected_initial_bytes = outer['initial_state_bytes'].decode('ascii')
    if (
        value['initial_state_bytes'] != expected_initial_bytes
        or value['initial_state_sha256'] != outer['initial_state_sha256']
        or value['transition_rows'] != _json_wire_tree_non_evidence(
            outer['transition_rows']
        )
        or value['terminal_state_rows'] != _json_wire_tree_non_evidence(
            outer['terminal_state_rows']
        )
        or value['reachable_ordinary_verdicts']
           != outer['reachable_ordinary_verdicts']
    ):
        raise ValueError('symbolic outer DP recomputation/order drift')
    initial_bytes = value['initial_state_bytes']
    if type(initial_bytes) is str: initial_bytes = initial_bytes.encode('ascii')
    if (
        type(initial_bytes) is not bytes
        or value['initial_state_sha256'] != sha256(initial_bytes).hexdigest()
    ):
        raise ValueError('symbolic DP initial state hash mismatch')
    try:
        initial = json.loads(initial_bytes.decode('ascii'))
    except Exception as exc:
        raise ValueError('symbolic DP initial state decoding failed') from exc
    if (
        _canonical_json_bytes(initial) != initial_bytes
        or initial != _global_state_identity_non_evidence()
    ):
        raise ValueError('symbolic DP initial state identity drift')
    reachable = value['reachable_ordinary_verdicts']
    if (
        type(reachable) is not list or not reachable
        or reachable != sorted(set(reachable))
        or any(branch not in plan['ordinary_branch_ids'] for branch in reachable)
    ):
        raise ValueError('symbolic DP reachable ordinary verdict list drift')
    terminal_branches = []
    prior_state_bytes = None
    for row in value['terminal_state_rows']:
        if type(row) is not dict or set(row) != {
            'state_bytes', 'state_sha256', 'ordinary_branch',
        }:
            raise ValueError('symbolic DP terminal row schema drift')
        state_bytes = row['state_bytes']
        if type(state_bytes) is str: state_bytes = state_bytes.encode('ascii')
        if (
            type(state_bytes) is not bytes
            or row['state_sha256'] != sha256(state_bytes).hexdigest()
            or (prior_state_bytes is not None and state_bytes <= prior_state_bytes)
        ):
            raise ValueError('symbolic DP terminal row order/hash drift')
        state = json.loads(state_bytes.decode('ascii'))
        if _canonical_json_bytes(state) != state_bytes:
            raise ValueError('symbolic DP terminal state not canonical')
        branch = _terminal_ordinary_branch_non_evidence(state)
        if row['ordinary_branch'] != branch:
            raise ValueError('symbolic DP terminal branch recomputation mismatch')
        terminal_branches.append(branch)
        prior_state_bytes = state_bytes
    if sorted(set(terminal_branches)) != reachable:
        raise ValueError('symbolic DP reachable/terminal mismatch')
    return deepcopy(value)


def _validate_ledger_collection_headers_non_evidence(
    plan: dict[str, Any], ledgers: Any,
) -> list[dict[str, Any]]:
    if type(ledgers) is not list or len(ledgers) != len(plan['variant_registry']):
        raise ValueError('exact six gate variant ledgers required')
    if len(plan['variant_registry']) != 6:
        raise ValueError('exact six normative variants required')
    for expected, ledger in zip(plan['variant_registry'], ledgers):
        if type(ledger) is not dict or not _LEDGER_HEADER_KEYS <= set(ledger):
            raise ValueError('gate variant ledger header schema drift')
        if any(ledger[key] != expected[key] for key in (
            'variant_id', 'median_convention', 'variant_kind',
        )):
            raise ValueError('gate variant ledger order/identity drift')
        _hex_digest(ledger['query_policy_sha256'], 'query policy hash')
        _hex_digest(ledger['envelope_rows_sha256'], 'envelope rows hash')
        if expected['variant_kind'] == 'lexical':
            if ledger['symbolic_dp_sha256'] is not None:
                raise ValueError('lexical ledger rejects symbolic state hash')
        else:
            _hex_digest(ledger['symbolic_dp_sha256'], 'symbolic DP hash')
    by_median = {}
    for ledger in ledgers:
        by_median.setdefault(ledger['median_convention'], {})[
            ledger['variant_kind']
        ] = ledger
    if set(by_median) != set(plan['median_conventions']):
        raise ValueError('gate variant ledger median coverage drift')
    for rows in by_median.values():
        if set(rows) != {'lexical', 'symbolic_global_policy_dp_v1'}:
            raise ValueError('gate variant ledger kind coverage drift')
        lexical = rows['lexical']
        symbolic = rows['symbolic_global_policy_dp_v1']
        if any(
            symbolic[key] != lexical[key]
            for key in ('query_policy_sha256', 'envelope_rows_sha256')
        ):
            raise ValueError('symbolic ledger must byte-match same-median lexical anchor')
    return deepcopy(ledgers)


def validate_gate_variant_ledger(plan: dict, ledger: dict) -> dict:
    plan=validate_gate_execution_plan(plan); _reject_stored_decisions(ledger)
    keys={'schema_version','execution_plan_sha256','variant_id','median_convention','variant_kind','query_policy_rows','query_policy_sha256','symbolic_dp_state','symbolic_dp_sha256','reachable_ordinary_verdicts','envelope_rows','envelope_rows_sha256'}
    if type(ledger) is not dict or set(ledger)!=keys: raise ValueError('gate variant ledger schema drift')
    if ledger['schema_version']!='GATE_VARIANT_LEDGER_V1': raise ValueError('gate variant ledger version drift')
    plan_hash=sha256(_canonical_json_bytes(plan)).hexdigest()
    if ledger['execution_plan_sha256']!=plan_hash: raise ValueError('execution plan hash mismatch')
    variants={r['variant_id']:r for r in plan['variant_registry']}
    if ledger['variant_id'] not in variants: raise ValueError('variant identity drift')
    expected_variant=variants[ledger['variant_id']]
    if any(ledger[k]!=expected_variant[k] for k in ('median_convention','variant_kind')): raise ValueError('variant identity drift')
    rows=ledger['query_policy_rows']
    if type(rows) is not list: raise ValueError('query policy rows must be ordered list')
    selectable=sorted(r['arm_id'] for r in _frozen_design()['arm_registry']['records'] if r['kind']=='trajectory' and r['acquisition_id']!='A_NO_QUERY')
    expected_keys=[(b['canonical_bank_sha256'],a) for b in plan['bank_groups'] for a in selectable]
    actual=[]; bank_by_hash={b['canonical_bank_sha256']:tuple(map(tuple,b['canonical_bank'])) for b in plan['bank_groups']}
    row_index = {}
    for row in rows:
      row = _validate_query_policy_row_non_evidence(
          plan, row, median_convention=ledger['median_convention'],
      )
      key=(row['canonical_bank_sha256'],row['arm_id']); actual.append(key)
      bank=bank_by_hash.get(key[0])
      if bank is None or key[1] not in selectable: raise ValueError('query policy domain drift')
      row_index[key] = row
    if actual!=expected_keys or len(set(actual))!=len(actual):
      raise ValueError('query policy rows are not the complete exact ordered domain')
    if ledger['query_policy_sha256']!=sha256(_canonical_json_bytes(rows)).hexdigest(): raise ValueError('query policy hash mismatch')
    if ledger['variant_kind']=='lexical':
      if ledger['symbolic_dp_state'] is not None or ledger['symbolic_dp_sha256'] is not None: raise ValueError('lexical ledger rejects symbolic state')
    else:
      symbolic = _validate_symbolic_dp_state_non_evidence(
          plan, ledger, ledger['symbolic_dp_state'],
      )
      if ledger['symbolic_dp_sha256']!=sha256(_canonical_json_bytes(symbolic)).hexdigest(): raise ValueError('symbolic DP hash mismatch')
    reachable=ledger['reachable_ordinary_verdicts']
    if type(reachable) is not list or not reachable or reachable!=sorted(set(reachable)) or any(v not in range(5,12) for v in reachable): raise ValueError('reachable ordinary verdict list drift')
    if ledger['variant_kind']=='lexical' and len(reachable)!=1:
      raise ValueError('lexical ledger requires exactly one ordinary verdict')
    if ledger['variant_kind']!='lexical' and reachable!=ledger['symbolic_dp_state']['reachable_ordinary_verdicts']:
      raise ValueError('symbolic ledger reachable verdict mismatch')
    envelopes=ledger['envelope_rows']
    if type(envelopes) is not list: raise ValueError('envelope rows must be ordered list')
    if ledger['envelope_rows_sha256']!=sha256(_canonical_json_bytes(envelopes)).hexdigest(): raise ValueError('envelope rows hash mismatch')
    expected_envelope_count=len(plan['bank_groups'])*len(mapping_space())*len(plan['arm_ids'])
    if len(envelopes)!=expected_envelope_count:
      raise ValueError('complete envelope row domain required')
    ordinal=0
    for bank_row in plan['bank_groups']:
      for target in bank_row['target_mappings']:
       for arm_id in plan['arm_ids']:
        _validate_envelope_row_non_evidence(
            plan, envelopes[ordinal], expected_bank_row=bank_row,
            expected_target_mapping=target, expected_arm_id=arm_id,
            median_convention=ledger['median_convention'],
            query_policy_rows=row_index,
        )
        ordinal += 1
    return deepcopy(ledger)


_PACKET_COLLECTIONS=('authority_receipts','bank_receipts','arm_coverage_receipts','ablation_semantic_records','property_records','invariance_records','leakage_records','amortized_records','replay_records','independent_recompute_records')
_PRODUCER_KEYS={'producer_id','producer_function','code_path_sha256','call_count','output_schema_id','canonical_output_bytes','output_sha256','pre_read_order_receipt_bytes','pre_read_order_receipt_sha256'}
_CASE_OUTPUT_SCHEMAS={
 'AUTHORITY_HASH':{'AUTHORITY_HASH_OUTPUT_V1'},'BANK_COVERAGE':{'BANK_COVERAGE_OUTPUT_V1'},
 'ARM_ROW_COVERAGE':{'ARM_COVERAGE_OUTPUT_V1'},'ABLATION_SEMANTIC':{'ABLATION_COMPARISON_OUTPUT_V1'},
 'INVARIANCE_SEMANTIC':{'INVARIANCE_COMPARISON_OUTPUT_V1','SOURCE_ORDER_LINEAGE_OUTPUT_V1'},
 'PROPERTY_WITNESS':{'PROPERTY_WITNESS_OUTPUT_V1'},
 'LEAKAGE_POSITIVE_CONTROL':{'LEAKAGE_VALIDATION_OUTPUT_V1'},
 'AMORTIZED_PUBLIC_STATE':{'AMORTIZED_COMPARISON_OUTPUT_V1'},
 'FRESH_PROCESS_TRAJECTORY_RECOMPUTE':{'RECOMPUTE_OUTPUT_V1'},
 'FRESH_PROCESS_AGGREGATE_RECOMPUTE':{'RECOMPUTE_OUTPUT_V1'},
 'INDEPENDENT_TRAJECTORY_RECOMPUTE':{'RECOMPUTE_OUTPUT_V1'},
 'INDEPENDENT_AGGREGATE_RECOMPUTE':{'RECOMPUTE_OUTPUT_V1'},
 'SYMBOLIC_LOCAL_CONTRIBUTION':{'RECOMPUTE_OUTPUT_V1'},
 'SYMBOLIC_LOCAL_AGGREGATE':{'RECOMPUTE_OUTPUT_V1'},
}

_PRODUCER_OUTPUT_SCHEMA = {
 'AUTHORITY_HASH_RECOMPUTE':'AUTHORITY_HASH_OUTPUT_V1',
 'BANK_CONSTRUCTOR_RECOMPUTE':'BANK_COVERAGE_OUTPUT_V1',
 'ARM_ROW_LIVE_RECOMPUTE':'ARM_COVERAGE_OUTPUT_V1',
 'ABLATION_LIVE_RECOMPUTE':'ABLATION_COMPARISON_OUTPUT_V1',
 'INVARIANCE_REFERENCE_RECOMPUTE':'INVARIANCE_COMPARISON_OUTPUT_V1',
 'INVARIANCE_TRANSFORM_RECOMPUTE':'INVARIANCE_COMPARISON_OUTPUT_V1',
 'SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE':'SOURCE_ORDER_LINEAGE_OUTPUT_V1',
 'SOURCE_ORDER_AST_DATAFLOW_AUDIT':'SOURCE_ORDER_LINEAGE_OUTPUT_V1',
 'SOURCE_ORDER_SABOTAGE_PROBE':'SOURCE_ORDER_LINEAGE_OUTPUT_V1',
 'PROPERTY_WITNESS_RECOMPUTE':'PROPERTY_WITNESS_OUTPUT_V1',
 'LEAKAGE_VALIDATOR_PROBE':'LEAKAGE_VALIDATION_OUTPUT_V1',
 'LIVE_PRIMARY_OUTPUT_RECOMPUTE':'AMORTIZED_COMPARISON_OUTPUT_V1',
 'AMORTIZED_LOOKUP_RECOMPUTE':'AMORTIZED_COMPARISON_OUTPUT_V1',
 'FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'FRESH_PROCESS_AGGREGATE_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'INDEPENDENT_PATH_TRAJECTORY_ROW_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'INDEPENDENT_PATH_AGGREGATE_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'FRESH_PROCESS_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'INDEPENDENT_PATH_SYMBOLIC_LOCAL_CONTRIBUTION_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'FRESH_PROCESS_SYMBOLIC_DP_AGGREGATE_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
 'INDEPENDENT_PATH_SYMBOLIC_DP_AGGREGATE_RECOMPUTE':'RECOMPUTE_OUTPUT_V1',
}


def _embedded_canonical_json_non_evidence(value: Any, *, name: str) -> tuple[bytes, Any]:
    if type(value) is str:
        try:
            payload = value.encode('ascii')
        except UnicodeEncodeError as exc:
            raise ValueError(f'{name} must be ASCII canonical JSON') from exc
    elif type(value) is bytes:
        payload = value
    else:
        raise ValueError(f'{name} must be canonical JSON bytes')
    try:
        decoded = json.loads(payload.decode('ascii'))
    except Exception as exc:
        raise ValueError(f'{name} decoding failed') from exc
    if _canonical_json_bytes(decoded) != payload:
        raise ValueError(f'{name} must be canonical JSON')
    _reject_stored_decisions(decoded)
    return payload, decoded


def _validate_aggregate_metric_non_evidence(value: Any) -> dict[str, Any]:
    keys = set(_frozen_design()['closed_schemas']['AGGREGATE_METRIC_V1']['keys'])
    if (
        type(value) is not dict or set(value) != keys
        or value.get('schema_version') != 'AGGREGATE_METRIC_V1'
    ):
        raise ValueError('aggregate metric schema drift')
    record = _arm_record(value['arm_id'])
    if record['kind'] != 'aggregate':
        raise ValueError('aggregate metric arm drift')
    expected_branches = _uniform_mixture_branch_ids(record)
    if value['branch_arm_ids'] != expected_branches:
        raise ValueError('aggregate metric branch registry drift')
    if value['branch_weights'] != [_rational(Fraction(1, 4))] * 4:
        raise ValueError('aggregate metric branch weights drift')
    rationals = value['expected_metric_rationals']
    if type(rationals) is not dict or set(rationals) != _METRIC_RATIONAL_KEYS:
        raise ValueError('aggregate metric rational keys drift')
    for rational in rationals.values():
        _decode_rational(rational)
    return deepcopy(value)


def _validate_live_semantic_trace_output_non_evidence(value: Any) -> dict[str, Any]:
    keys = {
        'schema_version', 'arm_id', 'public_history', 'state_h1',
        'query_decision', 'state_final', 'prediction_decision',
    }
    if (
        type(value) is not dict or set(value) != keys
        or value.get('schema_version') != 'LIVE_SEMANTIC_TRACE_V1'
    ):
        raise ValueError('live semantic trace schema drift')
    arm_id = value['arm_id']
    _arm_record(arm_id)
    history = _history_key(value['public_history'])
    state_h1 = validate_state(value['state_h1'])
    state_final = validate_state(value['state_final'])
    query = _validate_query_decision_metric_object(
        value['query_decision'], expected_arm_id=arm_id,
    )
    _validate_prediction_decision_metric_object(
        value['prediction_decision'], expected_arm_id=arm_id,
    )
    if (
        state_h1['arm_id'] != arm_id or state_h1['stage'] != 'H1'
        or state_final['arm_id'] != arm_id
        or state_final['feedback_count'] != len(history)
    ):
        raise ValueError('live semantic trace state linkage drift')
    expected_second = None if len(history) == 1 else history[1][0]
    if query['selected_token'] != expected_second:
        raise ValueError('live semantic trace query/history linkage drift')
    return deepcopy(value)


def _validate_invocation_receipt_non_evidence(
    receipt: Any,
    *,
    producer: dict[str, Any],
    case_input_sha256: str,
    nested_output_sha256: str,
) -> dict[str, Any]:
    keys = {
        'producer_function', 'input_sha256', 'code_path_sha256',
        'call_count', 'output_sha256',
    }
    if type(receipt) is not dict or set(receipt) != keys:
        raise ValueError('invocation receipt schema drift')
    expected = {
        'producer_function': producer['producer_function'],
        'input_sha256': case_input_sha256,
        'code_path_sha256': producer['code_path_sha256'],
        'call_count': producer['call_count'],
        'output_sha256': nested_output_sha256,
    }
    if receipt != expected:
        raise ValueError('invocation receipt linkage drift')
    return deepcopy(receipt)


def _validate_source_order_lineage_output_non_evidence(
    value: Any, *, producer_id: str, case_input: dict[str, Any],
) -> dict[str, Any]:
    keys = {
        'schema_version', 'receipt_kind', 'arm_id',
        'canonical_bank_sha256', 'call_rows', 'ast_dataflow_receipt',
        'canary_receipt',
    }
    if (
        type(value) is not dict or set(value) != keys
        or value.get('schema_version') != 'SOURCE_ORDER_LINEAGE_OUTPUT_V1'
    ):
        raise ValueError('source-order lineage output schema drift')
    kinds = {
        'SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE':'DYNAMIC_SPY',
        'SOURCE_ORDER_AST_DATAFLOW_AUDIT':'AST_DATAFLOW',
        'SOURCE_ORDER_SABOTAGE_PROBE':'SABOTAGE',
    }
    if value['receipt_kind'] != kinds[producer_id]:
        raise ValueError('source-order lineage receipt kind drift')
    call_keys = {
        'ordinal', 'caller_function', 'callee_function', 'input_bank_sha256',
        'validated_bank_sha256', 'downstream_bank_sha256',
    }
    calls = value['call_rows']
    if type(calls) is not list or calls != sorted(
        calls, key=lambda row: (
            row.get('ordinal'), row.get('caller_function'), row.get('callee_function'),
        ),
    ):
        raise ValueError('source-order lineage call row order drift')
    for ordinal, row in enumerate(calls):
        if type(row) is not dict or set(row) != call_keys:
            raise ValueError('source-order lineage call row schema drift')
        _strict_int(row['ordinal'], name='source-order call ordinal', minimum=0)
        if ordinal and row['ordinal'] < calls[ordinal - 1]['ordinal']:
            raise ValueError('source-order lineage call ordinal drift')
        for key in ('input_bank_sha256','validated_bank_sha256','downstream_bank_sha256'):
            _hex_digest(row[key], key)
    if producer_id == 'SOURCE_ORDER_DYNAMIC_SPY_RECOMPUTE':
        if not calls or value['ast_dataflow_receipt'] is not None or value['canary_receipt'] is not None:
            raise ValueError('dynamic-spy lineage payload drift')
        if value['arm_id'] != case_input['arm_ids'][0]:
            raise ValueError('dynamic-spy arm linkage drift')
        for row in calls:
            if not (
                row['validated_bank_sha256'] == row['downstream_bank_sha256']
                == row['input_bank_sha256']
            ):
                raise ValueError('dynamic-spy canonical bank lineage mismatch')
    elif producer_id == 'SOURCE_ORDER_AST_DATAFLOW_AUDIT':
        ast = value['ast_dataflow_receipt']
        ast_keys = {
            'source_path','source_sha256','root_function_names',
            'downstream_function_names','validated_assignment_name',
            'ast_dump_sha256','raw_bank_reachability_violations',
        }
        if type(ast) is not dict or set(ast) != ast_keys:
            raise ValueError('AST dataflow receipt schema drift')
        if ast['root_function_names'] != ['build_state','query_decision','prediction_decision']:
            raise ValueError('AST dataflow root function registry drift')
        if ast['downstream_function_names'] != [
            '_validate_bank','source_counts','local_counts','build_state',
            'query_decision','prediction_decision',
        ]:
            raise ValueError('AST dataflow downstream function registry drift')
        if ast['validated_assignment_name'] != 'validated_bank' or ast['raw_bank_reachability_violations'] != []:
            raise ValueError('AST dataflow reachability receipt drift')
        _hex_digest(ast['source_sha256'],'AST source hash')
        _hex_digest(ast['ast_dump_sha256'],'AST dump hash')
        if value['canary_receipt'] is not None:
            raise ValueError('AST dataflow rejects canary receipt')
    else:
        canary = value['canary_receipt']
        canary_keys = {
            'original_order_sha256','reversed_order_sha256',
            'detector_error_type','detector_error_message',
        }
        if type(canary) is not dict or set(canary) != canary_keys:
            raise ValueError('source-order sabotage canary schema drift')
        original = _hex_digest(canary['original_order_sha256'],'original-order hash')
        reversed_hash = _hex_digest(canary['reversed_order_sha256'],'reversed-order hash')
        if original == reversed_hash or not canary['detector_error_type'] or not canary['detector_error_message']:
            raise ValueError('source-order sabotage positive control failed')
        if calls or value['ast_dataflow_receipt'] is not None:
            raise ValueError('source-order sabotage payload drift')
    return deepcopy(value)


def _validate_recompute_output_non_evidence(
    plan: dict[str, Any], value: Any, *, case: dict[str, Any], case_input: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    keys = {
        'schema_version', 'recompute_kind', 'case_key',
        'canonical_row_or_aggregate_bytes',
    }
    if (
        type(value) is not dict or set(value) != keys
        or value.get('schema_version') != 'RECOMPUTE_OUTPUT_V1'
        or value.get('case_key') != case['case_id']
    ):
        raise ValueError('recompute output schema/linkage drift')
    child_bytes, child = _embedded_canonical_json_non_evidence(
        value['canonical_row_or_aggregate_bytes'], name='recompute child',
    )
    expected_kind = {
        'FRESH_PROCESS_TRAJECTORY_RECOMPUTE':'TRAJECTORY_ROW',
        'INDEPENDENT_TRAJECTORY_RECOMPUTE':'TRAJECTORY_ROW',
        'FRESH_PROCESS_AGGREGATE_RECOMPUTE':'AGGREGATE_METRIC',
        'INDEPENDENT_AGGREGATE_RECOMPUTE':'AGGREGATE_METRIC',
        'SYMBOLIC_LOCAL_CONTRIBUTION':'SYMBOLIC_LOCAL_CONTRIBUTION',
        'SYMBOLIC_LOCAL_AGGREGATE':'SYMBOLIC_DP_AGGREGATE',
    }[case['case_kind']]
    if value['recompute_kind'] != expected_kind:
        raise ValueError('recompute kind drift')
    if expected_kind in {'TRAJECTORY_ROW','AGGREGATE_METRIC'}:
        bank_row = next(
            row for row in plan['bank_groups']
            if row['canonical_bank_sha256'] == case_input['canonical_bank_sha256']
        )
        median = next(
            row['median_convention'] for row in plan['variant_registry']
            if row['variant_id'] == case_input['variant_id']
        )
        if expected_kind == 'TRAJECTORY_ROW':
            validate_arm_target_metric(child)
        else:
            _validate_aggregate_metric_non_evidence(child)
        live = evaluate_target(
            tuple(map(tuple, bank_row['canonical_bank'])),
            case_input['target_mapping'], case_input['arm_ids'][0],
            median_convention=median,
        )
        if _canonical_json_bytes(live) != child_bytes:
            raise ValueError('recompute child live mismatch')
    elif expected_kind == 'SYMBOLIC_LOCAL_CONTRIBUTION':
        if type(child) is not dict or set(child) != {
            'schema_version','factor_rows','ve_trace_rows','local_state_rows',
        } or child['schema_version'] != 'SYMBOLIC_LOCAL_RECOMPUTE_BUNDLE_V1':
            raise ValueError('symbolic local recompute bundle schema drift')
        if any(type(child[name]) is not list or not child[name] for name in (
            'factor_rows','ve_trace_rows','local_state_rows',
        )):
            raise ValueError('symbolic local recompute bundle incomplete')
    else:
        if type(child) is not dict or set(child) != {
            'schema_version','transition_rows','terminal_state_rows',
            'reachable_ordinary_verdicts',
        } or child['schema_version'] != 'SYMBOLIC_DP_RECOMPUTE_BUNDLE_V1':
            raise ValueError('symbolic DP recompute bundle schema drift')
        if (
            type(child['transition_rows']) is not list or not child['transition_rows']
            or type(child['terminal_state_rows']) is not list or not child['terminal_state_rows']
            or type(child['reachable_ordinary_verdicts']) is not list
            or not child['reachable_ordinary_verdicts']
        ):
            raise ValueError('symbolic DP recompute bundle incomplete')
    return deepcopy(value), sha256(child_bytes).hexdigest()


def _validate_producer_output_non_evidence(
    plan: dict[str, Any], case: dict[str, Any], producer: dict[str, Any], decoded: Any,
) -> str:
    case_input = json.loads(case['canonical_input_bytes'].decode('ascii'))
    schema_id = producer['output_schema_id']
    nested_hash = producer['output_sha256']
    if schema_id == 'AUTHORITY_HASH_OUTPUT_V1':
        keys={'schema_version','path','expected_sha256','actual_sha256'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('authority output schema drift')
        authority = sorted(EXPECTED_AUTHORITY.items())
        path, expected_hash = authority[case_input['ordinal']]
        if decoded != {'schema_version':schema_id,'path':path,'expected_sha256':expected_hash,'actual_sha256':_sha256(REPO_ROOT/path)}:
            raise ValueError('authority output recomputation mismatch')
    elif schema_id == 'BANK_COVERAGE_OUTPUT_V1':
        keys={'schema_version','canonical_bank_sha256','canonical_bank','role_ids','canonical_member','target_mappings'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('bank coverage output schema drift')
        expected = next(row for row in plan['bank_groups'] if row['canonical_bank_sha256']==case_input['canonical_bank_sha256'])
        if {key:decoded[key] for key in expected} != expected:
            raise ValueError('bank coverage output recomputation mismatch')
    elif schema_id == 'ARM_COVERAGE_OUTPUT_V1':
        keys={'schema_version','variant_id','canonical_bank_sha256','target_mapping','arm_id','metric_schema_id','metric_sha256'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('arm coverage output schema drift')
        arm_id=case_input['arm_ids'][0]; record=_arm_record(arm_id)
        expected_metric_schema='ARM_TARGET_METRIC_V1' if record['kind']=='trajectory' else 'AGGREGATE_METRIC_V1'
        if any(decoded[key]!=value for key,value in {
            'variant_id':case_input['variant_id'],'canonical_bank_sha256':case_input['canonical_bank_sha256'],
            'target_mapping':case_input['target_mapping'],'arm_id':arm_id,'metric_schema_id':expected_metric_schema,
        }.items()):
            raise ValueError('arm coverage output linkage drift')
        _hex_digest(decoded['metric_sha256'],'arm metric hash')
    elif schema_id in {'ABLATION_COMPARISON_OUTPUT_V1','INVARIANCE_COMPARISON_OUTPUT_V1'}:
        is_ablation=schema_id=='ABLATION_COMPARISON_OUTPUT_V1'
        keys=({'schema_version','ablation_id','arm_id','reference_behavior_bytes','intervened_behavior_bytes','invocation_receipt'} if is_ablation else {'schema_version','ablation_id','transformation_bytes','reference_behavior_bytes','inverse_mapped_behavior_bytes','invocation_receipt'})
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('semantic comparison output schema drift')
        if decoded['ablation_id'] != case['scope_id']:
            raise ValueError('semantic comparison scope linkage drift')
        reference_bytes, reference = _embedded_canonical_json_non_evidence(decoded['reference_behavior_bytes'],name='reference behavior')
        transformed_field='intervened_behavior_bytes' if is_ablation else 'inverse_mapped_behavior_bytes'
        transformed_bytes, transformed = _embedded_canonical_json_non_evidence(decoded[transformed_field],name='transformed behavior')
        _validate_live_semantic_trace_output_non_evidence(reference)
        _validate_live_semantic_trace_output_non_evidence(transformed)
        if is_ablation and decoded['arm_id'] != case_input['arm_ids'][0]:
            raise ValueError('ablation output arm linkage drift')
        _validate_invocation_receipt_non_evidence(
            decoded['invocation_receipt'], producer=producer,
            case_input_sha256=case['input_sha256'],
            nested_output_sha256=sha256(transformed_bytes).hexdigest(),
        )
        nested_hash=sha256(transformed_bytes).hexdigest()
    elif schema_id == 'SOURCE_ORDER_LINEAGE_OUTPUT_V1':
        _validate_source_order_lineage_output_non_evidence(
            decoded, producer_id=producer['producer_id'], case_input=case_input,
        )
    elif schema_id == 'PROPERTY_WITNESS_OUTPUT_V1':
        keys={'schema_version','property_role_id','witness_id','witness_tuple_bytes'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('property witness output schema drift')
        if decoded['property_role_id']!=case['scope_id'] or type(decoded['witness_id']) is not str or not decoded['witness_id']:
            raise ValueError('property witness output linkage drift')
        witness_bytes,_=_embedded_canonical_json_non_evidence(decoded['witness_tuple_bytes'],name='property witness tuple')
        nested_hash=sha256(witness_bytes).hexdigest()
    elif schema_id == 'LEAKAGE_VALIDATION_OUTPUT_V1':
        keys={'schema_version','forbidden_class','case_kind','error_type','error_message'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('leakage validation output schema drift')
        _,forbidden,kind=case_input['transformation_id'].split(':')
        if decoded['forbidden_class']!=forbidden or decoded['case_kind']!=kind or not decoded['error_type'] or not decoded['error_message']:
            raise ValueError('leakage positive-control output drift')
    elif schema_id == 'AMORTIZED_COMPARISON_OUTPUT_V1':
        keys={'schema_version','state_key','canonical_public_input_bytes','live_output_bytes','lookup_output_bytes'}
        if type(decoded) is not dict or set(decoded)!=keys or decoded.get('schema_version')!=schema_id:
            raise ValueError('amortized comparison output schema drift')
        if decoded['state_key']!=case_input['public_state_key']:
            raise ValueError('amortized state-key linkage drift')
        _,public_input=_embedded_canonical_json_non_evidence(decoded['canonical_public_input_bytes'],name='amortized public input')
        validated_input=validate_public_input(public_input)
        phase='H1' if validated_input['remaining_budget']==1 else 'H2'
        live_bytes,_=_embedded_canonical_json_non_evidence(decoded['live_output_bytes'],name='amortized live output')
        lookup_bytes,_=_embedded_canonical_json_non_evidence(decoded['lookup_output_bytes'],name='amortized lookup output')
        _validate_canonical_output_bytes(live_bytes,phase)
        _validate_canonical_output_bytes(lookup_bytes,phase)
        if live_bytes!=lookup_bytes:
            raise ValueError('amortized live/lookup mismatch')
        nested_hash=sha256(live_bytes).hexdigest()
    elif schema_id == 'RECOMPUTE_OUTPUT_V1':
        _,nested_hash=_validate_recompute_output_non_evidence(
            plan,decoded,case=case,case_input=case_input,
        )
    else:
        raise ValueError('unsupported producer output schema')
    return nested_hash


def _validate_pre_read_order_receipt_non_evidence(
    producer: dict[str, Any], *, case: dict[str, Any], nested_output_sha256: str,
) -> None:
    pre=producer['pre_read_order_receipt_bytes']; pre_hash=producer['pre_read_order_receipt_sha256']
    needs_pre=producer['producer_id'].startswith(('FRESH_PROCESS_','INDEPENDENT_PATH_'))
    if (pre is None)!=(pre_hash is None): raise ValueError('pre-read receipt pair drift')
    if needs_pre!=(pre is not None): raise ValueError('pre-read receipt applicability drift')
    if not needs_pre:
        return
    if type(pre) is not bytes or pre_hash!=sha256(pre).hexdigest():
        raise ValueError('pre-read receipt hash mismatch')
    try: receipt=json.loads(pre.decode('ascii'))
    except Exception as exc: raise ValueError('pre-read receipt decoding failed') from exc
    if _canonical_json_bytes(receipt)!=pre:
        raise ValueError('pre-read receipt must be canonical JSON')
    keys={'producer_id','input_sha256','recompute_start_ordinal','recompute_complete_ordinal','stored_bundle_read_ordinal','recomputed_output_sha256','stored_bundle_sha256'}
    if type(receipt) is not dict or set(receipt)!=keys:
        raise ValueError('pre-read receipt schema drift')
    if receipt['producer_id']!=producer['producer_id'] or receipt['input_sha256']!=case['input_sha256']:
        raise ValueError('pre-read receipt producer/input linkage drift')
    start=_strict_int(receipt['recompute_start_ordinal'],name='recompute start ordinal',minimum=0)
    complete=_strict_int(receipt['recompute_complete_ordinal'],name='recompute complete ordinal',minimum=0)
    stored=_strict_int(receipt['stored_bundle_read_ordinal'],name='stored bundle read ordinal',minimum=0)
    if not start < complete < stored:
        raise ValueError('pre-read order must satisfy start < complete < stored')
    if receipt['recomputed_output_sha256']!=nested_output_sha256 or receipt['stored_bundle_sha256']!=nested_output_sha256:
        raise ValueError('pre-read receipt output linkage drift')


def _iter_collection_cases(plan,collection):
    for row in plan['prerequisite_case_plan']['generator_rows']:
      if row['packet_collection']==collection: yield from _iter_generator_cases(plan,row)


def _validate_bounded_prerequisite_packet_prefix_non_evidence(plan: dict, packet: dict) -> dict:
    plan=validate_gate_execution_plan(plan); _reject_stored_decisions(packet)
    keys={'schema_version','execution_plan_sha256',*_PACKET_COLLECTIONS}
    if type(packet) is not dict or set(packet)!=keys: raise ValueError('gate prerequisite packet schema drift')
    if packet['schema_version']!='GATE_PREREQUISITE_PACKET_V1': raise ValueError('packet version drift')
    if packet['execution_plan_sha256']!=sha256(_canonical_json_bytes(plan)).hexdigest(): raise ValueError('execution plan hash mismatch')
    record_keys={'schema_version','case_id','case_kind','scope_id','canonical_input_bytes','input_sha256','producer_records'}
    for collection in _PACKET_COLLECTIONS:
      records=packet[collection]
      if type(records) is not list: raise ValueError('packet collection must be ordered list')
      expected_iter=_iter_collection_cases(plan,collection)
      for record in records:
       expected=next(expected_iter,None)
       if expected is None: raise ValueError('extra prerequisite record')
       if type(record) is not dict or set(record)!=record_keys: raise ValueError('prerequisite record schema drift')
       if record['schema_version']!='PREREQUISITE_CASE_RECORD_V1': raise ValueError('prerequisite record version drift')
       for key in ('case_id','case_kind','scope_id','canonical_input_bytes','input_sha256'):
        if record[key]!=expected[key]: raise ValueError('ordered prerequisite prefix mismatch')
       producers=record['producer_records']
       if type(producers) is not list or not producers: raise ValueError('producer records required')
       if [p.get('producer_id') for p in producers]!=sorted(expected['expected_producer_ids']): raise ValueError('producer ID schema mismatch')
       for producer in producers:
        if type(producer) is not dict or set(producer)!=_PRODUCER_KEYS: raise ValueError('producer record schema drift')
        producer_id=producer['producer_id']
        if producer_id not in _PRODUCER_OUTPUT_SCHEMA:
          raise ValueError('unknown producer ID')
        _hex_digest(producer['code_path_sha256'],'code path hash')
        if producer['producer_function']!=producer_id.lower():
          raise ValueError('producer function mapping drift')
        if _strict_int(producer['call_count'],name='call count',minimum=1)!=1:
          raise ValueError('producer call count drift')
        if (
          producer['output_schema_id'] not in _CASE_OUTPUT_SCHEMAS[record['case_kind']]
          or producer['output_schema_id'] != _PRODUCER_OUTPUT_SCHEMA[producer_id]
        ):
          raise ValueError('producer output schema ID mismatch')
        output=producer['canonical_output_bytes']
        if type(output) is not bytes or producer['output_sha256']!=sha256(output).hexdigest(): raise ValueError('producer output hash mismatch')
        try: decoded=json.loads(output.decode('utf-8'))
        except Exception as exc: raise ValueError('producer output must be canonical JSON') from exc
        if _canonical_json_bytes(decoded)!=output: raise ValueError('producer output must be canonical JSON')
        _reject_stored_decisions(decoded)
        nested_hash=_validate_producer_output_non_evidence(
          plan, expected, producer, decoded,
        )
        _validate_pre_read_order_receipt_non_evidence(
          producer, case=expected, nested_output_sha256=nested_hash,
        )
    return deepcopy(packet)


def validate_gate_prerequisite_packet(plan: dict, packet: dict) -> dict:
    validated=_validate_bounded_prerequisite_packet_prefix_non_evidence(plan,packet)
    for collection in _PACKET_COLLECTIONS:
      expected=sum(
        row['expected_count']
        for row in plan['prerequisite_case_plan']['generator_rows']
        if row['packet_collection']==collection
      )
      if len(validated[collection])!=expected:
        raise ValueError('complete formal prerequisite packet required')
    return validated


# C3B2B symbolic operators are deliberately private and non-evidence.  They
# implement the card's closed Boolean algebra and retain canonical preimages;
# they neither accept a formal packet nor emit a GATE_REDUCTION result.
_LOCAL_ALL_FIELDS = (
    'conservative_member_full_all', 'conservative_member_common_all',
    'conservative_member_same_history_all', 'conservative_canonical_common_all',
    'conservative_canonical_same_history_all', 'raw_member_full_all',
    'raw_member_common_all', 'raw_member_same_history_all',
    'raw_canonical_common_all', 'raw_canonical_same_history_all',
    'conservative_bounded_safety_all', 'conservative_strict_safety_all',
    'raw_bounded_safety_all', 'source_delete_reduction_all',
    'property_separable_all', 'property_collision_all', 'property_decoy_all',
    'property_balanced_all', 'property_mult6_all',
    'consistency_full_no_regression_all',
)
_LOCAL_SEEN_FIELDS = (
    'source_delete_member_failure_seen', 'active_delete_witness_seen',
    'local_delete_witness_seen', 'no_update_evsi_member_failure_seen',
    'no_update_evsi_effect_witness_seen',
    'no_update_passive_member_failure_seen',
    'no_update_passive_effect_witness_seen', 'mask_member_failure_seen',
    'mask_effect_witness_seen', 'postquery_member_failure_seen',
    'postquery_effect_witness_seen', 'sham_lcb_member_failure_seen',
    'sham_raw_member_failure_seen',
    'consistency_common_advantage_witness_seen',
)
_CONTROL_ALL_FIELDS = (
    'full_no_worse_all', 'member_common_no_worse_all',
    'metric_rationals_equal_all',
)
_CONTROL_SEEN_FIELDS = ('strict_witness_seen',)
_LOCAL_KEYS = {
    'schema_version', 'canonical_bank_sha256', 'role_ids', 'control_relations',
    *_LOCAL_ALL_FIELDS, *_LOCAL_SEEN_FIELDS,
}
_GLOBAL_KEYS = {
    'schema_version', 'control_relations', *_LOCAL_ALL_FIELDS,
    *_LOCAL_SEEN_FIELDS,
}
_CONTROL_KEYS = {
    'control_arm_id', *_CONTROL_ALL_FIELDS, *_CONTROL_SEEN_FIELDS,
}
_RELATION_ROW_KEYS = {
    'scope_variable_keys', 'assignment_bytes', 'contribution_bytes',
    'contribution_sha256',
}
_RELATION_FACTOR_KEYS = {
    'schema_version', 'scope_variable_keys', 'relation_rows',
}


def _identity_control_relations_non_evidence() -> list[dict[str, Any]]:
    return [{
        'control_arm_id': arm_id,
        **{key: True for key in _CONTROL_ALL_FIELDS},
        **{key: False for key in _CONTROL_SEEN_FIELDS},
    } for arm_id in _invalidating_control_ids()]


def _local_contribution_identity_non_evidence(
    canonical_bank_sha256: str,
    role_ids: list[str],
) -> dict[str, Any]:
    _hex_digest(canonical_bank_sha256, 'bank hash')
    if (
        type(role_ids) is not list or not role_ids
        or any(type(role_id) is not str or not role_id for role_id in role_ids)
        or role_ids != sorted(set(role_ids))
    ):
        raise ValueError('role IDs must be a complete sorted unique list')
    return _validate_local_contribution_non_evidence({
        'schema_version': 'GATE_LOCAL_CONTRIBUTION_V1',
        'canonical_bank_sha256': canonical_bank_sha256,
        'role_ids': list(role_ids),
        **{key: True for key in _LOCAL_ALL_FIELDS},
        **{key: False for key in _LOCAL_SEEN_FIELDS},
        'control_relations': _identity_control_relations_non_evidence(),
    })


def _validate_control_relations_non_evidence(value: Any) -> list[dict[str, Any]]:
    ids = _invalidating_control_ids()
    if type(value) is not list or len(value) != len(ids):
        raise ValueError('exact 19 control relations required')
    for expected_id, row in zip(ids, value):
        if type(row) is not dict or set(row) != _CONTROL_KEYS:
            raise ValueError('control relation schema drift')
        if row['control_arm_id'] != expected_id:
            raise ValueError('control relation order drift')
        if any(
            type(row[key]) is not bool
            for key in (*_CONTROL_ALL_FIELDS, *_CONTROL_SEEN_FIELDS)
        ):
            raise ValueError('control relation flags must be booleans')
    return deepcopy(value)


def _validate_local_contribution_non_evidence(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _LOCAL_KEYS:
        raise ValueError('local contribution schema drift')
    if value['schema_version'] != 'GATE_LOCAL_CONTRIBUTION_V1':
        raise ValueError('local contribution version drift')
    _hex_digest(value['canonical_bank_sha256'], 'bank hash')
    roles = value['role_ids']
    if (
        type(roles) is not list or not roles
        or any(type(role) is not str or not role for role in roles)
        or roles != sorted(set(roles))
    ):
        raise ValueError('role IDs must be a complete sorted unique list')
    if any(
        type(value[key]) is not bool
        for key in (*_LOCAL_ALL_FIELDS, *_LOCAL_SEEN_FIELDS)
    ):
        raise ValueError('local contribution flags must be booleans')
    _validate_control_relations_non_evidence(value['control_relations'])
    return deepcopy(value)


def _merge_control_relations_non_evidence(
    left: Any,
    right: Any,
) -> list[dict[str, Any]]:
    left = _validate_control_relations_non_evidence(left)
    right = _validate_control_relations_non_evidence(right)
    merged = []
    for left_row, right_row in zip(left, right):
        if left_row['control_arm_id'] != right_row['control_arm_id']:
            raise ValueError('control relation order drift')
        merged.append({
            'control_arm_id': left_row['control_arm_id'],
            **{
                key: left_row[key] and right_row[key]
                for key in _CONTROL_ALL_FIELDS
            },
            **{
                key: left_row[key] or right_row[key]
                for key in _CONTROL_SEEN_FIELDS
            },
        })
    return merged


def _merge_local_contributions_non_evidence(
    left: Any,
    right: Any,
) -> dict[str, Any]:
    left = _validate_local_contribution_non_evidence(left)
    right = _validate_local_contribution_non_evidence(right)
    if (
        left['canonical_bank_sha256'] != right['canonical_bank_sha256']
        or left['role_ids'] != right['role_ids']
    ):
        raise ValueError('bank identity and role IDs must match at joins')
    return _validate_local_contribution_non_evidence({
        'schema_version': 'GATE_LOCAL_CONTRIBUTION_V1',
        'canonical_bank_sha256': left['canonical_bank_sha256'],
        'role_ids': list(left['role_ids']),
        **{key: left[key] and right[key] for key in _LOCAL_ALL_FIELDS},
        **{key: left[key] or right[key] for key in _LOCAL_SEEN_FIELDS},
        'control_relations': _merge_control_relations_non_evidence(
            left['control_relations'], right['control_relations'],
        ),
    })


def _assignment_bytes_non_evidence(assignment: Any) -> bytes:
    if type(assignment) is not dict:
        raise ValueError('relation assignment must be a mapping')
    if any(type(key) is not str or not key for key in assignment):
        raise ValueError('relation variable keys must be nonempty strings')
    if any(
        type(token) is not int or not 0 <= token <= 4
        for token in assignment.values()
    ):
        raise ValueError('query token must be an integer in 0..4')
    return _canonical_json_bytes([
        {'variable_key': key, 'query_token': assignment[key]}
        for key in sorted(assignment)
    ])


def _decode_assignment_non_evidence(
    value: Any,
    scope_variable_keys: list[str],
) -> dict[str, int]:
    if type(value) is not bytes:
        raise ValueError('assignment bytes required')
    try:
        rows = json.loads(value.decode('ascii'))
    except Exception as exc:
        raise ValueError('assignment bytes must be canonical JSON') from exc
    if type(rows) is not list or _canonical_json_bytes(rows) != value:
        raise ValueError('assignment bytes must be canonical JSON')
    assignment = {}
    actual_keys = []
    for row in rows:
        if type(row) is not dict or set(row) != {'variable_key', 'query_token'}:
            raise ValueError('assignment row schema drift')
        key, token = row['variable_key'], row['query_token']
        if (
            type(key) is not str or not key or type(token) is not int
            or not 0 <= token <= 4
        ):
            raise ValueError('assignment row domain drift')
        actual_keys.append(key)
        assignment[key] = token
    if actual_keys != scope_variable_keys or len(assignment) != len(rows):
        raise ValueError('assignment keys must equal factor scope in order')
    return assignment


def _relation_row_non_evidence(
    assignment: dict[str, int],
    contribution: dict[str, Any],
) -> dict[str, Any]:
    contribution = _validate_local_contribution_non_evidence(contribution)
    contribution_bytes = _canonical_json_bytes(contribution)
    return {
        'scope_variable_keys': sorted(assignment),
        'assignment_bytes': _assignment_bytes_non_evidence(assignment),
        'contribution_bytes': contribution_bytes,
        'contribution_sha256': sha256(contribution_bytes).hexdigest(),
    }


def _validate_relation_row_non_evidence(
    row: Any,
    expected_scope: list[str] | None = None,
) -> dict[str, Any]:
    if type(row) is not dict or set(row) != _RELATION_ROW_KEYS:
        raise ValueError('VE relation row schema drift')
    scope = row['scope_variable_keys']
    if (
        type(scope) is not list
        or any(type(key) is not str or not key for key in scope)
        or scope != sorted(set(scope))
    ):
        raise ValueError('relation row scope must be sorted and unique')
    if expected_scope is not None and scope != expected_scope:
        raise ValueError('relation row scope differs from factor scope')
    _decode_assignment_non_evidence(row['assignment_bytes'], scope)
    value = row['contribution_bytes']
    if type(value) is not bytes:
        raise ValueError('contribution bytes required')
    try:
        contribution = json.loads(value.decode('ascii'))
    except Exception as exc:
        raise ValueError('contribution bytes must be canonical JSON') from exc
    if _canonical_json_bytes(contribution) != value:
        raise ValueError('contribution bytes must be canonical JSON')
    _validate_local_contribution_non_evidence(contribution)
    if row['contribution_sha256'] != sha256(value).hexdigest():
        raise ValueError('contribution hash mismatch')
    return deepcopy(row)


def _relation_row_bytes_non_evidence(row: Any) -> bytes:
    row = _validate_relation_row_non_evidence(row)
    # In an enclosing canonical JSON document the byte columns are represented
    # by their canonical ASCII JSON text; the in-memory row retains bytes.
    return _canonical_json_bytes({
        'scope_variable_keys': row['scope_variable_keys'],
        'assignment_bytes': row['assignment_bytes'].decode('ascii'),
        'contribution_bytes': row['contribution_bytes'].decode('ascii'),
        'contribution_sha256': row['contribution_sha256'],
    })


def _relation_factor_non_evidence(
    relation_rows: list[dict[str, Any]],
    scope_variable_keys: list[str] | None = None,
) -> dict[str, Any]:
    if type(relation_rows) is not list:
        raise ValueError('relation rows must be an ordered list')
    if scope_variable_keys is None:
        if not relation_rows:
            raise ValueError('empty factor requires an explicit scope')
        scope_variable_keys = deepcopy(relation_rows[0]['scope_variable_keys'])
    if (
        type(scope_variable_keys) is not list
        or any(type(key) is not str or not key for key in scope_variable_keys)
        or scope_variable_keys != sorted(set(scope_variable_keys))
    ):
        raise ValueError('factor scope must be sorted and unique')
    unique = {}
    for row in relation_rows:
        row = _validate_relation_row_non_evidence(row, scope_variable_keys)
        unique[_relation_row_bytes_non_evidence(row)] = row
    return {
        'schema_version': 'VE_RELATION_FACTOR_V1',
        'scope_variable_keys': list(scope_variable_keys),
        'relation_rows': [unique[key] for key in sorted(unique)],
    }


def _validate_relation_factor_non_evidence(factor: Any) -> dict[str, Any]:
    if type(factor) is not dict or set(factor) != _RELATION_FACTOR_KEYS:
        raise ValueError('VE relation factor schema drift')
    if factor['schema_version'] != 'VE_RELATION_FACTOR_V1':
        raise ValueError('VE relation factor version drift')
    rebuilt = _relation_factor_non_evidence(
        factor['relation_rows'], factor['scope_variable_keys'],
    )
    if (
        [_relation_row_bytes_non_evidence(row) for row in factor['relation_rows']]
        != [_relation_row_bytes_non_evidence(row) for row in rebuilt['relation_rows']]
    ):
        raise ValueError('relation factor rows must be canonical and deduplicated')
    return rebuilt


def _relation_factor_bytes_non_evidence(factor: Any) -> bytes:
    factor = _validate_relation_factor_non_evidence(factor)
    return _canonical_json_bytes({
        'schema_version': 'VE_RELATION_FACTOR_V1',
        'scope_variable_keys': factor['scope_variable_keys'],
        'relation_rows': [
            json.loads(_relation_row_bytes_non_evidence(row).decode('ascii'))
            for row in factor['relation_rows']
        ],
    })


def _relation_factor_sha256_non_evidence(factor: Any) -> str:
    return sha256(_relation_factor_bytes_non_evidence(factor)).hexdigest()


def _relation_factor_from_callable_non_evidence(
    declared_scope: list[str],
    leaf_domains: dict[str, list[int]],
    cell_callable: Any,
) -> dict[str, Any]:
    """Exhaustively reject a callable whose output depends on an omitted leaf."""
    if (
        type(leaf_domains) is not dict or not leaf_domains
        or sorted(set(declared_scope)) != declared_scope
        or any(key not in leaf_domains for key in declared_scope)
    ):
        raise ValueError('declared factor scope/domain drift')
    ordered_keys = sorted(leaf_domains)
    for key in ordered_keys:
        domain = leaf_domains[key]
        if (
            type(key) is not str or not key or type(domain) is not list
            or not domain or domain != sorted(set(domain))
            or any(type(token) is not int or not 0 <= token <= 4 for token in domain)
        ):
            raise ValueError('leaf domain drift')
    outputs = {}
    for values in product(*(leaf_domains[key] for key in ordered_keys)):
        full_assignment = dict(zip(ordered_keys, values))
        contribution = _validate_local_contribution_non_evidence(
            cell_callable(deepcopy(full_assignment))
        )
        declared_assignment = {
            key: full_assignment[key] for key in declared_scope
        }
        assignment_bytes = _assignment_bytes_non_evidence(declared_assignment)
        contribution_bytes = _canonical_json_bytes(contribution)
        previous = outputs.setdefault(assignment_bytes, contribution_bytes)
        if previous != contribution_bytes:
            raise ValueError('undeclared leaf changes factor output')
    return _relation_factor_non_evidence([
        _relation_row_non_evidence(
            {
                row['variable_key']: row['query_token']
                for row in json.loads(assignment_bytes.decode('ascii'))
            },
            json.loads(contribution_bytes.decode('ascii')),
        )
        for assignment_bytes, contribution_bytes in sorted(outputs.items())
    ], declared_scope)


def _join_relation_factors_non_evidence(
    left: Any,
    right: Any,
    *,
    left_factor_sha256: str | None = None,
    right_factor_sha256: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    left = _validate_relation_factor_non_evidence(left)
    right = _validate_relation_factor_non_evidence(right)
    scope = sorted(set(left['scope_variable_keys']) | set(right['scope_variable_keys']))
    left_hash = (
        _relation_factor_sha256_non_evidence(left)
        if left_factor_sha256 is None
        else _hex_digest(left_factor_sha256, 'left factor hash')
    )
    right_hash = (
        _relation_factor_sha256_non_evidence(right)
        if right_factor_sha256 is None
        else _hex_digest(right_factor_sha256, 'right factor hash')
    )
    joined_rows, trace_rows = [], []
    for left_row in left['relation_rows']:
        left_assignment = _decode_assignment_non_evidence(
            left_row['assignment_bytes'], left['scope_variable_keys'],
        )
        for right_row in right['relation_rows']:
            right_assignment = _decode_assignment_non_evidence(
                right_row['assignment_bytes'], right['scope_variable_keys'],
            )
            overlap = set(left_assignment) & set(right_assignment)
            if any(left_assignment[key] != right_assignment[key] for key in overlap):
                continue
            joined_row = _relation_row_non_evidence(
                {**left_assignment, **right_assignment},
                _merge_local_contributions_non_evidence(
                    json.loads(left_row['contribution_bytes'].decode('ascii')),
                    json.loads(right_row['contribution_bytes'].decode('ascii')),
                ),
            )
            joined_rows.append(joined_row)
            left_bytes = _relation_row_bytes_non_evidence(left_row)
            right_bytes = _relation_row_bytes_non_evidence(right_row)
            joined_bytes = _relation_row_bytes_non_evidence(joined_row)
            trace_rows.append({
                'left_factor_sha256': left_hash,
                'right_factor_sha256': right_hash,
                'left_row_bytes': left_bytes,
                'left_row_sha256': sha256(left_bytes).hexdigest(),
                'right_row_bytes': right_bytes,
                'right_row_sha256': sha256(right_bytes).hexdigest(),
                'joined_row_bytes': joined_bytes,
                'joined_row_sha256': sha256(joined_bytes).hexdigest(),
            })
    return _relation_factor_non_evidence(joined_rows, scope), trace_rows


def _eliminate_relation_variable_non_evidence(
    factor: Any,
    variable_key: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    factor = _validate_relation_factor_non_evidence(factor)
    if variable_key not in factor['scope_variable_keys']:
        raise ValueError('eliminated variable must be present in factor scope')
    projected_scope = [
        key for key in factor['scope_variable_keys'] if key != variable_key
    ]
    projected_rows, trace_rows = [], []
    for source_row in factor['relation_rows']:
        assignment = _decode_assignment_non_evidence(
            source_row['assignment_bytes'], factor['scope_variable_keys'],
        )
        del assignment[variable_key]
        projected_row = _relation_row_non_evidence(
            assignment,
            json.loads(source_row['contribution_bytes'].decode('ascii')),
        )
        projected_rows.append(projected_row)
        source_bytes = _relation_row_bytes_non_evidence(source_row)
        projected_bytes = _relation_row_bytes_non_evidence(projected_row)
        trace_rows.append({
            'source_row_bytes': source_bytes,
            'source_row_sha256': sha256(source_bytes).hexdigest(),
            'projected_row_bytes': projected_bytes,
            'projected_row_sha256': sha256(projected_bytes).hexdigest(),
        })
    return _relation_factor_non_evidence(projected_rows, projected_scope), trace_rows


def _min_fill_selection_non_evidence(
    variable_keys: list[str],
    factor_scopes: list[list[str]],
) -> dict[str, Any]:
    if (
        type(variable_keys) is not list or not variable_keys
        or any(type(key) is not str or not key for key in variable_keys)
        or len(set(variable_keys)) != len(variable_keys)
    ):
        raise ValueError('active variable keys must be a nonempty unique list')
    active = set(variable_keys)
    graph = {key: set() for key in active}
    if type(factor_scopes) is not list:
        raise ValueError('factor scopes must be an ordered list')
    for scope in factor_scopes:
        if (
            type(scope) is not list or len(scope) != len(set(scope))
            or any(type(key) is not str or key not in active for key in scope)
        ):
            raise ValueError('factor scope outside active variable graph')
        for left_key, right_key in combinations(scope, 2):
            graph[left_key].add(right_key)
            graph[right_key].add(left_key)
    candidates = []
    for variable_key in active:
        neighbors = sorted(graph[variable_key])
        missing = sum(
            right_key not in graph[left_key]
            for left_key, right_key in combinations(neighbors, 2)
        )
        candidates.append((missing, len(neighbors), variable_key, neighbors))
    missing, degree, variable_key, neighbors = min(candidates)
    return {
        'variable_key': variable_key,
        'selection_key': [missing, degree, variable_key],
        'neighbors': neighbors,
    }


def _eliminate_factor_graph_non_evidence(
    factors: list[dict[str, Any]],
    variable_keys: list[str],
    *,
    factor_sha256s: list[str] | None = None,
) -> dict[str, Any]:
    if type(factors) is not list or not factors:
        raise ValueError('at least one relation factor is required')
    validated_factors = [
        _validate_relation_factor_non_evidence(row) for row in factors
    ]
    if factor_sha256s is None:
        factor_sha256s = [
            _relation_factor_sha256_non_evidence(row)
            for row in validated_factors
        ]
    if (
        type(factor_sha256s) is not list
        or len(factor_sha256s) != len(validated_factors)
    ):
        raise ValueError('input factor hash coverage mismatch')
    current = [
        {
            'factor': factor,
            'sort_sha256': _hex_digest(digest, 'input factor hash'),
        }
        for factor, digest in zip(validated_factors, factor_sha256s)
    ]
    remaining = list(variable_keys)
    if len(set(remaining)) != len(remaining):
        raise ValueError('elimination variable keys must be unique')
    vertices = {
        key for entry in current for key in entry['factor']['scope_variable_keys']
    }
    if vertices != set(remaining):
        raise ValueError('elimination variables must equal factor graph vertices')
    ve_trace_rows = []
    while remaining:
        selection = _min_fill_selection_non_evidence(
            remaining,
            [entry['factor']['scope_variable_keys'] for entry in current],
        )
        variable_key = selection['variable_key']
        incident = [
            entry for entry in current
            if variable_key in entry['factor']['scope_variable_keys']
        ]
        if not incident:
            raise ValueError('isolated elimination variable has no relation factor')
        incident.sort(key=lambda entry: entry['sort_sha256'])
        incident_ids = {id(entry) for entry in incident}
        current = [entry for entry in current if id(entry) not in incident_ids]
        accumulator = incident[0]['factor']
        accumulator_hash = incident[0]['sort_sha256']
        join_trace_rows = []
        for right_entry in incident[1:]:
            accumulator, trace = _join_relation_factors_non_evidence(
                accumulator,
                right_entry['factor'],
                left_factor_sha256=accumulator_hash,
                right_factor_sha256=right_entry['sort_sha256'],
            )
            join_trace_rows.extend(trace)
            accumulator_hash = _relation_factor_sha256_non_evidence(accumulator)
        output, elimination_trace = _eliminate_relation_variable_non_evidence(
            accumulator, variable_key,
        )
        output_bytes = _relation_factor_bytes_non_evidence(output)
        ve_trace_rows.append({
            'step_ordinal': len(ve_trace_rows),
            'eliminated_variable_key': variable_key,
            'selection_key': selection['selection_key'],
            'input_factor_sha256s': [
                entry['sort_sha256'] for entry in incident
            ],
            'join_trace_rows': join_trace_rows,
            'elimination_trace_rows': elimination_trace,
            'output_factor_bytes': output_bytes,
            'output_factor_sha256': sha256(output_bytes).hexdigest(),
        })
        current.append({
            'factor': output,
            'sort_sha256': sha256(output_bytes).hexdigest(),
        })
        remaining.remove(variable_key)
    current.sort(key=lambda entry: entry['sort_sha256'])
    output = current[0]['factor']
    output_hash = current[0]['sort_sha256']
    terminal_join_trace_rows = []
    for right_entry in current[1:]:
        output, trace = _join_relation_factors_non_evidence(
            output,
            right_entry['factor'],
            left_factor_sha256=output_hash,
            right_factor_sha256=right_entry['sort_sha256'],
        )
        terminal_join_trace_rows.extend(trace)
        output_hash = _relation_factor_sha256_non_evidence(output)
    if output['scope_variable_keys']:
        raise AssertionError('variable elimination did not reach empty scope')
    return {
        'schema_version': 'VE_NON_EVIDENCE_RESULT_V1',
        've_trace_rows': ve_trace_rows,
        'terminal_join_trace_rows': terminal_join_trace_rows,
        'output_factor': output,
    }


def _global_state_identity_non_evidence() -> dict[str, Any]:
    return _validate_global_state_non_evidence({
        'schema_version': 'GATE_GLOBAL_STATE_V1',
        **{key: True for key in _LOCAL_ALL_FIELDS},
        **{key: False for key in _LOCAL_SEEN_FIELDS},
        'control_relations': _identity_control_relations_non_evidence(),
    })


def _validate_global_state_non_evidence(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _GLOBAL_KEYS:
        raise ValueError('global gate state schema drift')
    if value['schema_version'] != 'GATE_GLOBAL_STATE_V1':
        raise ValueError('global gate state version drift')
    if any(
        type(value[key]) is not bool
        for key in (*_LOCAL_ALL_FIELDS, *_LOCAL_SEEN_FIELDS)
    ):
        raise ValueError('global gate state flags must be booleans')
    _validate_control_relations_non_evidence(value['control_relations'])
    return deepcopy(value)


def _merge_global_local_non_evidence(
    state: Any,
    local: Any,
) -> dict[str, Any]:
    state = _validate_global_state_non_evidence(state)
    local = _validate_local_contribution_non_evidence(local)
    return _validate_global_state_non_evidence({
        'schema_version': 'GATE_GLOBAL_STATE_V1',
        **{key: state[key] and local[key] for key in _LOCAL_ALL_FIELDS},
        **{key: state[key] or local[key] for key in _LOCAL_SEEN_FIELDS},
        'control_relations': _merge_control_relations_non_evidence(
            state['control_relations'], local['control_relations'],
        ),
    })


def _terminal_ordinary_branch_non_evidence(state: Any) -> int:
    state = _validate_global_state_non_evidence(state)
    conservative_member = all(state[key] for key in (
        'conservative_member_full_all', 'conservative_member_common_all',
        'conservative_member_same_history_all',
        'conservative_canonical_common_all',
        'conservative_canonical_same_history_all',
    ))
    raw_member = all(state[key] for key in (
        'raw_member_full_all', 'raw_member_common_all',
        'raw_member_same_history_all', 'raw_canonical_common_all',
        'raw_canonical_same_history_all',
    ))
    attribution = all(state[key] for key in (
        'source_delete_member_failure_seen', 'source_delete_reduction_all',
        'active_delete_witness_seen', 'local_delete_witness_seen',
        'no_update_evsi_member_failure_seen',
        'no_update_evsi_effect_witness_seen',
        'no_update_passive_member_failure_seen',
        'no_update_passive_effect_witness_seen', 'mask_member_failure_seen',
        'mask_effect_witness_seen', 'postquery_member_failure_seen',
        'postquery_effect_witness_seen', 'sham_lcb_member_failure_seen',
        'sham_raw_member_failure_seen', 'property_separable_all',
        'property_collision_all', 'property_decoy_all',
        'property_balanced_all', 'property_mult6_all',
    ))
    pareto_match = any(
        row['full_no_worse_all'] and row['member_common_no_worse_all']
        and (row['strict_witness_seen'] or row['metric_rationals_equal_all'])
        for row in state['control_relations']
    )
    control_match = pareto_match or not (
        state['consistency_common_advantage_witness_seen']
        and state['consistency_full_no_regression_all']
    )
    return _derive_ordinary_branch({
        'raw_upside': raw_member,
        'raw_bounded_safety': state['raw_bounded_safety_all'],
        'conservative_member_and_forward': conservative_member,
        'conservative_bounded_safety': state['conservative_bounded_safety_all'],
        'conservative_strict_safety': state['conservative_strict_safety_all'],
        'attribution_gate': attribution,
        'control_match': control_match,
    })['ordinary_branch']


def _outer_gate_dp_non_evidence(
    bank_local_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if type(bank_local_rows) is not list or not bank_local_rows:
        raise ValueError('bank local contribution rows required')
    normalized = []
    seen_hashes = set()
    for row in bank_local_rows:
        if type(row) is not dict or set(row) != {
            'canonical_bank_sha256', 'local_contributions',
        }:
            raise ValueError('bank local row schema drift')
        bank_hash = _hex_digest(row['canonical_bank_sha256'], 'bank hash')
        if bank_hash in seen_hashes:
            raise ValueError('duplicate bank local row')
        seen_hashes.add(bank_hash)
        values = row['local_contributions']
        if type(values) is not list or not values:
            raise ValueError('reachable local contributions required')
        unique = {}
        for value in values:
            value = _validate_local_contribution_non_evidence(value)
            if value['canonical_bank_sha256'] != bank_hash:
                raise ValueError('local contribution bank mismatch')
            value_bytes = _canonical_json_bytes(value)
            unique[value_bytes] = value
        normalized.append((bank_hash, [unique[key] for key in sorted(unique)]))
    normalized.sort(key=lambda item: item[0])
    initial = _global_state_identity_non_evidence()
    reach = {_canonical_json_bytes(initial): initial}
    transition_rows = []
    for bank_ordinal, (_, local_values) in enumerate(normalized):
        next_reach = {}
        for from_bytes in sorted(reach):
            from_state = reach[from_bytes]
            for local in local_values:
                local_bytes = _canonical_json_bytes(local)
                to_state = _merge_global_local_non_evidence(from_state, local)
                to_bytes = _canonical_json_bytes(to_state)
                next_reach[to_bytes] = to_state
                transition_rows.append({
                    'bank_ordinal': bank_ordinal,
                    'from_state_bytes': from_bytes,
                    'from_state_sha256': sha256(from_bytes).hexdigest(),
                    'local_contribution_bytes': local_bytes,
                    'local_contribution_sha256': sha256(local_bytes).hexdigest(),
                    'to_state_bytes': to_bytes,
                    'to_state_sha256': sha256(to_bytes).hexdigest(),
                })
        reach = next_reach
    terminal_state_rows = [{
        'state_bytes': state_bytes,
        'state_sha256': sha256(state_bytes).hexdigest(),
        'ordinary_branch': _terminal_ordinary_branch_non_evidence(state),
    } for state_bytes, state in sorted(reach.items())]
    return {
        'schema_version': 'OUTER_GATE_DP_NON_EVIDENCE_V1',
        'initial_state_bytes': _canonical_json_bytes(initial),
        'initial_state_sha256': sha256(_canonical_json_bytes(initial)).hexdigest(),
        'transition_rows': transition_rows,
        'terminal_state_rows': terminal_state_rows,
        'reachable_ordinary_verdicts': sorted({
            row['ordinary_branch'] for row in terminal_state_rows
        }),
    }

_ORDINARY_FACT_KEYS = {
    'raw_upside', 'raw_bounded_safety', 'conservative_member_and_forward',
    'conservative_bounded_safety', 'conservative_strict_safety',
    'attribution_gate', 'control_match',
}


def _derive_ordinary_branch(facts: Any) -> dict[str, Any]:
    if type(facts) is not dict or set(facts) != _ORDINARY_FACT_KEYS:
        raise ValueError('ordinary fact keys drift')
    if any(type(facts[key]) is not bool for key in _ORDINARY_FACT_KEYS):
        raise ValueError('ordinary facts must be booleans')
    if facts['conservative_strict_safety'] and not facts['conservative_bounded_safety']:
        raise ValueError('strict safety implies bounded safety')
    bounded_core = (
        facts['conservative_member_and_forward']
        and facts['conservative_bounded_safety']
    )
    strict_core = (
        facts['conservative_member_and_forward']
        and facts['conservative_strict_safety']
    )
    bounded_joint = bounded_core and facts['attribution_gate']
    strict_joint = strict_core and facts['attribution_gate']
    if strict_core and not bounded_core or strict_joint and not bounded_joint:
        raise ValueError('ordinary core implication drift')
    matches = {
        5: facts['raw_upside'] and not facts['raw_bounded_safety'] and not bounded_core,
        6: facts['raw_upside'] and facts['raw_bounded_safety'] and not bounded_core,
        7: not facts['raw_upside'] and not bounded_core,
        8: bounded_core and not facts['attribution_gate'],
        9: bounded_joint and not strict_core,
        10: strict_joint and facts['control_match'],
        11: strict_joint and not facts['control_match'],
    }
    matching = [branch for branch, matched in matches.items() if matched]
    if len(matching) != 1:
        raise ValueError('ordinary branches must form an exact partition')
    return {
        **facts,
        'bounded_core': bounded_core,
        'strict_core': strict_core,
        'bounded_joint': bounded_joint,
        'strict_joint': strict_joint,
        'ordinary_branch': matching[0],
        'matching_branch_count': len(matching),
    }


def _synthetic_dispatch_truth_table_non_evidence() -> dict[str, Any]:
    rows = []
    ordered_keys = tuple(sorted(_ORDINARY_FACT_KEYS))
    for values in product((False, True), repeat=len(ordered_keys)):
        facts = dict(zip(ordered_keys, values))
        try:
            rows.append(_derive_ordinary_branch(facts))
        except ValueError:
            continue
    if set(row['ordinary_branch'] for row in rows) != set(range(5, 12)):
        raise AssertionError('synthetic ordinary truth table lacks a frozen branch')
    return {
        'schema_version': 'SYNTHETIC_DISPATCH_TRUTH_TABLE_NON_EVIDENCE_V1',
        'evidence_eligible': False,
        'rows': rows,
    }


_GATE_REDUCTION_KEYS = {
    'schema_version', 'execution_plan_sha256', 'variant_ledger_sha256s',
    'prerequisite_packet_sha256', 'coverage_summary', 'metric_extrema',
    'causal_effect_witnesses', 'control_comparison_witnesses',
    'property_witnesses', 'private_truth_leakage', 'instrument_invalid',
    'raw_upside', 'raw_bounded_safety', 'conservative_member_and_forward',
    'conservative_bounded_safety', 'conservative_strict_safety',
    'bounded_core', 'strict_core', 'attribution_gate', 'bounded_joint',
    'strict_joint', 'pareto_match_arm_ids',
    'consistency_positive_non_equivalence', 'control_match',
    'ordinary_branch_by_median', 'median_sensitive', 'query_sensitive',
    'ordinary_branch', 'verdict', 'claim_ceiling',
}
_COVERAGE_SUMMARY_KEYS = {
    'expected_case_count', 'observed_case_count',
    'expected_case_id_digest', 'observed_case_id_digest',
    'first_case_mismatch_ordinal', 'expected_case_id_at_mismatch',
    'observed_case_id_at_mismatch', 'expected_ledger_count',
    'observed_ledger_count', 'missing_variant_ids', 'extra_variant_ids',
    'duplicate_variant_ids',
}
_METRIC_EXTREMA_KEYS = {
    'metric_id','direction','value','arm_id','bank_role_id',
    'canonical_bank_sha256','target_mapping','stratum','variant_id',
}
_CAUSAL_EFFECT_WITNESS_KEYS = {
    'predicate_id','ablation_id','arm_id','bank_role_id',
    'canonical_bank_sha256','target_mapping','metric_id','reference_value',
    'intervened_value','effect_value','threshold','variant_id',
}
_CONTROL_COMPARISON_WITNESS_KEYS = {
    'control_arm_id','comparison_kind','bank_role_id',
    'canonical_bank_sha256','target_mapping','candidate_value',
    'control_value','difference','variant_id',
}
_PROPERTY_WITNESS_KEYS = {
    'property_role_id','witness_id','canonical_bank_sha256','target_mapping',
    'arm_ids','named_rationals','semantic_hashes','variant_id',
}


def _validate_reduction_explanation_rows_non_evidence(reduction: dict[str, Any]) -> None:
    schema_rows = (
        ('metric_extrema', _METRIC_EXTREMA_KEYS),
        ('causal_effect_witnesses', _CAUSAL_EFFECT_WITNESS_KEYS),
        ('control_comparison_witnesses', _CONTROL_COMPARISON_WITNESS_KEYS),
        ('property_witnesses', _PROPERTY_WITNESS_KEYS),
    )
    for name, keys in schema_rows:
        rows = reduction[name]
        if type(rows) is not list or rows != sorted(rows, key=_canonical_json_bytes):
            raise ValueError(f'{name} rows order drift')
        for row in rows:
            if type(row) is not dict or set(row) != keys:
                raise ValueError(f'{name} row schema drift')
            _hex_digest(row['canonical_bank_sha256'], f'{name} bank hash')
            if row['target_mapping'] is not None:
                _validate_mapping(row['target_mapping'])
    for row in reduction['metric_extrema']:
        if row['direction'] not in {'minimum','maximum'}:
            raise ValueError('metric extrema direction drift')
        _decode_rational(row['value'])
    for row in reduction['causal_effect_witnesses']:
        for field in ('reference_value','intervened_value','effect_value','threshold'):
            _decode_rational(row[field])
    for row in reduction['control_comparison_witnesses']:
        for field in ('candidate_value','control_value','difference'):
            _decode_rational(row[field])
    for row in reduction['property_witnesses']:
        if type(row['arm_ids']) is not list or row['arm_ids'] != sorted(set(row['arm_ids'])):
            raise ValueError('property witness arm order drift')
        named = row['named_rationals']
        semantic = row['semantic_hashes']
        if (
            type(named) is not list
            or any(type(item) is not dict or set(item) != {'metric_id','value'} for item in named)
            or type(semantic) is not list
            or any(type(item) is not dict or set(item) != {'receipt_id','sha256'} for item in semantic)
        ):
            raise ValueError('property witness nested schema drift')
        for item in named:
            _decode_rational(item['value'])
        for item in semantic:
            _hex_digest(item['sha256'],'property semantic hash')


def _validate_gate_reduction_shape_non_evidence(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _GATE_REDUCTION_KEYS:
        raise ValueError('gate reduction schema drift')
    if value['schema_version'] != 'GATE_REDUCTION_V1':
        raise ValueError('gate reduction version drift')
    _hex_digest(value['execution_plan_sha256'],'execution plan hash')
    ledger_hashes=value['variant_ledger_sha256s']
    if (
        type(ledger_hashes) is not list or len(ledger_hashes)!=6
        or len(set(ledger_hashes))!=6
    ):
        raise ValueError('exact six unique variant ledger hashes required')
    for digest in ledger_hashes:
        _hex_digest(digest,'variant ledger hash')
    _hex_digest(value['prerequisite_packet_sha256'],'prerequisite packet hash')
    coverage=value['coverage_summary']
    if type(coverage) is not dict or set(coverage)!=_COVERAGE_SUMMARY_KEYS:
        raise ValueError('coverage summary schema drift')
    expected_count=_strict_int(coverage['expected_case_count'],name='expected case count',minimum=0)
    observed_count=_strict_int(coverage['observed_case_count'],name='observed case count',minimum=0)
    expected_digest=_hex_digest(coverage['expected_case_id_digest'],'expected case digest')
    observed_digest=_hex_digest(coverage['observed_case_id_digest'],'observed case digest')
    expected_ledgers=_strict_int(coverage['expected_ledger_count'],name='expected ledger count',minimum=0)
    observed_ledgers=_strict_int(coverage['observed_ledger_count'],name='observed ledger count',minimum=0)
    if expected_ledgers != 6:
        raise ValueError('coverage summary expected ledger count drift')
    variant_lists=[]
    for name in ('missing_variant_ids','extra_variant_ids','duplicate_variant_ids'):
        rows=coverage[name]
        if type(rows) is not list or rows!=sorted(set(rows)) or any(type(row) is not str or not row for row in rows):
            raise ValueError('coverage summary variant ID list drift')
        variant_lists.append(rows)
    mismatch_fields=(
        coverage['first_case_mismatch_ordinal'],
        coverage['expected_case_id_at_mismatch'],
        coverage['observed_case_id_at_mismatch'],
    )
    exact_cases=expected_count==observed_count and expected_digest==observed_digest
    if exact_cases:
        if mismatch_fields != (None,None,None):
            raise ValueError('exact coverage must have null mismatch fields')
    else:
        ordinal=_strict_int(mismatch_fields[0],name='first mismatch ordinal',minimum=0)
        if ordinal > max(expected_count,observed_count):
            raise ValueError('first mismatch ordinal outside stream')
        for digest in mismatch_fields[1:]:
            if digest is not None:
                _hex_digest(digest,'case ID at mismatch')
    exact_ledgers=(observed_ledgers==6 and not any(variant_lists))
    if value['instrument_invalid'] is False and not (exact_cases and exact_ledgers):
        raise ValueError('coverage mismatch requires instrument invalidity')
    _validate_reduction_explanation_rows_non_evidence(value)
    boolean_fields = {
        'private_truth_leakage','instrument_invalid','raw_upside',
        'raw_bounded_safety','conservative_member_and_forward',
        'conservative_bounded_safety','conservative_strict_safety',
        'bounded_core','strict_core','attribution_gate','bounded_joint',
        'strict_joint','consistency_positive_non_equivalence','control_match',
        'median_sensitive','query_sensitive',
    }
    if any(type(value[field]) is not bool for field in boolean_fields):
        raise ValueError('gate reduction predicates must be booleans')
    pareto=value['pareto_match_arm_ids']
    controls=list(_invalidating_control_ids())
    if type(pareto) is not list or pareto!=sorted(set(pareto)) or any(arm not in controls for arm in pareto):
        raise ValueError('Pareto match arm IDs drift')
    expected_control=bool(pareto) or not value['consistency_positive_non_equivalence']
    if value['control_match'] != expected_control:
        raise ValueError('control match recomputation mismatch')
    facts={key:value[key] for key in _ORDINARY_FACT_KEYS}
    ordinary=_derive_ordinary_branch(facts)
    for field in ('bounded_core','strict_core','bounded_joint','strict_joint'):
        if value[field]!=ordinary[field]:
            raise ValueError('ordinary derived core mismatch')
    by_median=value['ordinary_branch_by_median']
    if type(by_median) is not dict or list(by_median)!=['lower','midpoint_integer','upper']:
        raise ValueError('ordinary branch by median schema/order drift')
    for branch in by_median.values():
        _strict_int(branch,name='ordinary branch by median',minimum=5,maximum=11)
    median_sensitive=len(set(by_median.values()))>1
    if value['median_sensitive']!=median_sensitive:
        raise ValueError('median sensitivity recomputation mismatch')
    if value['ordinary_branch']!=ordinary['ordinary_branch'] or value['ordinary_branch']!=by_median['midpoint_integer']:
        raise ValueError('ordinary branch recomputation mismatch')
    if value['claim_ceiling'] != _frozen_design()['claim_ceiling']:
        raise ValueError('gate reduction claim ceiling drift')
    return deepcopy(value)


def _dispatch_gate_reduction_expected_verdict_non_evidence(
    reduction: dict[str, Any],
) -> str:
    if reduction['private_truth_leakage']:
        return 'ACTIVE_TRANSFER_PRIVATE_TRUTH_LEAKAGE'
    if reduction['instrument_invalid']:
        return 'ACTIVE_TRANSFER_INSTRUMENT_INVALID'
    if reduction['median_sensitive']:
        return 'ACTIVE_TRANSFER_MEDIAN_SELECTION_SENSITIVE'
    if reduction['query_sensitive']:
        return 'ACTIVE_TRANSFER_QUERY_TIE_SENSITIVE'
    branch=reduction['ordinary_branch']
    return _frozen_design()['verdict_dispatch'][branch-1]['verdict']


def dispatch_gate_reduction(reduction: dict) -> str:
    """Validate a closed reduction-shaped object and recompute first-true priority.

    This dispatch callable is usable for synthetic branch coverage in I1.  It
    does not make the object evidence and is deliberately separate from the
    fail-closed public evidence reducer.
    """
    validated=_validate_gate_reduction_shape_non_evidence(reduction)
    expected=_dispatch_gate_reduction_expected_verdict_non_evidence(validated)
    if validated['verdict']!=expected:
        raise ValueError('stored verdict mismatch with recomputed dispatch')
    return expected


def reduce_gate_evidence(plan: dict, ledgers: list[dict], packet: dict) -> dict:
    """Expose the I1 evidence boundary and fail closed before result emission."""
    validated_plan=validate_gate_execution_plan(plan)
    ordered_ledgers=_validate_ledger_collection_headers_non_evidence(
        validated_plan, ledgers,
    )
    for ledger in ordered_ledgers:
        validate_gate_variant_ledger(validated_plan, ledger)
    _validate_bounded_prerequisite_packet_prefix_non_evidence(
        validated_plan, packet,
    )
    raise FormalRunNotAuthorized(
        'I2 must bind packet-stream framing, incremental packet hash, finalized '
        'producer/source/dependency hashes, and independent producer path before '
        'GATE_REDUCTION_V1 can be emitted'
    )


def compute_gate_inputs(rows: list[dict]) -> dict[str, Any]:
    raise ValueError(
        'trusted row booleans are forbidden; ledger-bound C3B reduction is required'
    )


def dispatch_verdict(gate_inputs: dict) -> str:
    raise ValueError(
        'stored branches/verdicts are forbidden; ledger-bound C3B reduction is required'
    )


def run_leakage_positive_controls() -> dict[str, Any]:
    bank = build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    valid = _exact_primary_public_payload(bank, history)
    try:
        validate_public_input(valid)
        base_validated = True
    except ValueError:
        base_validated = False

    frozen_classes = list(_frozen_design()['leakage']['forbidden_classes'])
    direct_aliases = [
        'target_mapping',
        'membership_stratum',
        'bank_role',
        'future_outcome',
        'run_id',
        'hidden_cause',
        'private_state',
        'scorer_truth',
        'checkpoint_metric',
        'verdict',
        'artifact_hash',
        'static_oracle',
    ]
    if len(frozen_classes) != 12 or len(direct_aliases) != len(frozen_classes):
        raise ValueError('frozen leakage class registry drift')

    def encoded_probe(index: int) -> tuple[dict[str, Any], str]:
        """Hide a canary in an allowed slot; never rely on alias-name scanning."""
        payload = deepcopy(valid)
        if index == 0:  # target truth disguised as a source permutation
            replacement = next(
                mapping for mapping in mapping_space()
                if mapping not in bank
            )
            payload['source_mappings'][0] = list(replacement)
            canary = 'source_mappings[0]=foreign_legal_permutation'
        elif index == 1:  # stratum/distance disguised as budget
            payload['remaining_budget'] = 0
            canary = 'remaining_budget=semantic_mismatch'
        elif index == 2:  # role disguised as a token ordinal
            payload['initial_token_index'] = 5
            canary = 'initial_token_index=out_of_range_5'
        elif index == 3:  # future outcome disguised as current outcome
            payload['public_history'][0]['prototype_index'] = (
                payload['public_history'][0]['prototype_index'] + 1
            ) % 5
            canary = 'public_history[0].prototype_index=unrecomputed_outcome'
        elif index == 4:  # ID disguised as a count of the correct JSON type family
            payload['query_counts'][0] = True
            canary = 'query_counts[0]=boolean_id_canary'
        elif index == 5:  # cause disguised as a legal-shaped prototype vector
            payload['prototype_table'][0]['vector_micro'][0] += 1
            canary = 'prototype_table[0].vector_micro[0]=nonfrozen_value'
        elif index == 6:  # private state disguised inside a closed state vector
            counts = payload['learner_state']['consistency_counts']
            positive = next(i for i, value in enumerate(counts) if value > 0)
            zero = next(i for i, value in enumerate(counts) if value == 0)
            counts[positive] -= 1
            counts[zero] += 1
            canary = 'learner_state.consistency_counts=plausible_private_mutation'
        elif index == 7:  # scorer/future truth encoded as an outcome range violation
            payload['public_history'][0]['prototype_index'] = -1
            canary = 'public_history[0].prototype_index=negative_truth_canary'
        elif index == 8:  # checkpoint metric encoded in a rational weight
            payload['learner_state']['effective_mapping_weights'][0]['n'] += 1
            canary = 'learner_state.effective_mapping_weights[0]=metric_canary'
        elif index == 9:  # verdict encoded as a schema-version substitution
            payload['schema_version'] = 'ego.v2.active_transfer.public_input.v0'
            canary = 'schema_version=verdict_canary_version'
        elif index == 10:  # artifact position encoded as an ordinal
            payload['public_history'][0]['ordinal'] = 1
            canary = 'public_history[0].ordinal=artifact_position_canary'
        elif index == 11:  # oracle output encoded in a phase-inconsistent state slot
            payload['learner_state']['selected_second_token'] = 4
            canary = 'learner_state.selected_second_token=H1_oracle_canary'
        else:
            raise AssertionError('unreachable leakage control index')
        return payload, canary

    receipts = []
    for index, (forbidden_class, alias) in enumerate(zip(frozen_classes, direct_aliases)):
        direct = deepcopy(valid)
        direct[alias] = {'canary': index}
        direct_rejected = False
        direct_error = None
        try:
            validate_public_input(direct)
        except ValueError as exc:
            direct_rejected = True
            direct_error = str(exc)

        encoded, encoded_canary = encoded_probe(index)
        encoded_rejected = False
        encoded_error = None
        try:
            validate_public_input(encoded)
        except ValueError as exc:
            encoded_rejected = True
            encoded_error = str(exc)
        receipts.append({
            'forbidden_class': forbidden_class,
            'direct_alias': alias,
            'direct_rejected': direct_rejected,
            'direct_error': direct_error,
            'encoded_canary': encoded_canary,
            'encoded_rejected': encoded_rejected,
            'encoded_error': encoded_error,
        })

    direct_rejected_count = sum(row['direct_rejected'] for row in receipts)
    encoded_rejected_count = sum(row['encoded_rejected'] for row in receipts)
    rejected = direct_rejected_count + encoded_rejected_count
    passed = (
        base_validated
        and direct_rejected_count == len(frozen_classes)
        and encoded_rejected_count == len(frozen_classes)
    )
    return {
        'passed': passed,
        'base_validated': base_validated,
        'forbidden_class_count': len(frozen_classes),
        'direct_case_count': len(frozen_classes),
        'encoded_case_count': len(frozen_classes),
        'direct_rejected_count': direct_rejected_count,
        'encoded_rejected_count': encoded_rejected_count,
        'rejected_case_count': rejected,
        'receipts': receipts,
    }


def build_development_report(*, exhaustive: bool) -> dict[str, Any]:
    if exhaustive:
        raise FormalRunNotAuthorized('formal exhaustive run is forbidden in I1')
    design = _frozen_design()
    registry = validate_frozen_registry(design)
    property_banks = scan_property_banks()
    leakage = run_leakage_positive_controls()
    receipts = validate_authority_hashes()
    return {
        'task_id': TASK_ID,
        'formal_run_authorized': False,
        'authority_receipts': receipts,
        'registry_summary': registry,
        'property_roles': sorted(property_banks),
        'leakage_positive_controls': leakage,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    active_argv = list(sys.argv[1:] if argv is None else argv)
    extras = set(active_argv) - {'--self-check'}
    if extras & FORMAL_ONLY_FLAGS:
        raise SystemExit('formal or artifact flags are not authorized in I1')
    if not args.self_check:
        raise SystemExit('I1 only supports --self-check')
    print(json.dumps(build_development_report(exhaustive=False), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
