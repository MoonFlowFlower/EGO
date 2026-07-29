from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / 'scripts' / 'codex' / 'check_ego_v2_active_transfer_headroom_preflight_001d.py'
CARD = REPO_ROOT / 'docs' / 'codex' / 'tasks' / 'EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1.md'
DESIGN = REPO_ROOT / 'docs' / 'codex' / 'tasks' / 'ego-v2-p1-active-transfer-headroom-preflight-001d' / 'FROZEN_DESIGN.json'
TASK_ID = 'EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D'


def _load_module():
    if not SCRIPT.exists():
        raise AssertionError(f'missing producer module: {SCRIPT}')
    spec = importlib.util.spec_from_file_location('active_transfer_headroom_001d', SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError('could not load 001D producer')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_authority_registry_formal_refusal() -> None:
    module = _load_module()
    design = module.load_frozen_design()
    receipts = module.authority_receipts()
    assert [row['path'] for row in receipts] == [
        'docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D.md',
        'docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/COLLISION_RECORD.md',
        'docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json',
    ]
    assert receipts[2]['sha256'] == hashlib.sha256(DESIGN.read_bytes()).hexdigest()
    summary = module.validate_frozen_registry(design)
    assert summary['primary_role_count'] == 75
    assert summary['property_role_count'] == 4
    assert summary['arm_count'] == 45
    assert summary['ablation_count'] == 13
    assert summary['verdict_count'] == 11
    with pytest.raises(module.FormalRunNotAuthorized):
        module.build_development_report(exhaustive=True)
    parser = module.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['--output-dir', 'tmp'])


def test_mapping_bank_property_determinism() -> None:
    module = _load_module()
    mappings = module.mapping_space()
    assert len(mappings) == 120
    assert mappings[0] == (0, 1, 2, 3, 4)
    assert mappings[-1] == (4, 3, 2, 1, 0)
    assert module.canonical_mapping_bytes(mappings[0]) == b'[0,1,2,3,4]'
    hash_bank = module.build_hash_bank(0)
    assert len(hash_bank) == 6
    assert hash_bank == tuple(sorted(hash_bank))
    mult_bank = module.build_multiplicity_bank((3, 2, 1))
    assert len(mult_bank) == 6
    assert len(set(mult_bank)) == 3
    assert module.source_counts(mult_bank)[module.mapping_space().index(mult_bank[0])] == 3
    scanned = module.scan_property_banks()
    assert set(scanned) == {'B_SEPARABLE', 'B_COLLISION', 'B_DECOY', 'B_BALANCED_MARGINAL'}
    assert scanned['B_BALANCED_MARGINAL']['first_index'] >= 0
    assert scanned['B_BALANCED_MARGINAL']['witness']['ordered_pair_a'] != scanned['B_BALANCED_MARGINAL']['witness']['ordered_pair_b']


def test_schema_state_history_construction() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    validated = module.validate_public_input(_canonical_public_payload(
        module,
        bank,
        history,
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
    ))
    assert validated['public_history'] == ((0, 0, bank[0][0]),)
    state = module.build_state('ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK', bank, history, median_convention='midpoint_integer')
    assert module.validate_state(state)['stage'] == 'H1'
    assert len(state['effective_mapping_weights']) == 120
    h2 = history + [{'token_index': 1, 'prototype_index': bank[0][1]}]
    no_update = module.build_state('ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK', bank, h2, median_convention='midpoint_integer')
    masked = module.build_state('ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK', bank, h2, median_convention='midpoint_integer')
    assert no_update['stage'] == 'H2'
    assert masked['incoming_family_contributions'] == masked['sealed_family_contributions']


def test_median_lcb_evsi_eig_entropy_decisions() -> None:
    module = _load_module()
    lower, midpoint, upper = module.weighted_median_endpoints([0, 2], [1, 1])
    assert (lower, midpoint, upper) == (0, 1, 2)
    assert module.round_half_even_fraction(1, 2) == 0
    assert module.round_half_even_fraction(3, 2) == 2
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    query = module.query_decision('ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK', bank, history, median_convention='midpoint_integer')
    assert query['selected_token'] in query['eligible_tokens']
    eig = module.query_decision('ARM_I_TRANSFER__A_EIG__D_LCB05_FALLBACK', bank, history, median_convention='midpoint_integer')
    entropy = module.query_decision('ARM_I_TRANSFER__A_MAX_OUTCOME_ENTROPY__D_LCB05_FALLBACK', bank, history, median_convention='midpoint_integer')
    assert eig['exact_scores'] == entropy['exact_scores']
    h2 = history + [{'token_index': query['selected_token'], 'prototype_index': bank[0][query['selected_token']]}]
    decision = module.prediction_decision('ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK', bank, h2, median_convention='midpoint_integer')
    assert decision['schema_version'] == 'PREDICTION_DECISION_V1'
    assert len(decision['used_transfer']) == 5
    assert all(type(value) is bool for value in decision['used_transfer'])


def test_arm_target_metric_baseline_decomposition() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    row = module.evaluate_target(bank, target, 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK', median_convention='midpoint_integer')
    assert row['arm_id'] == 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    assert row['target_mapping'] == list(target)
    assert row['metric_denominators'] == {
        'full': 20, 'own_unqueried': 12, 'common_unqueried': 8,
        'same_history_forward': 12,
    }
    assert row['full_improvement_raw'] == row['common_raw'] + row['query_asymmetry_raw']
    scratch = module.evaluate_target(bank, target, 'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1', median_convention='midpoint_integer')
    assert scratch['used_transfer'] == [False, False, False, False, False]
    classifications = [module.classify_target(bank, mapping) for mapping in module.mapping_space()]
    assert len(classifications) == 120
    assert all(row['distance'] != 1 for row in classifications)


def test_ablation_invariant_leakage_amortized_lookup() -> None:
    module = _load_module()
    leakage = module.run_leakage_positive_controls()
    assert leakage['passed'] is True
    assert leakage['rejected_case_count'] > 0
    bank = module.build_hash_bank(0)
    report = module.build_amortized_lookup({'HASH_00': bank})
    assert report['builder_id'] == 'CANDIDATE_RULE_AMORTIZED_LOOKUP'
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    payload = _canonical_public_payload(
        module, bank, history,
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
    )
    lookup = module.lookup_query_or_prediction(report, payload)
    assert lookup == module.query_decision(
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        history,
        median_convention='midpoint_integer',
    )


def test_gate_verdict_replay_self_check() -> None:
    module = _load_module()
    with pytest.raises(ValueError, match='ledger-bound C3B'):
        module.compute_gate_inputs([{'bounded_core': False, 'raw_upside': False}])
    with pytest.raises(ValueError, match='ledger-bound C3B'):
        module.dispatch_verdict({'ordinary_branch': 7})
    self_check = module.build_development_report(exhaustive=False)
    assert self_check['task_id'] == TASK_ID
    cli = _run_cli('--self-check')
    assert cli.returncode == 0, cli.stderr
    payload = json.loads(cli.stdout)
    assert payload['task_id'] == TASK_ID
    assert payload['formal_run_authorized'] is False


def test_fix_round1_authority_argv_and_closed_state_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    receipts = module.authority_receipts()
    assert receipts[0]['expected_sha256'] == 'c9a7d71dcd92b0bc4571a4e5aa975e04fc97485d47b23b826894f13cac96072e'
    assert receipts[1]['expected_sha256'] == '75e870cd638e58949e48ff0a3ea42101d71279196905cc461b1aa996762a0ae1'
    assert receipts[2]['expected_sha256'] == 'f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916'
    assert all(row['matches_expected'] is True for row in receipts)

    tampered = [dict(row) for row in receipts]
    tampered[0]['sha256'] = '0' * 64
    monkeypatch.setattr(module, 'authority_receipts', lambda: tampered)
    with pytest.raises(ValueError, match='authority hash drift'):
        module.build_development_report(exhaustive=False)
    monkeypatch.setattr(module, 'authority_receipts', lambda: receipts)

    bank = module.build_hash_bank(0)
    state = module.build_state(
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        [{'token_index': 0, 'prototype_index': bank[0][0]}],
        median_convention='midpoint_integer',
    )
    assert 'median_convention' not in state
    tampered_state = dict(state)
    tampered_state['effective_mapping_weights'] = [{'n': 0, 'd': 1} for _ in range(120)]
    with pytest.raises(ValueError, match='state semantic drift'):
        module.validate_state(tampered_state)

    monkeypatch.setattr(sys, 'argv', ['prog', '--formal'])
    assert module.main(['--self-check']) == 0


def _canonical_public_payload(module, bank, history, arm_id):
    state = module.build_state(arm_id, bank, history, median_convention='midpoint_integer')
    counts = [0] * 5
    for row in history:
        counts[row['token_index']] += 1
    return {
        'schema_version': 'ego.v2.active_transfer.public_input.v1',
        'prototype_table': [
            {'prototype_index': index, 'vector_micro': list(vector)}
            for index, vector in enumerate(module.load_frozen_design()['public_grammar']['prototype_vectors_micro'])
        ],
        'source_mappings': [list(row) for row in reversed(bank)],
        'initial_token_index': history[0]['token_index'],
        'public_history': [
            {'ordinal': ordinal, 'token_index': row['token_index'], 'prototype_index': row['prototype_index']}
            for ordinal, row in enumerate(history)
        ],
        'query_counts': counts,
        'remaining_budget': 2 - len(history),
        'learner_state': state,
    }


def _rational_ints(rows):
    return tuple(row['n'] // row['d'] for row in rows)


def test_fix_round2a_exact_sha_ranked_banks_and_duplicate_local_counts() -> None:
    module = _load_module()
    assert module.build_hash_bank(0) == (
        (0, 3, 1, 4, 2),
        (0, 3, 2, 4, 1),
        (1, 2, 3, 4, 0),
        (1, 2, 4, 3, 0),
        (1, 3, 4, 0, 2),
        (2, 1, 0, 3, 4),
    )
    assert module.build_hash_bank(1) == (
        (1, 2, 4, 0, 3),
        (3, 1, 0, 4, 2),
        (3, 4, 2, 1, 0),
        (4, 1, 2, 0, 3),
        (4, 2, 0, 3, 1),
        (4, 3, 0, 2, 1),
    )
    mult = module.build_multiplicity_bank((3, 2, 1))
    assert mult == (
        (2, 0, 4, 1, 3),
        (2, 0, 4, 1, 3),
        (2, 0, 4, 1, 3),
        (2, 4, 3, 0, 1),
        (3, 2, 0, 4, 1),
        (3, 2, 0, 4, 1),
    )

    repeated = module.build_multiplicity_bank((6,))
    source = repeated[0]
    local = module.local_counts(repeated)
    for i in range(5):
        for j in range(i + 1, 5):
            neighbor = list(source)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            assert local[module.mapping_space().index(tuple(neighbor))] == 6
    assert sum(local) == 60


def test_fix_round2a_exact_property_predicates_witnesses_and_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    scanned = module.scan_property_banks()
    assert {role: row['first_index'] for role, row in scanned.items()} == {
        'B_SEPARABLE': 0,
        'B_COLLISION': 48,
        'B_DECOY': 0,
        'B_BALANCED_MARGINAL': 4626,
    }
    for row in scanned.values():
        bank = tuple(tuple(mapping) for mapping in row['bank'])
        assert row['canonical_bank_bytes'] == module.canonical_bank_bytes(bank).decode('ascii')
        assert row['canonical_bank_sha256'] == hashlib.sha256(module.canonical_bank_bytes(bank)).hexdigest()
    assert scanned['B_SEPARABLE']['witness']['policy'] == [2, 3, 1, -1, -1]
    assert scanned['B_DECOY']['witness']['h1_outcome'] == 4
    assert scanned['B_DECOY']['witness']['eig_query'] != scanned['B_DECOY']['witness']['evsi_query']
    assert len(scanned['B_COLLISION']['witness']['policy_witnesses']) > 0
    assert scanned['B_BALANCED_MARGINAL']['witness']['h1_outcome'] >= 0

    histogram_only_near_miss = (
        (0, 1, 2, 3, 4),
        (0, 2, 3, 4, 1),
        (1, 0, 2, 4, 3),
        (2, 0, 1, 4, 3),
        (3, 0, 1, 2, 4),
        (4, 0, 1, 2, 3),
    )
    assert module._balanced_marginal_witness(histogram_only_near_miss) is None
    assert module._collision_witnesses(module.build_hash_bank(0)) is None

    monkeypatch.setattr(module, 'build_hash_bank', lambda index: module.mapping_space()[:6])
    with pytest.raises(ValueError, match='property bank scan incomplete'):
        module._scan_property_banks(scan_stop=3)


def test_fix_round2a_closed_public_schema_and_nested_forbidden_aliases() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    arm = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    payload = _canonical_public_payload(module, bank, history, arm)
    validated = module.validate_public_input(payload)
    assert validated['source_mappings'] == tuple(sorted(bank))
    assert validated['public_history'] == ((0, 0, bank[0][0]),)

    mutations = []
    extra = dict(payload)
    extra['target_mapping'] = [0, 1, 2, 3, 4]
    mutations.append(extra)
    nested = json.loads(json.dumps(payload))
    nested['prototype_table'][0]['vector_micro'] = {'artifact_hash': 'encoded'}
    mutations.append(nested)
    wrong_counts = json.loads(json.dumps(payload))
    wrong_counts['query_counts'] = [0, 0, 0, 0, 0]
    mutations.append(wrong_counts)
    wrong_history = json.loads(json.dumps(payload))
    wrong_history['public_history'][0]['ordinal'] = 1
    mutations.append(wrong_history)
    open_state = json.loads(json.dumps(payload))
    open_state['learner_state']['metadata'] = {'verdict': 'pass'}
    mutations.append(open_state)
    semantic_state = json.loads(json.dumps(payload))
    semantic_state['learner_state']['effective_mapping_weights'][0] = {'n': 2, 'd': 2}
    mutations.append(semantic_state)
    for mutation in mutations:
        with pytest.raises(ValueError):
            module.validate_public_input(mutation)


def test_fix_round2a_exact_rational_state_and_all_inference_transitions() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    source_mapping = bank[0]
    h1 = [{'token_index': 0, 'prototype_index': source_mapping[0]}]
    h2 = h1 + [{'token_index': 1, 'prototype_index': source_mapping[1]}]
    arm_ids = {
        'transfer': 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        'scratch': 'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1',
        'consistency': 'ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN',
        'no_update': 'ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK',
        'mask': 'ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK',
        'then_scratch': 'ARM_I_TRANSFER_THEN_SCRATCH__A_L1_EVSI__D_SCRATCH_L1',
        'no_local': 'ARM_I_TRANSFER_NO_LOCAL__A_L1_EVSI__D_LCB05_FALLBACK',
        'flat': 'ARM_I_TRANSFER_FLAT__A_L1_EVSI__D_LCB05_FALLBACK',
        'sham': 'ARM_I_SHAM__A_L1_EVSI__D_LCB05_FALLBACK',
    }
    states_h1 = {name: module.build_state(arm, bank, h1, median_convention='midpoint_integer') for name, arm in arm_ids.items()}
    states_h2 = {name: module.build_state(arm, bank, h2, median_convention='midpoint_integer') for name, arm in arm_ids.items()}
    for state in [*states_h1.values(), *states_h2.values()]:
        assert module.validate_state(state) == state
        for family in ('scratch', 'source', 'local'):
            assert all(set(row) == {'n', 'd'} and row['d'] == 1 for row in state['incoming_family_contributions'][family])
        sealed_sum = tuple(
            sum(state['sealed_family_contributions'][family][i]['n'] for family in ('scratch', 'source', 'local'))
            for i in range(120)
        )
        assert sealed_sum == _rational_ints(state['effective_mapping_weights'])

    for name in ('transfer', 'scratch', 'consistency', 'no_local', 'flat', 'sham'):
        assert states_h2[name]['incoming_family_contributions'] == states_h1[name]['sealed_family_contributions']
    assert states_h1['no_update']['incoming_family_contributions'] == states_h1['no_update']['sealed_family_contributions']
    assert states_h2['no_update']['incoming_family_contributions'] == states_h1['no_update']['incoming_family_contributions']
    assert states_h2['no_update']['sealed_family_contributions'] == states_h1['no_update']['incoming_family_contributions']
    assert states_h2['mask']['incoming_family_contributions'] == states_h1['mask']['sealed_family_contributions']
    assert states_h2['mask']['sealed_family_contributions'] == states_h1['mask']['sealed_family_contributions']
    assert sum(_rational_ints(states_h2['then_scratch']['incoming_family_contributions']['scratch'])) == 24
    assert sum(_rational_ints(states_h2['then_scratch']['sealed_family_contributions']['scratch'])) == 6
    assert all(row == {'n': 0, 'd': 1} for row in states_h2['no_local']['sealed_family_contributions']['local'])

    expected_consistency = tuple(
        count if mapping[0] == source_mapping[0] and mapping[1] == source_mapping[1] else 0
        for mapping, count in zip(module.mapping_space(), module.source_counts(bank))
    )
    assert tuple(states_h2['consistency']['consistency_counts']) == expected_consistency

    impossible_h2 = h1 + [{'token_index': 1, 'prototype_index': next(
        p for p in range(5)
        if p != source_mapping[0] and all(m[1] != p for m in bank if m[0] == source_mapping[0])
    )}]
    fallback = module.build_state(arm_ids['consistency'], bank, impossible_h2, median_convention='midpoint_integer')
    assert sum(_rational_ints(fallback['sealed_family_contributions']['source'])) == 0
    assert sum(_rational_ints(fallback['sealed_family_contributions']['scratch'])) > 0

    repeated = module.build_multiplicity_bank((6,))
    repeated_h1 = [{'token_index': 0, 'prototype_index': repeated[0][0]}]
    ordinary = module.build_state(arm_ids['transfer'], repeated, repeated_h1, median_convention='midpoint_integer')
    flat = module.build_state(arm_ids['flat'], repeated, repeated_h1, median_convention='midpoint_integer')
    for key in ('incoming_family_contributions', 'sealed_family_contributions', 'effective_mapping_weights', 'consistency_counts'):
        assert ordinary[key] == flat[key]


def test_fix_round2a_r1_frozen_public_domain_and_non_tautological_leakage_controls() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    arm = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    payload = _canonical_public_payload(module, bank, history, arm)
    assert module.validate_public_input(payload)['prototype_table'] == tuple(
        (index, tuple(vector))
        for index, vector in enumerate(module.load_frozen_design()['public_grammar']['prototype_vectors_micro'])
    )

    arbitrary_table = json.loads(json.dumps(payload))
    arbitrary_table['prototype_table'][0]['vector_micro'] = [31001, 31002, 31003, 31004]
    with pytest.raises(ValueError, match='prototype table semantic drift'):
        module.validate_public_input(arbitrary_table)

    assert len(module.build_hash_bank(65535)) == 6
    with pytest.raises(ValueError, match='hash-bank index above range'):
        module.build_hash_bank(65536)
    for invalid_partition in ((1, 5), (2, 4), (1, 2, 3)):
        with pytest.raises(ValueError, match='frozen multiplicity partition'):
            module.build_multiplicity_bank(invalid_partition)

    leakage = module.run_leakage_positive_controls()
    assert leakage['base_validated'] is True
    assert leakage['direct_case_count'] >= len(module.load_frozen_design()['leakage']['forbidden_classes'])
    assert leakage['encoded_case_count'] >= len(module.load_frozen_design()['leakage']['forbidden_classes'])
    assert leakage['rejected_case_count'] == leakage['direct_case_count'] + leakage['encoded_case_count']
    assert leakage['passed'] is True


def test_fix_round2a_r1_state_bound_checks_and_contextual_recomputation() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    arm = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    payload = _canonical_public_payload(module, bank, history, arm)

    impossible_counts = json.loads(json.dumps(payload['learner_state']))
    impossible_counts['consistency_counts'][0] = 7
    with pytest.raises(ValueError, match='consistency count bound drift'):
        module.validate_state(impossible_counts)

    plausible_but_wrong = json.loads(json.dumps(payload))
    counts = plausible_but_wrong['learner_state']['consistency_counts']
    positive = next(index for index, value in enumerate(counts) if value > 0)
    zero = next(index for index, value in enumerate(counts) if value == 0)
    counts[positive] -= 1
    counts[zero] += 1
    assert module.validate_state(plausible_but_wrong['learner_state']) == plausible_but_wrong['learner_state']
    with pytest.raises(ValueError, match='state semantic drift'):
        module.validate_public_input(plausible_but_wrong)


def _independent_evsi_scores(module, arm_id, bank, history, median_convention='midpoint_integer'):
    initial = history[0]['token_index']
    h1_weights = _rational_ints(module.build_state(
        arm_id, bank, history, median_convention=median_convention,
    )['effective_mapping_weights'])
    scores = {}
    for query in range(5):
        if query == initial:
            continue
        score = 0
        for outcome in range(5):
            if not any(
                weight > 0 and mapping[query] == outcome
                for mapping, weight in zip(module.mapping_space(), h1_weights)
            ):
                continue
            h2 = history + [{'token_index': query, 'prototype_index': outcome}]
            decision = module.prediction_decision(
                arm_id, bank, h2, median_convention=median_convention,
            )
            for mapping, weight in zip(module.mapping_space(), h1_weights):
                if weight <= 0 or mapping[query] != outcome:
                    continue
                for token in range(5):
                    if token in {initial, query}:
                        continue
                    score += weight * module._l1(
                        decision['prediction_micro'][token],
                        module._prototype_table()[mapping[token]],
                    )
        scores[query] = score
    return scores


def _independent_token_lcb(module, transfer_weights, transfer_row, scratch_row, token):
    weighted = []
    for mapping, weight in zip(module.mapping_space(), transfer_weights):
        if weight <= 0:
            continue
        truth = module._prototype_table()[mapping[token]]
        benefit = module._l1(scratch_row, truth) - module._l1(transfer_row, truth)
        weighted.append((benefit, weight))
    total = sum(weight for _, weight in weighted)
    cumulative = 0
    for benefit, weight in sorted(weighted):
        cumulative += weight
        if 20 * cumulative >= total:
            return benefit
    raise AssertionError('empty transfer posterior')


def test_fix_round2b_public_payload_is_in_live_decision_chain_and_initial_is_not_hardcoded(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    initial = 3
    history = [{'token_index': initial, 'prototype_index': bank[0][initial]}]
    calls = []
    original = module.validate_public_input

    def recording_validator(payload):
        calls.append(payload)
        return original(payload)

    monkeypatch.setattr(module, 'validate_public_input', recording_validator)
    query = module.query_decision(
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        history,
        median_convention='midpoint_integer',
    )
    assert calls and all(payload['initial_token_index'] == initial for payload in calls)
    assert initial not in query['eligible_tokens']
    assert query['selected_token'] == min(_independent_evsi_scores(
        module,
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        history,
    ), key=lambda token: (_independent_evsi_scores(
        module,
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        history,
    )[token], token))

    h2 = history + [{'token_index': query['selected_token'], 'prototype_index': bank[0][query['selected_token']]}]
    calls.clear()
    module.prediction_decision(
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        bank,
        h2,
        median_convention='midpoint_integer',
    )
    assert len(calls) >= 1
    assert calls[0]['public_history'][0]['token_index'] == initial


def test_fix_round2b_exact_weighted_medians_and_negative_half_even() -> None:
    module = _load_module()
    assert module.round_half_even_fraction(-1, 2) == 0
    assert module.round_half_even_fraction(-3, 2) == -2
    assert module.round_half_even_fraction(-5, 2) == -2
    assert module.round_half_even_fraction(-7, 2) == -4
    assert module.weighted_median_endpoints([-5, -1], [1, 1]) == (-5, -3, -1)
    assert module.weighted_median_endpoints([-4, -1], [1, 1]) == (-4, -2, -1)
    assert module.weighted_median_endpoints([7, 1, 7, 3], [1, 2, 3, 2]) == (3, 5, 7)
    with pytest.raises(ValueError):
        module.weighted_median_endpoints([], [])
    with pytest.raises(ValueError):
        module.weighted_median_endpoints([0], [0])
    with pytest.raises(ValueError):
        module.weighted_median_endpoints([0, 1], [1])

    values, weights = [-5, -1], [1, 1]
    endpoints = module.weighted_median_endpoints(values, weights)
    risks = [sum(weight * abs(value - action) for value, weight in zip(values, weights)) for action in endpoints]
    assert risks == [4, 4, 4]


def test_fix_round2b_lcb05_is_per_token_and_comparators_follow_inference() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    mapping = bank[0]
    h1 = [{'token_index': 0, 'prototype_index': mapping[0]}]
    h2 = h1 + [{'token_index': 2, 'prototype_index': mapping[2]}]
    arm = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    decision = module.prediction_decision(arm, bank, h2, median_convention='midpoint_integer')
    assert set(decision) == {
        'schema_version', 'arm_id', 'prediction_micro', 'median_endpoints_micro',
        'used_transfer', 'lcb05_benefit_micro',
    }
    assert len(decision['prediction_micro']) == 5
    assert all(len(row) == 4 for row in decision['prediction_micro'])
    assert len(decision['median_endpoints_micro']) == 5
    assert all(len(row) == 4 and all(len(pair) == 2 for pair in row) for row in decision['median_endpoints_micro'])
    assert len(decision['used_transfer']) == 5
    assert len(decision['lcb05_benefit_micro']) == 5
    assert decision['used_transfer'][0] is False and decision['used_transfer'][2] is False
    assert decision['lcb05_benefit_micro'][0] is None and decision['lcb05_benefit_micro'][2] is None
    assert decision['prediction_micro'][0] == list(module._prototype_table()[mapping[0]])
    assert decision['prediction_micro'][2] == list(module._prototype_table()[mapping[2]])

    transfer_weights = _rational_ints(module.build_state(
        arm, bank, h2, median_convention='midpoint_integer',
    )['effective_mapping_weights'])
    scratch_weights = _rational_ints(module.build_state(
        'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1', bank, h2,
        median_convention='midpoint_integer',
    )['effective_mapping_weights'])
    for token in (1, 3, 4):
        transfer_row, _ = module._weighted_prediction(transfer_weights, token, 'midpoint_integer')
        scratch_row, _ = module._weighted_prediction(scratch_weights, token, 'midpoint_integer')
        exact_lcb = _independent_token_lcb(module, transfer_weights, transfer_row, scratch_row, token)
        assert decision['lcb05_benefit_micro'][token] == exact_lcb
        assert decision['used_transfer'][token] is (exact_lcb >= 0)
        assert decision['prediction_micro'][token] == list(transfer_row if exact_lcb >= 0 else scratch_row)

    no_update = 'ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK'
    no_update_h1 = module.prediction_decision(no_update, bank, h1, median_convention='midpoint_integer')
    no_update_h2 = module.prediction_decision(no_update, bank, h2, median_convention='midpoint_integer')
    for token in (1, 3, 4):
        assert no_update_h2['lcb05_benefit_micro'][token] == no_update_h1['lcb05_benefit_micro'][token]

    masked = 'ARM_I_TRANSFER_MASK_H2__A_L1_EVSI__D_LCB05_FALLBACK'
    masked_h1 = module.prediction_decision(masked, bank, h1, median_convention='midpoint_integer')
    masked_h2 = module.prediction_decision(masked, bank, h2, median_convention='midpoint_integer')
    for token in (1, 3, 4):
        assert masked_h2['lcb05_benefit_micro'][token] == masked_h1['lcb05_benefit_micro'][token]


def test_fix_round2b_evsi_exact_h1_primitive_weight_once_and_hash00_counterexample() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    arm = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    independent = _independent_evsi_scores(module, arm, bank, history)
    decision = module.query_decision(arm, bank, history, median_convention='midpoint_integer')
    assert {row['token_index']: row['int_score'] for row in decision['exact_scores']} == independent
    expected_minimizers = [token for token, value in independent.items() if value == min(independent.values())]
    assert decision['minimizing_tokens'] == expected_minimizers
    assert decision['selected_token'] == min(expected_minimizers)
    assert decision['selected_token'] != 1


def test_fix_round2b_eig_entropy_are_independent_callables_and_exact_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = [{'token_index': 0, 'prototype_index': bank[0][0]}]
    eig_arm = 'ARM_I_TRANSFER__A_EIG__D_LCB05_FALLBACK'
    entropy_arm = 'ARM_I_TRANSFER__A_MAX_OUTCOME_ENTROPY__D_LCB05_FALLBACK'
    eig = module.query_decision(eig_arm, bank, history, median_convention='midpoint_integer')
    entropy = module.query_decision(entropy_arm, bank, history, median_convention='midpoint_integer')
    assert eig['exact_scores'] == entropy['exact_scores']
    assert eig['minimizing_tokens'] == entropy['minimizing_tokens']
    assert eig['selected_token'] == entropy['selected_token']

    original_eig = module._eig_acquisition_scores
    monkeypatch.setattr(module, '_eig_acquisition_scores', lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('EIG alias used')))
    assert module.query_decision(entropy_arm, bank, history, median_convention='midpoint_integer')['exact_scores'] == entropy['exact_scores']
    monkeypatch.setattr(module, '_eig_acquisition_scores', original_eig)
    monkeypatch.setattr(module, '_max_outcome_entropy_scores', lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('entropy alias used')))
    assert module.query_decision(eig_arm, bank, history, median_convention='midpoint_integer')['exact_scores'] == eig['exact_scores']


def test_fix_round2b_acquisition_policies_aggregate_refusal_and_sensitivity_primitives() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    initial = 3
    history = [{'token_index': initial, 'prototype_index': bank[0][initial]}]
    passive = module.query_decision(
        'ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK', bank, history,
        median_convention='midpoint_integer',
    )
    assert passive['selected_token'] == 0
    no_query = module.query_decision(
        'ARM_I_TRANSFER__A_NO_QUERY__D_LCB05_FALLBACK', bank, history,
        median_convention='midpoint_integer',
    )
    assert no_query['selected_token'] is None and no_query['score_kind'] == 'none'
    with pytest.raises(ValueError, match='fixed token is not eligible'):
        module.query_decision(
            'ARM_I_TRANSFER__A_FIXED_V3__D_LCB05_FALLBACK', bank, history,
            median_convention='midpoint_integer',
        )
    with pytest.raises(ValueError, match='aggregate-only'):
        module.query_decision(
            'AGG_I_TRANSFER__A_UNIFORM_MIXTURE__D_LCB05_FALLBACK', bank, history,
            median_convention='midpoint_integer',
        )
    with pytest.raises(ValueError, match='aggregate-only'):
        module.prediction_decision(
            'AGG_I_TRANSFER__A_UNIFORM_MIXTURE__D_LCB05_FALLBACK', bank, history,
            median_convention='midpoint_integer',
        )

    scratch_eig = 'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1'
    lexical = module.query_decision(scratch_eig, bank, history, median_convention='midpoint_integer')
    assert len(lexical['minimizing_tokens']) > 1
    selected = max(lexical['minimizing_tokens'])
    alternate = module.query_decision(
        scratch_eig, bank, history, median_convention='midpoint_integer', query_policy=selected,
    )
    assert alternate['selected_token'] == selected
    assert alternate['tie_rule'] == 'enumerated_exact_minimizer'
    with pytest.raises(ValueError, match='exact minimizer'):
        module.query_decision(
            scratch_eig, bank, history, median_convention='midpoint_integer', query_policy=initial,
        )
    enumerated = module.enumerate_query_tie_decisions(
        scratch_eig, bank, history, median_convention='midpoint_integer',
    )
    assert [row['selected_token'] for row in enumerated] == lexical['minimizing_tokens']
    policies = module.enumerate_query_tie_policies(
        scratch_eig, bank, initial_token_index=initial,
        median_convention='midpoint_integer',
    )
    assert policies['h1_outcomes'] == [0, 1, 2, 3, 4]
    assert policies['policy_count'] == len(policies['policies'])
    assert policies['policy_count'] == 4 ** 5
    assert policies['query_selection_sensitive'] is True
    assert all(len(policy) == 5 for policy in policies['policies'])
    sensitivity = module.prediction_median_sensitivity(
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK', bank, history,
    )
    assert sensitivity['sensitive'] is (len(set(sensitivity['decision_sha256'].values())) > 1)


def test_fix_round2b_r1_primitive_weights_null_lcb_and_fail_closed_boundaries() -> None:
    module = _load_module()
    bank = module.build_multiplicity_bank((6,))
    mapping = bank[0]
    history = [{'token_index': 0, 'prototype_index': mapping[0]}]
    consistency_eig = 'ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN'
    state = module.build_state(
        consistency_eig, bank, history, median_convention='midpoint_integer',
    )
    effective = _rational_ints(state['effective_mapping_weights'])
    assert sorted(weight for weight in effective if weight > 0) == [6]
    assert sorted(weight for weight in module._primitive_integer_weights(state) if weight > 0) == [1]
    eig = module.query_decision(
        consistency_eig, bank, history, median_convention='midpoint_integer',
    )
    assert {row['int_score'] for row in eig['exact_scores']} == {1}

    median = module.prediction_decision(
        consistency_eig, bank, history, median_convention='midpoint_integer',
    )
    assert median['lcb05_benefit_micro'] == [None] * 5
    scratch = module.prediction_decision(
        'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1', bank, history,
        median_convention='midpoint_integer',
    )
    assert scratch['lcb05_benefit_micro'] == [None] * 5

    with pytest.raises(ValueError, match='aggregate.*FINITE trajectory state'):
        module.build_state(
            'AGG_I_TRANSFER__A_UNIFORM_MIXTURE__D_LCB05_FALLBACK',
            bank,
            history,
            median_convention='midpoint_integer',
        )

    target = module.mapping_space()[0]
    alternate = module.evaluate_target(
        bank,
        target,
        'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1',
        median_convention='midpoint_integer',
        query_policy=4,
    )
    assert alternate['selected_query_token'] == 4
    with pytest.raises(ValueError, match='exact minimizer'):
        module.evaluate_target(
            bank,
            target,
            'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1',
            median_convention='midpoint_integer',
            query_policy=0,
        )

    with pytest.raises(ValueError, match='query_policies must be a dict'):
        module.evaluate_bank(
            ['MULT_6'], bank, median_convention='midpoint_integer',
            query_policies=[],
        )


def test_fix_round2c1_target_private_classification_and_exact_metric_decomposition() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = next(mapping for mapping in module.mapping_space() if mapping[0] == 0)
    row = module.evaluate_target(
        bank,
        target,
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        median_convention='midpoint_integer',
    )

    assert row['schema_version'] == 'ARM_TARGET_METRIC_V1'
    assert row['selected_query_token'] == 3
    assert row['public_selected_query_token'] == 1
    assert row['metric_denominators'] == {
        'full': 20,
        'own_unqueried': 12,
        'common_unqueried': 8,
        'same_history_forward': 12,
    }
    assert row['full_improvement_raw'] == row['common_raw'] + row['query_asymmetry_raw']
    assert row['candidate_full_loss_raw'] == sum(row['candidate_token_losses_raw'])
    assert row['baseline_full_loss_raw'] == sum(row['baseline_token_losses_raw'])
    assert row['same_history_scratch_loss_raw'] == sum(
        row['same_history_scratch_token_losses_raw'][token]
        for token in row['candidate_own_unqueried_tokens']
    )
    for value in row['metric_rationals'].values():
        assert set(value) == {'n', 'd'}
        assert value == module._rational(module._decode_rational(value))

    support = set(bank)
    for mapping in module.mapping_space():
        classification = module.classify_target(bank, mapping)
        distance = min(sum(a != b for a, b in zip(mapping, source)) for source in support)
        assert classification['distance'] == distance
        assert distance != 1
        if mapping in support:
            assert classification['stratum'] == 'EXACT_MEMBER_D0'
            assert classification['source_occurrence'] == bank.count(mapping)
        else:
            assert classification['source_occurrence'] == 0
            assert classification['stratum'].endswith(f'D{distance}')


def test_fix_round2c1_query_policy_leaf_dispatch_and_rejection(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    arm_id = 'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1'
    policy = [4, 4, 4, 4, 4]
    calls = []

    def fake_evaluate_target(received_bank, target, received_arm_id, *, median_convention, query_policy=None):
        calls.append((tuple(target), received_arm_id, query_policy))
        return {
            'schema_version': 'TEST_METRIC',
            'arm_id': received_arm_id,
            'selected_query_token': (
                query_policy['candidate'] if isinstance(query_policy, dict)
                else query_policy
            ),
        }

    monkeypatch.setattr(module, 'evaluate_target', fake_evaluate_target)
    rows = module.evaluate_bank(
        ['HASH_00', 'B_SEPARABLE', 'B_DECOY'],
        bank,
        median_convention='midpoint_integer',
        query_policies={arm_id: policy, module.PUBLIC_ARM_ID: [2] * 5},
    )
    selected = [
        envelope['metric_rows'][0]['selected_query_token']
        for envelope in rows
        if envelope['metric_rows'][0]['arm_id'] == arm_id
    ]
    assert selected == [4] * 120
    assert [query_policy for _, received_arm, query_policy in calls if received_arm == arm_id] == [
        {'candidate': 4, 'public': 2}
    ] * 120
    assert all(envelope['bank_role_ids'] == ['HASH_00', 'B_SEPARABLE', 'B_DECOY'] for envelope in rows)

    with pytest.raises(ValueError, match='unknown|extra'):
        module.evaluate_bank(
            ['HASH_00'], bank, median_convention='midpoint_integer',
            query_policies={'DYNAMIC_ARM': policy},
        )
    with pytest.raises(ValueError, match='five'):
        module.evaluate_bank(
            ['HASH_00'], bank, median_convention='midpoint_integer',
            query_policies={arm_id: [4] * 4},
        )
    with pytest.raises(ValueError, match='exact minimizer'):
        module.evaluate_bank(
            ['HASH_00'], bank, median_convention='midpoint_integer',
            query_policies={arm_id: [0] * 5},
        )


def test_fix_round2c1_uniform_mixture_is_exact_metric_only_expectation() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    aggregate_id = 'AGG_I_TRANSFER__A_UNIFORM_MIXTURE__D_LCB05_FALLBACK'
    aggregate = module.evaluate_target(
        bank, target, aggregate_id, median_convention='midpoint_integer',
    )
    assert set(aggregate) == {
        'schema_version', 'arm_id', 'branch_arm_ids', 'branch_weights',
        'expected_metric_rationals',
    }
    assert aggregate['schema_version'] == 'AGGREGATE_METRIC_V1'
    assert aggregate['arm_id'] == aggregate_id
    assert aggregate['branch_weights'] == [{'n': 1, 'd': 4}] * 4
    assert len(aggregate['branch_arm_ids']) == 4
    assert all('__A_FIXED_V' in arm_id for arm_id in aggregate['branch_arm_ids'])
    branches = [
        module.evaluate_target(bank, target, arm_id, median_convention='midpoint_integer')
        for arm_id in aggregate['branch_arm_ids']
    ]
    for metric_id, expected in aggregate['expected_metric_rationals'].items():
        recomputed = sum(
            (module._decode_rational(branch['metric_rationals'][metric_id]) for branch in branches),
            module.Fraction(0, 1),
        ) / 4
        assert module._decode_rational(expected) == recomputed


def test_fix_round2c1_no_query_uses_set_derived_denominators_and_identity() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    row = module.evaluate_target(
        bank,
        target,
        'ARM_I_TRANSFER__A_NO_QUERY__D_LCB05_FALLBACK',
        median_convention='midpoint_integer',
    )
    assert row['selected_query_token'] is None
    assert row['metric_denominators'] == {
        'full': 20,
        'own_unqueried': 16,
        'common_unqueried': 12,
        'same_history_forward': 16,
    }
    q_public = row['public_selected_query_token']
    assert row['query_asymmetry_raw'] == -row['candidate_token_losses_raw'][q_public]
    assert row['full_improvement_raw'] == row['common_raw'] + row['query_asymmetry_raw']


def test_fix_round2c1_evaluate_bank_dispatches_every_frozen_record(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    calls = []

    def fake_evaluate_target(received_bank, target, arm_id, *, median_convention, query_policy=None):
        assert received_bank == bank
        calls.append((tuple(target), arm_id, median_convention, query_policy))
        return {'schema_version': 'TEST_METRIC', 'arm_id': arm_id}

    monkeypatch.setattr(module, 'evaluate_target', fake_evaluate_target)
    rows = module.evaluate_bank(['HASH_00'], bank, median_convention='midpoint_integer')
    frozen_ids = [row['arm_id'] for row in module.load_frozen_design()['arm_registry']['records']]
    assert len(rows) == 120 * 45
    assert len(calls) == 120 * 45
    assert {arm_id for _, arm_id, _, _ in calls} == set(frozen_ids)
    assert all(set(row) == {
        'schema_version', 'bank_role_ids', 'canonical_bank_sha256', 'target_mapping',
        'stratum', 'source_occurrence', 'distance', 'scorer_truth', 'metric_rows',
        'artifact_receipts',
    } for row in rows)


def test_fix_round2c1_r1_pairwise_public_policy_changes_common_set_and_fails_closed() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = next(mapping for mapping in module.mapping_space() if mapping[0] == 0)
    arm_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    lexical = module.evaluate_target(
        bank, target, arm_id, median_convention='midpoint_integer',
    )
    pairwise = module.evaluate_target(
        bank,
        target,
        arm_id,
        median_convention='midpoint_integer',
        query_policy={'candidate': None, 'public': 4},
    )
    assert lexical['selected_query_token'] == pairwise['selected_query_token'] == 3
    assert lexical['public_selected_query_token'] == 1
    assert pairwise['public_selected_query_token'] == 4
    assert lexical['common_unqueried_tokens'] != pairwise['common_unqueried_tokens']
    assert pairwise['full_improvement_raw'] == pairwise['common_raw'] + pairwise['query_asymmetry_raw']

    with pytest.raises(ValueError, match='exact minimizer|eligible'):
        module.evaluate_target(
            bank,
            target,
            arm_id,
            median_convention='midpoint_integer',
            query_policy={'candidate': None, 'public': 0},
        )
    for invalid in (
        {'candidate': None},
        {'candidate': None, 'public': None, 'extra': 1},
        {'candidate': True, 'public': None},
        {'candidate': None, 'public': '4'},
    ):
        with pytest.raises(ValueError, match='pair|component'):
            module.evaluate_target(
                bank,
                target,
                arm_id,
                median_convention='midpoint_integer',
                query_policy=invalid,
            )


def test_fix_round2c1_r1_bank_role_provenance_reconstructs_exact_bytes(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)

    def fake_evaluate_target(received_bank, target, arm_id, *, median_convention, query_policy=None):
        return {'schema_version': 'TEST_METRIC', 'arm_id': arm_id}

    monkeypatch.setattr(module, 'evaluate_target', fake_evaluate_target)
    rows = module.evaluate_bank(
        ['HASH_00', 'B_SEPARABLE', 'B_DECOY'],
        bank,
        median_convention='midpoint_integer',
    )
    assert len(rows) == 120 * 45
    assert all(row['bank_role_ids'] == ['HASH_00', 'B_SEPARABLE', 'B_DECOY'] for row in rows)

    for invalid_roles in (
        ['HASH_00_ALIAS'],
        ['HASH_01'],
        ['HASH_00', 'B_COLLISION'],
    ):
        with pytest.raises(ValueError, match='registered|canonical bank bytes'):
            module.evaluate_bank(
                invalid_roles, bank, median_convention='midpoint_integer',
            )


def test_fix_round2c1_r1_decision_byte_memoization_is_fresh_isolated_and_scoped(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    history = ((0, 0),)
    query_calls = 0
    prediction_calls = 0
    original_query = module.query_decision
    original_prediction = module.prediction_decision

    def query_spy(*args, **kwargs):
        nonlocal query_calls
        query_calls += 1
        return original_query(*args, **kwargs)

    def prediction_spy(*args, **kwargs):
        nonlocal prediction_calls
        prediction_calls += 1
        return original_prediction(*args, **kwargs)

    monkeypatch.setattr(module, 'query_decision', query_spy)
    monkeypatch.setattr(module, 'prediction_decision', prediction_spy)
    module._clear_decision_byte_memoization()
    transfer_arm = 'ARM_I_TRANSFER__A_PASSIVE__D_L1_MEDIAN'
    scratch_arm = 'ARM_I_SCRATCH__A_PASSIVE__D_SCRATCH_L1'
    first_query = module._fresh_query_decision(
        transfer_arm, bank, history, 'midpoint_integer', None,
    )
    first_prediction = module._fresh_prediction_decision(
        transfer_arm, bank, history, 'midpoint_integer',
    )
    first_query['eligible_tokens'].append(99)
    first_prediction['prediction_micro'][1][0] = -999
    second_query = module._fresh_query_decision(
        transfer_arm, bank, history, 'midpoint_integer', None,
    )
    second_prediction = module._fresh_prediction_decision(
        transfer_arm, bank, history, 'midpoint_integer',
    )
    assert 99 not in second_query['eligible_tokens']
    assert second_prediction['prediction_micro'][1][0] != -999
    assert query_calls == 1
    assert prediction_calls == 1

    module._fresh_query_decision(
        scratch_arm, bank, history, 'midpoint_integer', None,
    )
    module._fresh_prediction_decision(
        scratch_arm, bank, history, 'midpoint_integer',
    )
    tie_arm = 'ARM_I_SCRATCH__A_EIG__D_SCRATCH_L1'
    module._fresh_query_decision(tie_arm, bank, history, 'midpoint_integer', None)
    module._fresh_query_decision(tie_arm, bank, history, 'midpoint_integer', 2)
    assert query_calls == 4
    assert prediction_calls == 2
    assert module._memoized_query_decision_bytes.cache_info().currsize == 4
    assert module._memoized_prediction_decision_bytes.cache_info().currsize == 2

    def fake_evaluate_target(received_bank, target, arm_id, *, median_convention, query_policy=None):
        return {'schema_version': 'TEST_METRIC', 'arm_id': arm_id}

    monkeypatch.setattr(module, 'evaluate_target', fake_evaluate_target)
    module.evaluate_bank(['HASH_00'], bank, median_convention='midpoint_integer')
    assert module._memoized_query_decision_bytes.cache_info().currsize == 0
    assert module._memoized_prediction_decision_bytes.cache_info().currsize == 0


def test_fix_round2c2a_exact_ablation_registry_dispatches_all_thirteen_live_paths() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    frozen_ids = tuple(
        row['ablation_id']
        for row in module.load_frozen_design()['ablation_registry']['records']
    )
    assert module.registered_ablation_ids() == frozen_ids
    assert len(frozen_ids) == 13

    ordinary_ids = frozen_ids[:8] + (frozen_ids[-1],)
    for ablation_id in ordinary_ids:
        result = module.execute_registered_ablation(
            ablation_id,
            bank,
            target,
            median_convention='midpoint_integer',
        )
        assert result['ablation_id'] == ablation_id
        assert result['registered'] is True
        assert result['invocation_receipts']['evaluate_target_calls'] >= 1
        assert result['invocation_receipts']['query_decision_calls'] >= 1
        assert result['invocation_receipts']['prediction_decision_calls'] >= 1
        assert result['semantic_sha256'] == module.sha256(
            module._canonical_json_bytes(result['semantic_output'])
        ).hexdigest()
        assert result['semantic_equal_to_primary'] == [
            value == result['semantic_hashes']['primary_reference']
            for value in result['semantic_hashes']['registered_arms']
        ]
        assert result['semantic_changed_from_primary'] == [
            not value for value in result['semantic_equal_to_primary']
        ]

    source_delete = module.execute_registered_ablation(
        'ABL_SOURCE_DELETE', bank, target, median_convention='midpoint_integer',
    )
    assert source_delete['executed_arm_ids'] == [module.PUBLIC_ARM_ID]
    assert source_delete['public_byte_identity'] is True
    assert source_delete['semantic_hashes']['ablation'] == source_delete['semantic_hashes']['canonical_public']

    no_query = module.execute_registered_ablation(
        'ABL_NO_QUERY', bank, target, median_convention='midpoint_integer',
    )
    assert no_query['executed_arm_ids'] == [
        'ARM_I_TRANSFER__A_NO_QUERY__D_LCB05_FALLBACK',
        'ARM_I_SCRATCH__A_NO_QUERY__D_SCRATCH_L1',
        'ARM_I_CONSISTENCY__A_NO_QUERY__D_L1_MEDIAN',
    ]
    assert no_query['own_unqueried_denominators'] == [16, 16, 16]

    for invalid in ('DYNAMIC_ABLATION', '', None):
        with pytest.raises(ValueError, match='registered ablation'):
            module.execute_registered_ablation(
                invalid, bank, target, median_convention='midpoint_integer',
            )


def test_fix_round2c2a_source_order_unique_multiset_cases_use_same_live_semantics() -> None:
    module = _load_module()
    duplicate_bank = module.build_multiplicity_bank((3, 3))
    distinct_bank = module.build_hash_bank(1)
    assert len(module.enumerate_unique_source_orders(duplicate_bank)) == 20
    assert len(module.enumerate_unique_source_orders(distinct_bank)) == 720

    duplicate_order = module.enumerate_unique_source_orders(duplicate_bank)[-1]
    result = module.execute_source_order_invariance_case(
        duplicate_bank,
        module.mapping_space()[0],
        duplicate_order,
        median_convention='midpoint_integer',
        arm_ids=(module.PUBLIC_ARM_ID,),
    )
    assert result['semantic_equal'] is True
    assert result['unique_order_count'] == 20
    assert result['invocation_receipts'] == {
        'state_calls': 4,
        'query_decision_calls': 2,
        'prediction_decision_calls': 2,
    }
    assert result['baseline_semantic_sha256'] == result['reordered_semantic_sha256']

    distinct_result = module.execute_source_order_invariance_case(
        distinct_bank,
        module.mapping_space()[7],
        module.enumerate_unique_source_orders(distinct_bank)[-1],
        median_convention='midpoint_integer',
        arm_ids=(module.PUBLIC_ARM_ID,),
    )
    assert distinct_result['semantic_equal'] is True
    assert distinct_result['unique_order_count'] == 720

    corrupt = list(duplicate_order)
    corrupt[0] = module.mapping_space()[7]
    with pytest.raises(ValueError, match='multiset'):
        module.execute_source_order_invariance_case(
            duplicate_bank,
            module.mapping_space()[0],
            corrupt,
            median_convention='midpoint_integer',
            arm_ids=(module.PUBLIC_ARM_ID,),
        )


def test_fix_round2c2a_token_relabel_nonzero_initial_inverse_maps_live_receipts(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = next(mapping for mapping in module.mapping_space() if mapping[2] == 4)
    permutation = (2, 4, 1, 0, 3)
    result = module.execute_token_relabel_invariance_case(
        bank,
        target,
        permutation,
        initial_token_index=2,
        median_convention='midpoint_integer',
        bank_role_id='HASH_00',
    )
    assert result['initial_token_index'] == 2
    assert result['relabelled_initial_token_index'] == permutation[2]
    assert result['semantic_equal'] is True
    assert result['scope_arm_ids'] == [
        'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        module.PUBLIC_ARM_ID,
        'ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN',
    ]
    assert result['invocation_receipts']['query_decision_calls'] >= 9
    assert result['invocation_receipts']['prediction_decision_calls'] == 6
    assert result['baseline_semantic_sha256'] == result['inverse_mapped_semantic_sha256']

    with pytest.raises(ValueError, match='permutation'):
        module.execute_token_relabel_invariance_case(
            bank,
            target,
            (0, 1, 2, 3, 3),
            initial_token_index=2,
            median_convention='midpoint_integer',
            bank_role_id='HASH_00',
        )
    with pytest.raises(ValueError, match='role'):
        module.execute_token_relabel_invariance_case(
            bank,
            target,
            permutation,
            initial_token_index=2,
            median_convention='midpoint_integer',
            bank_role_id='B_COLLISION',
        )

    original_inverse = module._inverse_map_token_trace

    def sabotaged_inverse(trace, received_permutation):
        output = original_inverse(trace, received_permutation)
        output['prediction_decision']['prediction_micro'][0][0] += 1
        return output

    monkeypatch.setattr(module, '_inverse_map_token_trace', sabotaged_inverse)
    failed = module.execute_token_relabel_invariance_case(
        bank,
        target,
        permutation,
        initial_token_index=2,
        median_convention='midpoint_integer',
        bank_role_id='HASH_00',
    )
    assert failed['semantic_equal'] is False


def test_fix_round2c2a_prototype_relabel_validates_bijection_then_runs_same_core() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[11]
    permutation = (3, 0, 4, 1, 2)
    relabelled_bank = module.relabel_prototype_indices_in_bank(bank, permutation)
    relabelled_target = module.relabel_prototype_indices_in_mapping(target, permutation)
    table = module.build_relabelled_prototype_table(permutation)
    result = module.execute_prototype_relabel_invariance_case(
        relabelled_bank,
        relabelled_target,
        table,
        median_convention='midpoint_integer',
        bank_role_id='HASH_00',
    )
    assert result['semantic_equal'] is True
    assert result['validated_bijection'] is True
    assert result['invocation_receipts']['query_decision_calls'] == 6
    assert result['invocation_receipts']['prediction_decision_calls'] == 6
    assert result['baseline_semantic_sha256'] == result['inverse_mapped_semantic_sha256']

    arbitrary = json.loads(json.dumps(table))
    arbitrary[0]['vector_micro'][0] += 1
    with pytest.raises(ValueError, match='frozen vectors'):
        module.execute_prototype_relabel_invariance_case(
            relabelled_bank,
            relabelled_target,
            arbitrary,
            median_convention='midpoint_integer',
            bank_role_id='HASH_00',
        )
    non_bijection = json.loads(json.dumps(table))
    non_bijection[0]['prototype_index'] = non_bijection[1]['prototype_index']
    with pytest.raises(ValueError, match='bijection'):
        module.execute_prototype_relabel_invariance_case(
            relabelled_bank,
            relabelled_target,
            non_bijection,
            median_convention='midpoint_integer',
            bank_role_id='HASH_00',
        )
    with pytest.raises(ValueError, match='role'):
        module.execute_prototype_relabel_invariance_case(
            relabelled_bank,
            relabelled_target,
            table,
            median_convention='midpoint_integer',
            bank_role_id='B_COLLISION',
        )


def test_fix_round2c2a_eig_entropy_alias_uses_independent_live_callables_and_sabotage_fails(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    result = module.execute_eig_entropy_alias_invariance(
        bank,
        initial_token_index=3,
        initial_prototype_index=bank[0][3],
        median_convention='midpoint_integer',
    )
    assert result['semantic_equal'] is True
    assert result['inference_ids'] == ['I_TRANSFER', 'I_SCRATCH', 'I_CONSISTENCY']
    assert result['invocation_receipts'] == {
        'eig_query_decision_calls': 3,
        'entropy_query_decision_calls': 3,
    }
    assert all(row['exact_scores_equal'] and row['minimizers_equal'] and row['choice_equal'] for row in result['comparisons'])

    original = module._max_outcome_entropy_scores

    def sabotaged(weights, eligible):
        rows = original(weights, eligible)
        rows[0] = dict(rows[0], int_score=rows[0]['int_score'] + 1)
        return rows

    monkeypatch.setattr(module, '_max_outcome_entropy_scores', sabotaged)
    failed = module.execute_eig_entropy_alias_invariance(
        bank,
        initial_token_index=3,
        initial_prototype_index=bank[0][3],
        median_convention='midpoint_integer',
    )
    assert failed['semantic_equal'] is False
    assert any(not row['exact_scores_equal'] for row in failed['comparisons'])


def test_fix_round2c2a_invariance_ids_reach_dispatcher_without_formal_enumeration() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    source_order = module.enumerate_unique_source_orders(bank)[-1]
    token_permutation = module.mapping_space()[37]
    prototype_permutation = module.mapping_space()[73]
    cases = {
        'INV_SOURCE_ORDER': {'source_order': source_order},
        'INV_TOKEN_RELABEL': {
            'permutation': token_permutation,
            'initial_token_index': 2,
            'bank_role_id': 'HASH_00',
        },
        'INV_PROTOTYPE_RELABEL': {'permutation': prototype_permutation},
        'INV_EIG_ENTROPY_ALIAS': {'initial_token_index': 2},
    }
    for ablation_id, options in cases.items():
        result = module.execute_registered_ablation(
            ablation_id,
            bank,
            target,
            median_convention='midpoint_integer',
            **options,
        )
        assert result['ablation_id'] == ablation_id
        assert result['registered'] is True
        assert isinstance(result['semantic_equal'], bool)
        assert result['semantic_changed'] is (not result['semantic_equal'])
        assert result['semantic_hashes']
        assert result['invocation_receipts']
        if ablation_id == 'INV_SOURCE_ORDER':
            assert len(result['scope_arm_ids']) == 42

    with pytest.raises(ValueError, match='full frozen trajectory scope'):
        module.execute_registered_ablation(
            'INV_SOURCE_ORDER',
            bank,
            target,
            median_convention='midpoint_integer',
            source_order=source_order,
            arm_ids=(module.PUBLIC_ARM_ID,),
        )


def test_fix_round2c2a_r1_dispatcher_rejects_every_cross_id_option() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    order = module.enumerate_unique_source_orders(bank)[-1]

    hostile = (
        (
            'ABL_SOURCE_DELETE',
            {'initial_token_index': 1},
        ),
        (
            'INV_SOURCE_ORDER',
            {'source_order': order, 'bank_role_id': 'B_SEPARABLE'},
        ),
        (
            'INV_TOKEN_RELABEL',
            {'permutation': module.mapping_space()[3], 'source_order': order},
        ),
        (
            'INV_PROTOTYPE_RELABEL',
            {'permutation': module.mapping_space()[5], 'initial_token_index': 1},
        ),
        (
            'INV_EIG_ENTROPY_ALIAS',
            {'permutation': module.mapping_space()[7]},
        ),
        (
            'INV_EIG_ENTROPY_ALIAS',
            {'bank_role_id': 'B_SEPARABLE'},
        ),
    )
    for ablation_id, options in hostile:
        with pytest.raises(ValueError, match='option|argument|scope'):
            module.execute_registered_ablation(
                ablation_id,
                bank,
                target,
                median_convention='midpoint_integer',
                **options,
            )


def test_fix_round2c2a_r1_prototype_control_executes_relabelled_live_core_and_detects_label_sabotage(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[11]
    permutation = (3, 0, 4, 1, 2)
    relabelled_bank = module.relabel_prototype_indices_in_bank(bank, permutation)
    relabelled_target = module.relabel_prototype_indices_in_mapping(target, permutation)
    table = module.build_relabelled_prototype_table(permutation)
    frozen_table = module._prototype_table()
    expected_active_table = tuple(
        tuple(row['vector_micro'])
        for row in sorted(table, key=lambda row: row['prototype_index'])
    )
    assert relabelled_target != target

    calls = []
    original = module._run_live_semantic_trace

    def spy(arm_id, received_bank, received_target, **kwargs):
        calls.append((
            tuple(tuple(row) for row in received_bank),
            tuple(received_target),
            module._prototype_table(),
        ))
        return original(arm_id, received_bank, received_target, **kwargs)

    monkeypatch.setattr(module, '_run_live_semantic_trace', spy)
    result = module.execute_prototype_relabel_invariance_case(
        relabelled_bank,
        relabelled_target,
        table,
        median_convention='midpoint_integer',
        bank_role_id='HASH_00',
    )
    assert result['semantic_equal'] is True
    assert len(calls) == 6
    assert all(calls[index][0] == bank and calls[index][1] == target and calls[index][2] == frozen_table for index in (0, 2, 4))
    assert all(calls[index][0] == relabelled_bank and calls[index][1] == relabelled_target and calls[index][2] == expected_active_table for index in (1, 3, 5))

    calls.clear()

    def label_sensitive_sabotage(arm_id, received_bank, received_target, **kwargs):
        trace, receipt = original(arm_id, received_bank, received_target, **kwargs)
        if tuple(received_target) == relabelled_target:
            trace['prediction_decision']['prediction_micro'][0][0] += 1
        return trace, receipt

    monkeypatch.setattr(module, '_run_live_semantic_trace', label_sensitive_sabotage)
    failed = module.execute_prototype_relabel_invariance_case(
        relabelled_bank,
        relabelled_target,
        table,
        median_convention='midpoint_integer',
        bank_role_id='HASH_00',
    )
    assert failed['semantic_equal'] is False
    assert failed['semantic_changed'] is True


def test_fix_round2c2a_r1_primary_comparison_strips_registry_identity_only() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    trace, _ = module._run_live_semantic_trace(
        module.PUBLIC_ARM_ID,
        bank,
        target,
        initial_token_index=0,
        median_convention='midpoint_integer',
    )
    renamed = json.loads(json.dumps(trace))
    renamed['arm_id'] = 'RENAMED_ARM'
    for state_key in ('state_h1', 'state_final'):
        for field in ('arm_id', 'inference_id', 'acquisition_id', 'decision_id', 'transition_id'):
            renamed[state_key][field] = 'RENAMED_' + field
    renamed['query_decision']['arm_id'] = 'RENAMED_ARM'
    renamed['prediction_decision']['arm_id'] = 'RENAMED_ARM'
    assert module._behavior_semantic_payload(trace) == module._behavior_semantic_payload(renamed)
    assert module._semantic_sha256(module._behavior_semantic_payload(trace)) == module._semantic_sha256(
        module._behavior_semantic_payload(renamed)
    )


def test_fix_round2c2a_r1_controlled_table_context_rejects_unvalidated_vectors() -> None:
    module = _load_module()
    frozen = module._prototype_table()
    arbitrary = ((999, 998, 997, 996),) + frozen[1:]
    with pytest.raises(ValueError, match='frozen-vector bijection'):
        with module._controlled_prototype_table_context(arbitrary):
            raise AssertionError('unvalidated table entered controlled context')


def test_fix_round2c2b_amortized_hash00_aliases_cover_exact_public_domain_and_live_bytes(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    calls = {'query': 0, 'prediction': 0}
    real_query = module.query_decision
    real_prediction = module.prediction_decision
    real_builder_query = module._amortized_live_query_output
    real_builder_prediction = module._amortized_live_prediction_output

    def counted_query(*args, **kwargs):
        calls['query'] += 1
        return real_builder_query(*args, **kwargs)

    def counted_prediction(*args, **kwargs):
        calls['prediction'] += 1
        return real_builder_prediction(*args, **kwargs)

    monkeypatch.setattr(module, '_amortized_live_query_output', counted_query)
    monkeypatch.setattr(module, '_amortized_live_prediction_output', counted_prediction)
    table = module.build_amortized_lookup({
        'HASH_00': bank,
        'B_SEPARABLE': tuple(reversed(bank)),
        'B_DECOY': bank,
    })
    assert table['builder_id'] == 'CANDIDATE_RULE_AMORTIZED_LOOKUP'
    assert table['primary_arm_id'] == 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    # Distinct permutation tokens cannot share a prototype.  Of the nominal
    # 100 H2 combinations, 20 have zero likelihood even under scratch.
    assert table['state_count'] == 85
    assert len(table['states']) == 85
    assert table['phase_state_counts'] == {'H1': 5, 'H2': 80}
    assert table['bank_provenance'] == [{
        'canonical_bank_sha256': hashlib.sha256(module.canonical_bank_bytes(bank)).hexdigest(),
        'role_ids': ['B_DECOY', 'B_SEPARABLE', 'HASH_00'],
        'state_count': 85,
    }]
    assert calls == {'query': 5, 'prediction': 80}
    assert all(type(key) is str and len(key) == 64 for key in table['states'])
    assert all(type(output) is bytes and b'role_id' not in output for output in table['states'].values())

    primary = table['primary_arm_id']
    expected_lookups = 0
    for h1_outcome in range(5):
        h1 = [{'token_index': 0, 'prototype_index': h1_outcome}]
        payload = _canonical_public_payload(module, bank, h1, primary)
        assert module.lookup_query_or_prediction(table, payload) == real_query(
            primary, bank, h1, median_convention='midpoint_integer',
        )
        expected_lookups += 1
        for second_token in range(1, 5):
            for h2_outcome in range(5):
                if h2_outcome == h1_outcome:
                    continue
                h2 = h1 + [
                    {'token_index': second_token, 'prototype_index': h2_outcome}
                ]
                payload = _canonical_public_payload(module, bank, h2, primary)
                assert module.lookup_query_or_prediction(table, payload) == real_prediction(
                    primary, bank, h2, median_convention='midpoint_integer',
                )
                expected_lookups += 1
    assert expected_lookups == 85


def test_fix_round2c2b_amortized_provenance_collision_integrity_and_fresh_outputs(monkeypatch) -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    primary = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    with pytest.raises(ValueError, match='registered role'):
        module.build_amortized_lookup({'HASH_00_FAKE': bank})
    with pytest.raises(ValueError, match='canonical bank bytes mismatch'):
        module.build_amortized_lookup({'HASH_00': module.build_hash_bank(1)})

    monkeypatch.setattr(module, '_public_state_key', lambda _payload_bytes: '0' * 64)
    with pytest.raises(ValueError, match='public state key collision'):
        module.build_amortized_lookup({'HASH_00': bank})
    monkeypatch.undo()

    table = module.build_amortized_lookup({'HASH_00': bank})
    h1 = [{'token_index': 0, 'prototype_index': 0}]
    payload = _canonical_public_payload(module, bank, h1, primary)
    first = module.lookup_query_or_prediction(table, payload)
    first['selected_token'] = 99
    second = module.lookup_query_or_prediction(table, payload)
    assert second['selected_token'] != 99

    forged_output = deepcopy(table)
    key = next(iter(forged_output['states']))
    forged_output['states'][key] = b'{}'
    with pytest.raises(ValueError, match='lookup table integrity'):
        module.lookup_query_or_prediction(forged_output, payload)

    forged_key = deepcopy(table)
    value = forged_key['states'].pop(key)
    forged_key['states']['f' * 64] = value
    with pytest.raises(ValueError, match='lookup table integrity'):
        module.lookup_query_or_prediction(forged_key, payload)

    private_payload = deepcopy(payload)
    private_payload['bank_role'] = 'HASH_00'
    with pytest.raises(ValueError):
        module.lookup_query_or_prediction(table, private_payload)

    bad_state = deepcopy(payload)
    bad_state['learner_state']['consistency_counts'][0] += 1
    with pytest.raises(ValueError):
        module.lookup_query_or_prediction(table, bad_state)

    scratch_payload = _canonical_public_payload(
        module, bank, h1, 'ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1',
    )
    with pytest.raises(ValueError, match='primary arm'):
        module.lookup_query_or_prediction(table, scratch_payload)

    unknown_history = [{'token_index': 1, 'prototype_index': 0}]
    unknown = _canonical_public_payload(module, bank, unknown_history, primary)
    assert module.validate_public_input(unknown)['initial_token_index'] == 1
    with pytest.raises(KeyError, match='unknown valid public state'):
        module.lookup_query_or_prediction(table, unknown)

    impossible_h2 = h1 + [{'token_index': 1, 'prototype_index': 0}]
    with pytest.raises(ValueError, match='zero effective evidence'):
        _canonical_public_payload(module, bank, impossible_h2, primary)


def test_fix_round2c2b_leakage_receipts_cover_direct_encoded_and_do_not_depend_on_alias_scanner(monkeypatch) -> None:
    module = _load_module()
    frozen_classes = module.load_frozen_design()['leakage']['forbidden_classes']
    result = module.run_leakage_positive_controls()
    assert result['base_validated'] is True
    assert result['forbidden_class_count'] == len(frozen_classes) == 12
    assert [row['forbidden_class'] for row in result['receipts']] == frozen_classes
    assert all(row['direct_rejected'] and row['encoded_rejected'] for row in result['receipts'])
    assert all(row['direct_error'] and row['encoded_error'] for row in result['receipts'])
    assert result['direct_case_count'] == result['encoded_case_count'] == 12
    assert result['rejected_case_count'] == 24
    assert result['passed'] is True

    monkeypatch.setattr(module, '_reject_forbidden_aliases', lambda _value: None)
    scanner_disabled = module.run_leakage_positive_controls()
    assert scanner_disabled['passed'] is True
    assert scanner_disabled['rejected_case_count'] == 24


def test_fix_round2c2b_leakage_validator_sabotage_fails_positive_control(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module, 'validate_public_input', lambda payload: payload)
    sabotaged = module.run_leakage_positive_controls()
    assert sabotaged['base_validated'] is True
    assert sabotaged['rejected_case_count'] == 0
    assert sabotaged['passed'] is False


def test_fix_round2c2b_r1_resigned_output_swap_is_rejected_by_live_recomputation() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    table = module.build_amortized_lookup({'HASH_00': bank})
    primary = table['primary_arm_id']
    h1_zero = [{'token_index': 0, 'prototype_index': 0}]
    h1_one = [{'token_index': 0, 'prototype_index': 1}]
    payload_zero = _canonical_public_payload(module, bank, h1_zero, primary)
    payload_one = _canonical_public_payload(module, bank, h1_one, primary)
    key_zero = module._public_state_key(module._canonical_public_input_bytes(payload_zero))
    key_one = module._public_state_key(module._canonical_public_input_bytes(payload_one))
    assert table['states'][key_zero] != table['states'][key_one]

    forged = deepcopy(table)
    forged['states'][key_zero], forged['states'][key_one] = (
        forged['states'][key_one], forged['states'][key_zero],
    )
    forged['table_sha256'] = module._lookup_table_sha256({
        key: value for key, value in forged.items() if key != 'table_sha256'
    })
    assert forged['table_sha256'] != table['table_sha256']
    module._clear_amortized_validation_cache()
    with pytest.raises(ValueError, match='independent live recomputation mismatch'):
        module.lookup_query_or_prediction(forged, payload_zero)


def test_fix_round2c2b_r1_resigned_role_provenance_forge_is_rejected() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    table = module.build_amortized_lookup({'HASH_00': bank})
    primary = table['primary_arm_id']
    payload = _canonical_public_payload(
        module, bank, [{'token_index': 0, 'prototype_index': 0}], primary,
    )
    forged = deepcopy(table)
    forged['bank_provenance'][0]['role_ids'] = ['HASH_01']
    forged['table_sha256'] = module._lookup_table_sha256({
        key: value for key, value in forged.items() if key != 'table_sha256'
    })
    module._clear_amortized_validation_cache()
    with pytest.raises(ValueError, match='registered provenance bank mismatch'):
        module.lookup_query_or_prediction(forged, payload)


def test_fix_round2c3a_strict_metric_validation_and_live_recompute_rejects_stored_claims() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = module.mapping_space()[0]
    arm_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    policy = {'candidate': None, 'public': 4}
    metric = module.evaluate_target(
        bank, target, arm_id, median_convention='midpoint_integer',
        query_policy=policy,
    )
    assert module.validate_arm_target_metric(metric) == metric
    assert module._validate_and_live_recompute_metric(
        metric,
        bank=bank,
        target_mapping=target,
        arm_id=arm_id,
        median_convention='midpoint_integer',
        query_policy=policy,
    ) == metric

    extra = deepcopy(metric)
    extra['verdict'] = 'ACTIVE_TRANSFER_STATIC_REFERENCE_FEASIBLE'
    with pytest.raises(ValueError, match='metric keys'):
        module.validate_arm_target_metric(extra)
    for key in ('bounded_core', 'winner', 'gate_pass'):
        forged = deepcopy(metric)
        forged[key] = True
        with pytest.raises(ValueError, match='metric keys'):
            module._validate_and_live_recompute_metric(
                forged,
                bank=bank,
                target_mapping=target,
                arm_id=arm_id,
                median_convention='midpoint_integer',
                query_policy=policy,
            )

    bad_loss = deepcopy(metric)
    bad_loss['candidate_token_losses_raw'][2] += 1
    with pytest.raises(ValueError, match='loss|semantic'):
        module.validate_arm_target_metric(bad_loss)
    bad_rational = deepcopy(metric)
    bad_rational['metric_rationals']['candidate_full_endpoint_mae'] = {'n': 0, 'd': 1}
    with pytest.raises(ValueError, match='rational|semantic'):
        module.validate_arm_target_metric(bad_rational)
    with pytest.raises(ValueError, match='live metric recomputation mismatch'):
        module._validate_and_live_recompute_metric(
            metric,
            bank=bank,
            target_mapping=target,
            arm_id=arm_id,
            median_convention='midpoint_integer',
            query_policy={'candidate': None, 'public': 1},
        )


def test_fix_round2c3a_recursive_metric_schema_and_pairwise_common_mae() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    target = next(mapping for mapping in module.mapping_space() if mapping[0] == 0)
    left = module.evaluate_target(
        bank, target, 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK',
        median_convention='midpoint_integer',
    )
    right = module.evaluate_target(
        bank, target, 'ARM_I_TRANSFER__A_PASSIVE__D_LCB05_FALLBACK',
        median_convention='midpoint_integer',
    )
    assert left['selected_query_token'] != right['selected_query_token']
    pair = module._pairwise_common_mae(left, right)
    expected_tokens = sorted(
        {1, 2, 3, 4} - {left['selected_query_token'], right['selected_query_token']}
    )
    assert pair['common_tokens'] == expected_tokens
    assert pair['component_denominator'] == 8
    left_raw = sum(left['candidate_token_losses_raw'][token] for token in expected_tokens)
    right_raw = sum(right['candidate_token_losses_raw'][token] for token in expected_tokens)
    assert module._decode_rational(pair['left_mae']) == module.Fraction(left_raw, 8_000_000)
    assert module._decode_rational(pair['right_mae']) == module.Fraction(right_raw, 8_000_000)
    assert module._decode_rational(pair['left_advantage']) == module.Fraction(right_raw - left_raw, 8_000_000)

    malformed = deepcopy(left)
    malformed['query_decision']['exact_scores'][0]['stored_winner'] = True
    with pytest.raises(ValueError, match='query score row keys'):
        module.validate_arm_target_metric(malformed)
    malformed = deepcopy(left)
    malformed['prediction_decision']['prediction_micro'][0].append(0)
    with pytest.raises(ValueError, match='prediction shape'):
        module.validate_arm_target_metric(malformed)
    malformed = deepcopy(left)
    malformed['query_decision']['minimizing_tokens'] = list(
        malformed['query_decision']['eligible_tokens']
    )
    with pytest.raises(ValueError, match='minimizing query tokens'):
        module.validate_arm_target_metric(malformed)


def test_fix_round2c3a_pointwise_member_safety_and_control_primitives() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    conservative_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    raw_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_L1_MEDIAN'

    def rows_for(arm_id):
        return {
            target: module.evaluate_target(
                bank, target, arm_id, median_convention='midpoint_integer',
            )
            for target in module.mapping_space()
        }

    conservative = rows_for(conservative_id)
    raw = rows_for(raw_id)
    role_banks = {'HASH_00': bank}
    candidate = {'HASH_00': conservative}
    raw_by_role = {'HASH_00': raw}
    def validated_view(arm_id, role_rows):
        return module._ValidatedLiveBoundMetricView(
            expected_arm_id=arm_id,
            median_convention='midpoint_integer',
            role_banks=role_banks,
            candidate_query_policies={'HASH_00': (None,) * 5},
            public_query_policies={'HASH_00': (None,) * 5},
            rows_by_role=role_rows,
            digest_sha256='unit-formula-view',
        )

    candidate_index = validated_view(conservative_id, candidate)
    raw_index = validated_view(raw_id, raw_by_role)
    reduced = module._reduce_candidate_and_raw_validated_views(
        candidate_index, raw_index,
    )
    manual_raw_bounded = all(
        -module._decode_rational(row['metric_rationals']['full_endpoint_improvement'])
        <= module.Fraction(4375, 1_000_000)
        for target, row in raw.items()
        if module.classify_target(bank, target)['distance'] in {2, 3, 4, 5}
    )
    assert reduced['raw_bounded_safety'] is manual_raw_bounded
    assert set(reduced) == {
        'raw_upside', 'raw_bounded_safety',
        'conservative_member_and_forward', 'conservative_bounded_safety',
        'conservative_strict_safety', 'role_receipts',
    }
    with pytest.raises(ValueError, match='live-bound metric index'):
        module._reduce_candidate_and_raw_primitives(candidate, raw_by_role)

    identical = module._pareto_match_validated_views(candidate_index, candidate_index)
    assert identical['matches'] is True
    assert identical['byte_identical_metric_rationals_everywhere'] is True
    assert identical['strict_improvement_found'] is False
    with pytest.raises(ValueError, match='exact 19'):
        module._reduce_exact_control_pareto(candidate_index, {})

    consistency = {'HASH_00': rows_for(
        'ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN'
    )}
    consistency_index = validated_view(
        'ARM_I_CONSISTENCY__A_L1_EVSI__D_L1_MEDIAN', consistency,
    )
    same_consistency = module._consistency_positive_non_equivalence_validated_views(
        candidate_index, consistency_index,
    )
    assert same_consistency['control_match'] is (
        not same_consistency['positive_non_equivalence']
    )


def test_fix_round2c3a_no_update_requires_both_registered_arms() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    conservative_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    no_update_ids = (
        'ARM_I_NO_UPDATE__A_L1_EVSI__D_LCB05_FALLBACK',
        'ARM_I_NO_UPDATE__A_PASSIVE__D_LCB05_FALLBACK',
    )

    def all_rows(arm_id):
        return {
            target: module.evaluate_target(
                bank, target, arm_id, median_convention='midpoint_integer',
            )
            for target in module.mapping_space()
        }

    role_banks = {'HASH_00': bank}
    def validated_view(arm_id):
        return module._ValidatedLiveBoundMetricView(
            expected_arm_id=arm_id,
            median_convention='midpoint_integer',
            role_banks=role_banks,
            candidate_query_policies={'HASH_00': (None,) * 5},
            public_query_policies={'HASH_00': (None,) * 5},
            rows_by_role={'HASH_00': all_rows(arm_id)},
            digest_sha256='unit-formula-view',
        )

    conservative = validated_view(conservative_id)
    no_update = {
        arm_id: validated_view(arm_id) for arm_id in no_update_ids
    }
    result = module._reduce_no_update_validated_views(conservative, no_update)
    assert set(result['per_arm']) == set(no_update_ids)
    assert all('complete_member_and_forward' in row for row in result['per_arm'].values())
    with pytest.raises(ValueError, match='both registered no-update arms'):
        module._reduce_no_update_validated_views(
            conservative, {no_update_ids[0]: no_update[no_update_ids[0]]},
        )


def test_fix_round2c3a_ordinary_branch_partition_and_legacy_boolean_path_rejection() -> None:
    module = _load_module()
    facts = {
        'raw_upside': False,
        'raw_bounded_safety': False,
        'conservative_member_and_forward': False,
        'conservative_bounded_safety': False,
        'conservative_strict_safety': False,
        'attribution_gate': False,
        'control_match': True,
    }
    derived = module._derive_ordinary_branch(facts)
    assert derived['ordinary_branch'] == 7
    assert derived['bounded_core'] is False
    with pytest.raises(ValueError, match='strict safety implies bounded safety'):
        module._derive_ordinary_branch({
            **facts,
            'conservative_member_and_forward': True,
            'conservative_strict_safety': True,
        })
    truth_table = module._synthetic_dispatch_truth_table_non_evidence()
    assert truth_table['evidence_eligible'] is False
    assert set(row['ordinary_branch'] for row in truth_table['rows']) == set(range(5, 12))
    assert all(row['matching_branch_count'] == 1 for row in truth_table['rows'])

    with pytest.raises(ValueError, match='ledger-bound C3B'):
        module.compute_gate_inputs([{'bounded_core': True, 'verdict': 'pass'}])
    with pytest.raises(ValueError, match='ledger-bound C3B'):
        module.dispatch_verdict({'ordinary_branch': 11})


def test_fix_round2c3a_r1_live_bound_per_role_helper_rejects_context_forgery() -> None:
    module = _load_module()
    bank = module.build_hash_bank(0)
    other_bank = module.build_hash_bank(1)
    arm_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    def all_rows(source_bank, source_arm=arm_id, median='midpoint_integer'):
        return {
            target: module.evaluate_target(
                source_bank, target, source_arm, median_convention=median,
            )
            for target in module.mapping_space()
        }

    rows = all_rows(bank)
    live = module._live_recompute_role_metric_rows(
        'HASH_00', bank, rows,
        expected_arm_id=arm_id,
        median_convention='midpoint_integer',
        candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
    )
    assert live['candidate_query_policy'] == (None,) * 5
    assert live['public_query_policy'] == (None,) * 5
    assert set(live['rows']) == set(module.mapping_space())
    assert live['rows'] == rows

    with pytest.raises(ValueError, match='registered primary role'):
        module._live_recompute_role_metric_rows(
            'FAKE_ALIAS', bank, rows,
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )
    with pytest.raises(ValueError, match='canonical bank provenance'):
        module._live_recompute_role_metric_rows(
            'HASH_00', other_bank, all_rows(other_bank),
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )
    with pytest.raises(ValueError, match='live metric recomputation mismatch'):
        module._live_recompute_role_metric_rows(
            'HASH_00', bank, all_rows(other_bank),
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )
    with pytest.raises(ValueError, match='live metric recomputation mismatch'):
        module._live_recompute_role_metric_rows(
            'HASH_00', bank, rows,
            expected_arm_id=arm_id, median_convention='lower',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )
    with pytest.raises(ValueError, match='exact minimizer|live metric recomputation mismatch'):
        module._live_recompute_role_metric_rows(
            'HASH_00', bank, rows,
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=(1, 1, 1, 1, 1),
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )
    with pytest.raises(ValueError, match='live metric recomputation mismatch'):
        module._live_recompute_role_metric_rows(
            'HASH_00', bank, rows,
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=(2, 2, 2, 2, 2),
        )

    forged = deepcopy(rows)
    forged[module.mapping_space()[0]] = deepcopy(forged[module.mapping_space()[1]])
    forged[module.mapping_space()[0]]['target_mapping'] = list(module.mapping_space()[0])
    with pytest.raises(ValueError, match='semantic|live metric'):
        module._live_recompute_role_metric_rows(
            'HASH_00', bank, forged,
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policy_spec=module.LEXICAL_QUERY_POLICY,
            public_query_policy_spec=module.LEXICAL_QUERY_POLICY,
        )


def test_fix_round2c3a_r2_full_suite_content_addressed_admission(monkeypatch) -> None:
    module = _load_module()
    role_ids = tuple(module._frozen_design()['bank_suite']['primary_role_ids'])
    arm_id = 'ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK'
    banks = {role_id: module._reconstruct_primary_role_bank(role_id) for role_id in role_ids}
    base_rows = {
        target: module.evaluate_target(
            banks['HASH_00'], target, arm_id, median_convention='midpoint_integer',
        )
        for target in module.mapping_space()
    }
    rows = {role_id: base_rows for role_id in role_ids}
    lexical = {role_id: module.LEXICAL_QUERY_POLICY for role_id in role_ids}

    short_ids = role_ids[:-1]
    with pytest.raises(ValueError, match='exact all 75 frozen primary roles'):
        module.build_live_bound_metric_index(
            {role_id: banks[role_id] for role_id in short_ids},
            {role_id: rows[role_id] for role_id in short_ids},
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policies={role_id: lexical[role_id] for role_id in short_ids},
            public_query_policies={role_id: lexical[role_id] for role_id in short_ids},
        )
    fake_banks = dict(banks)
    fake_banks.pop(role_ids[-1])
    fake_banks['FAKE_ALIAS'] = banks[role_ids[-1]]
    fake_rows = dict(rows)
    fake_rows.pop(role_ids[-1])
    fake_rows['FAKE_ALIAS'] = base_rows
    fake_lexical = dict(lexical)
    fake_lexical.pop(role_ids[-1])
    fake_lexical['FAKE_ALIAS'] = module.LEXICAL_QUERY_POLICY
    with pytest.raises(ValueError, match='exact all 75 frozen primary roles'):
        module.build_live_bound_metric_index(
            fake_banks, fake_rows,
            expected_arm_id=arm_id, median_convention='midpoint_integer',
            candidate_query_policies=fake_lexical,
            public_query_policies=fake_lexical,
        )

    helper_calls = []

    def structural_helper(role_id, bank, stored_rows, **kwargs):
        helper_calls.append(role_id)
        assert bank == banks[role_id]
        assert kwargs['expected_arm_id'] == arm_id
        return {
            'candidate_query_policy': (None,) * 5,
            'public_query_policy': (None,) * 5,
            'rows': stored_rows,
        }

    # This is the single bounded all-75 structural test. Only the exact
    # production per-role live helper is replaced; builder/admission/reducer
    # logic is unchanged.
    monkeypatch.setattr(module, '_live_recompute_role_metric_rows', structural_helper)
    index = module.build_live_bound_metric_index(
        banks, rows,
        expected_arm_id=arm_id, median_convention='midpoint_integer',
        candidate_query_policies=lexical, public_query_policies=lexical,
    )
    assert helper_calls == list(role_ids)
    assert set(module.LiveBoundMetricIndex.__slots__) == {'payload_bytes', 'digest_sha256'}
    view = module._require_live_bound_metric_index(index, expected_arm_id=arm_id)
    assert tuple(view.role_banks) == role_ids
    assert all(set(view.rows_by_role[role_id]) == set(module.mapping_space()) for role_id in role_ids)
    first_target = module.mapping_space()[0]
    expected_full_loss = view.rows_by_role['HASH_00'][first_target][
        'metric_rationals'
    ]['candidate_full_endpoint_mae']
    view.rows_by_role['HASH_00'][first_target]['metric_rationals'][
        'candidate_full_endpoint_mae'
    ] = {'numerator': 999, 'denominator': 1}
    del view
    fresh_view = module._require_live_bound_metric_index(index, expected_arm_id=arm_id)
    assert fresh_view.rows_by_role['HASH_00'][first_target][
        'metric_rationals'
    ]['candidate_full_endpoint_mae'] == expected_full_loss
    del fresh_view

    with pytest.raises(ValueError, match='canonical builder'):
        module.LiveBoundMetricIndex(index.payload_bytes, index.digest_sha256)

    original_bytes = index.payload_bytes
    original_digest = index.digest_sha256
    header_end = original_bytes.find(b'\n')
    policy_payload = module.json.loads(original_bytes[:header_end].decode('utf-8'))
    policy_payload['candidate_query_policies'][0]['choices'][0] = 1
    index.payload_bytes = (
        module._canonical_json_bytes(policy_payload) + b'\n'
        + original_bytes[header_end + 1:]
    )
    index.digest_sha256 = module.sha256(index.payload_bytes).hexdigest()
    with pytest.raises(ValueError, match='not admitted'):
        module._require_live_bound_metric_index(index)

    first_metric_end = original_bytes.find(b'\n', header_end + 1)
    metric_payload = module.json.loads(
        original_bytes[header_end + 1:first_metric_end].decode('utf-8')
    )
    metric_payload['metric']['candidate_full_loss_raw'] += 1
    index.payload_bytes = (
        original_bytes[:header_end + 1]
        + module._canonical_json_bytes(metric_payload) + b'\n'
        + original_bytes[first_metric_end + 1:]
    )
    index.digest_sha256 = module.sha256(index.payload_bytes).hexdigest()
    with pytest.raises(ValueError, match='not admitted'):
        module._require_live_bound_metric_index(index)

    index.payload_bytes = original_bytes
    index.digest_sha256 = original_digest
    module._clear_live_bound_metric_index_admission_cache_for_tests()
    with pytest.raises(ValueError, match='not admitted'):
        module._require_live_bound_metric_index(index)



def test_fix_round2c3b1_normative_plan_counts_and_lazy_prefix() -> None:
    from itertools import islice

    module = _load_module()
    plan = module.build_gate_execution_plan()
    assert module.validate_gate_execution_plan(plan) == plan
    assert plan['schema_version'] == 'GATE_EXECUTION_PLAN_V1'
    assert len(plan['variant_registry']) == 6
    assert [row['variant_id'] for row in plan['variant_registry']] == [
        'MEDIAN_LOWER__LEXICAL',
        'MEDIAN_LOWER__SYMBOLIC_GLOBAL_POLICY_DP_V1',
        'MEDIAN_MIDPOINT_INTEGER__LEXICAL',
        'MEDIAN_MIDPOINT_INTEGER__SYMBOLIC_GLOBAL_POLICY_DP_V1',
        'MEDIAN_UPPER__LEXICAL',
        'MEDIAN_UPPER__SYMBOLIC_GLOBAL_POLICY_DP_V1',
    ]
    assert len(plan['bank_groups']) == 76
    assert len(plan['query_sensitivity_pairs']) == 39
    generator_rows = plan['prerequisite_case_plan']['generator_rows']
    assert len(generator_rows) == 31
    assert generator_rows[0]['generator_id'] == 'GEN_AUTHORITY_HASH'
    assert generator_rows[-1]['generator_id'] == 'GEN_SYMBOLIC_LOCAL_AGGREGATE'
    assert plan['prerequisite_case_plan']['expected_case_count'] == sum(
        row['expected_count'] for row in generator_rows
    )
    assert generator_rows[2]['expected_count'] == 6 * 76 * 120 * 45

    prefix = list(islice(module.iter_expected_prerequisite_cases(plan), 7))
    assert len(prefix) == 7
    assert [row['case_kind'] for row in prefix[:3]] == ['AUTHORITY_HASH'] * 3
    assert [row['case_kind'] for row in prefix[3:]] == ['BANK_COVERAGE'] * 4
    assert len({row['case_id'] for row in prefix}) == len(prefix)
    for row in prefix:
        decoded = json.loads(row['canonical_input_bytes'].decode('utf-8'))
        assert decoded['schema_version'] == 'PREREQUISITE_CASE_INPUT_V1'
        assert hashlib.sha256(row['canonical_input_bytes']).hexdigest() == row['input_sha256']

    forged = deepcopy(plan)
    forged['prerequisite_case_plan']['generator_rows'][2]['expected_count'] += 1
    forged['prerequisite_case_plan']['expected_case_count'] += 1
    with pytest.raises(ValueError, match='normative execution plan mismatch'):
        module.validate_gate_execution_plan(forged)
    reordered = deepcopy(plan)
    reordered['prerequisite_case_plan']['generator_rows'][0:2] = reversed(
        reordered['prerequisite_case_plan']['generator_rows'][0:2]
    )
    with pytest.raises(ValueError, match='normative execution plan mismatch'):
        module.validate_gate_execution_plan(reordered)

    hostile_plans = []
    for mutate in (
        lambda value: value['primary_role_ids'].pop(),
        lambda value: value['arm_ids'].pop(),
        lambda value: value['variant_registry'].pop(),
        lambda value: value['bank_groups'].pop(),
        lambda value: value['bank_groups'][0]['target_mappings'].pop(),
        lambda value: value['query_sensitivity_pairs'].pop(),
        lambda value: value['bank_groups'][0].__setitem__(
            'canonical_member', value['bank_groups'][0]['target_mappings'][-1]
        ),
        lambda value: value['bank_groups'][0]['role_ids'].append(
            value['bank_groups'][0]['role_ids'][0]
        ),
        lambda value: value['query_sensitivity_pairs'].append({
            **value['query_sensitivity_pairs'][0],
            'pair_id': 'f' * 64,
            'gate_ids': ['INV_EIG_ENTROPY_ALIAS'],
        }),
    ):
        hostile = deepcopy(plan)
        mutate(hostile)
        hostile_plans.append(hostile)
    for hostile in hostile_plans:
        with pytest.raises(ValueError, match='normative execution plan mismatch'):
            module.validate_gate_execution_plan(hostile)


def test_fix_round2c3b1_structural_ledger_and_packet_prefix_validation() -> None:
    from itertools import islice

    module = _load_module()
    plan = module.build_gate_execution_plan()
    plan_sha = hashlib.sha256(module._canonical_json_bytes(plan)).hexdigest()
    variant = plan['variant_registry'][0]
    records_by_id = {
        row['arm_id']: row for row in module._frozen_design()['arm_registry']['records']
    }
    selectable = sorted(
        arm_id for arm_id in plan['arm_ids']
        if records_by_id[arm_id]['kind'] == 'trajectory'
        and records_by_id[arm_id]['acquisition_id'] != 'A_NO_QUERY'
    )
    bank = tuple(tuple(row) for row in plan['bank_groups'][0]['canonical_bank'])
    policy_rows = []
    for arm_id in selectable[:2]:
        choices = [
            module.query_decision(
                arm_id, bank,
                [{'token_index': 0, 'prototype_index': outcome}],
                median_convention=variant['median_convention'],
            )['selected_token']
            for outcome in range(5)
        ]
        policy_rows.append({
            'canonical_bank_sha256': plan['bank_groups'][0]['canonical_bank_sha256'],
            'arm_id': arm_id,
            'choices_by_h1_outcome': choices,
        })
    ledger = {
        'schema_version': 'GATE_VARIANT_LEDGER_V1',
        'execution_plan_sha256': plan_sha,
        'variant_id': variant['variant_id'],
        'median_convention': variant['median_convention'],
        'variant_kind': variant['variant_kind'],
        'query_policy_rows': policy_rows,
        'query_policy_sha256': hashlib.sha256(module._canonical_json_bytes(policy_rows)).hexdigest(),
        'symbolic_dp_state': None,
        'symbolic_dp_sha256': None,
        'reachable_ordinary_verdicts': [5],
        'envelope_rows': [],
        'envelope_rows_sha256': hashlib.sha256(module._canonical_json_bytes([])).hexdigest(),
    }
    with pytest.raises(ValueError, match='complete exact ordered domain'):
        module.validate_gate_variant_ledger(plan, ledger)
    bad_order = deepcopy(ledger)
    bad_order['query_policy_rows'].reverse()
    bad_order['query_policy_sha256'] = hashlib.sha256(
        module._canonical_json_bytes(bad_order['query_policy_rows'])
    ).hexdigest()
    with pytest.raises(ValueError, match='ordered'):
        module.validate_gate_variant_ledger(plan, bad_order)
    stored = deepcopy(ledger)
    stored['stored_verdict'] = 5
    with pytest.raises(ValueError, match='schema|stored verdict'):
        module.validate_gate_variant_ledger(plan, stored)

    cases = list(islice(module.iter_expected_prerequisite_cases(plan), 2))
    records = []
    for case in cases:
        case_input = json.loads(case['canonical_input_bytes'].decode('ascii'))
        authority_path, authority_sha = sorted(module.EXPECTED_AUTHORITY.items())[
            case_input['ordinal']
        ]
        output = {
            'schema_version': 'AUTHORITY_HASH_OUTPUT_V1',
            'path': authority_path,
            'expected_sha256': authority_sha,
            'actual_sha256': module._sha256(module.REPO_ROOT / authority_path),
        }
        output_bytes = module._canonical_json_bytes(output)
        producer_id = case['expected_producer_ids'][0]
        records.append({
            'schema_version': 'PREREQUISITE_CASE_RECORD_V1',
            'case_id': case['case_id'],
            'case_kind': case['case_kind'],
            'scope_id': case['scope_id'],
            'canonical_input_bytes': case['canonical_input_bytes'],
            'input_sha256': case['input_sha256'],
            'producer_records': [{
                'producer_id': producer_id,
                'producer_function': producer_id.lower(),
                'code_path_sha256': '1' * 64,
                'call_count': 1,
                'output_schema_id': 'AUTHORITY_HASH_OUTPUT_V1',
                'canonical_output_bytes': output_bytes,
                'output_sha256': hashlib.sha256(output_bytes).hexdigest(),
                'pre_read_order_receipt_bytes': None,
                'pre_read_order_receipt_sha256': None,
            }],
        })
    packet = {
        'schema_version': 'GATE_PREREQUISITE_PACKET_V1',
        'execution_plan_sha256': plan_sha,
        'authority_receipts': records,
        'bank_receipts': [],
        'arm_coverage_receipts': [],
        'ablation_semantic_records': [],
        'property_records': [],
        'invariance_records': [],
        'leakage_records': [],
        'amortized_records': [],
        'replay_records': [],
        'independent_recompute_records': [],
    }
    assert module._validate_bounded_prerequisite_packet_prefix_non_evidence(plan, packet) == packet
    with pytest.raises(ValueError, match='complete formal prerequisite packet'):
        module.validate_gate_prerequisite_packet(plan, packet)
    missing = deepcopy(packet)
    missing['authority_receipts'] = missing['authority_receipts'][1:]
    with pytest.raises(ValueError, match='ordered prerequisite prefix mismatch'):
        module._validate_bounded_prerequisite_packet_prefix_non_evidence(plan, missing)
    extra = deepcopy(packet)
    extra['stored_verdict'] = 5
    with pytest.raises(ValueError, match='schema|stored verdict'):
        module._validate_bounded_prerequisite_packet_prefix_non_evidence(plan, extra)



def test_fix_round2c3b2a_all_generator_boundaries_and_alias_grouping() -> None:
    from itertools import islice

    module = _load_module()
    plan = module.build_gate_execution_plan()
    generators = plan['prerequisite_case_plan']['generator_rows']
    assert len(generators) == 31
    closed_input_keys = {
        'schema_version', 'generator_id', 'case_kind', 'scope_id',
        'canonical_bank_sha256', 'role_ids', 'arm_ids', 'target_mapping',
        'variant_id', 'transformation_id', 'public_state_key', 'ordinal',
    }
    for generator in generators:
        descriptor = generator['dimension_descriptor']
        assert set(descriptor) == {'schema_version', 'generator_id', 'dimensions'}
        assert descriptor['schema_version'] == 'COMPACT_GATE_GENERATOR_DESCRIPTOR_V2'
        assert descriptor['generator_id'] == generator['generator_id']
        assert [row['dimension_key'] for row in descriptor['dimensions']] == (
            generator['dimension_keys']
        )
        assert all(
            set(row) == {'dimension_key', 'domain_id'}
            and isinstance(row['domain_id'], str) and row['domain_id']
            for row in descriptor['dimensions']
        )
        samples = list(islice(module._iter_generator_cases(plan, generator), 2))
        assert len(samples) == min(2, generator['expected_count']), generator['generator_id']
        semantic_tuples = []
        for expected_ordinal, sample in enumerate(samples):
            decoded = json.loads(sample['canonical_input_bytes'].decode('utf-8'))
            assert set(decoded) == closed_input_keys
            assert decoded['generator_id'] == generator['generator_id']
            assert decoded['case_kind'] == generator['case_kind']
            assert decoded['scope_id'] == generator['scope_id']
            assert decoded['ordinal'] == expected_ordinal
            assert sample['input_sha256'] == hashlib.sha256(
                sample['canonical_input_bytes']
            ).hexdigest()
            semantic_tuples.append(tuple(
                json.dumps(decoded[key], sort_keys=True, separators=(',', ':'))
                for key in generator['dimension_keys']
            ))
        assert len(semantic_tuples) == len(set(semantic_tuples)), generator['generator_id']

    named_roles = {
        'HASH_00', 'B_SEPARABLE', 'B_COLLISION', 'B_DECOY',
        'B_BALANCED_MARGINAL',
    }
    named_group_hashes = {
        group['canonical_bank_sha256']
        for group in plan['bank_groups']
        if named_roles & set(group['role_ids'])
    }
    assert len(named_group_hashes) == 3
    token_row = next(
        row for row in generators if row['generator_id'] == 'GEN_INV_TOKEN_RELABEL'
    )
    prototype_row = next(
        row for row in generators if row['generator_id'] == 'GEN_INV_PROTOTYPE_RELABEL'
    )
    expected = 6 * len(named_group_hashes) * 3 * 120 * 120
    assert token_row['expected_count'] == expected
    assert prototype_row['expected_count'] == expected

    separable_group = next(
        group for group in plan['bank_groups'] if 'B_SEPARABLE' in group['role_ids']
    )
    assert {'HASH_00', 'B_SEPARABLE', 'B_DECOY'} <= set(separable_group['role_ids'])



def test_fix_round2c3b2a2_mixed_radix_first_transition_last_all_generators() -> None:
    module = _load_module()
    plan = module.build_gate_execution_plan()
    for generator in plan['prerequisite_case_plan']['generator_rows']:
        count = generator['expected_count']
        assert count > 0
        ordinals = sorted({0, min(1, count - 1), count // 2, count - 1})
        rows = [
            module._generator_case_at_ordinal_non_evidence(
                plan, generator, ordinal,
            )
            for ordinal in ordinals
        ]
        assert len({row['case_id'] for row in rows}) == len(rows)
        semantic_tuples = []
        for ordinal, row in zip(ordinals, rows):
            decoded = json.loads(row['canonical_input_bytes'].decode('utf-8'))
            assert decoded['ordinal'] == ordinal
            assert row['input_sha256'] == hashlib.sha256(
                row['canonical_input_bytes']
            ).hexdigest()
            assert {
                key for key, value in decoded.items()
                if value is not None
            } == module._generator_expected_nonnull_input_fields(
                generator['generator_id']
            )
            semantic_tuples.append(tuple(
                json.dumps(decoded[key], sort_keys=True, separators=(',', ':'))
                for key in generator['dimension_keys']
            ))
        assert len(semantic_tuples) == len(set(semantic_tuples))

        iterator = module._iter_generator_cases(plan, generator)
        assert next(iterator) == rows[0]
        if count > 1:
            assert next(iterator) == module._generator_case_at_ordinal_non_evidence(
                plan, generator, 1,
            )
        with pytest.raises(ValueError, match='generator ordinal'):
            module._generator_case_at_ordinal_non_evidence(plan, generator, count)


def test_fix_round2c3b2b1_symbolic_relation_primitives() -> None:
    module = _load_module()
    bank_hash = '0' * 64
    roles = ['HASH_00']

    identity = module._local_contribution_identity_non_evidence(bank_hash, roles)
    assert identity['schema_version'] == 'GATE_LOCAL_CONTRIBUTION_V1'
    assert identity['canonical_bank_sha256'] == bank_hash
    assert identity['role_ids'] == roles
    assert [row['control_arm_id'] for row in identity['control_relations']] == list(
        module._invalidating_control_ids()
    )

    left_contribution = deepcopy(identity)
    right_contribution = deepcopy(identity)
    left_contribution['conservative_member_full_all'] = False
    left_contribution['control_relations'][0]['full_no_worse_all'] = False
    right_contribution['active_delete_witness_seen'] = True
    right_contribution['control_relations'][0]['strict_witness_seen'] = True
    merged = module._merge_local_contributions_non_evidence(
        left_contribution, right_contribution,
    )
    assert merged['conservative_member_full_all'] is False
    assert merged['active_delete_witness_seen'] is True
    assert merged['control_relations'][0]['full_no_worse_all'] is False
    assert merged['control_relations'][0]['strict_witness_seen'] is True

    wrong_bank = deepcopy(identity)
    wrong_bank['canonical_bank_sha256'] = '1' * 64
    with pytest.raises(ValueError, match='bank identity'):
        module._merge_local_contributions_non_evidence(identity, wrong_bank)

    tie = module._min_fill_selection_non_evidence(
        ['b', 'a', 'c'], [['b', 'c'], ['a', 'c']],
    )
    assert tie == {
        'variable_key': 'a',
        'selection_key': [0, 1, 'a'],
        'neighbors': ['c'],
    }
    missing_edges_first = module._min_fill_selection_non_evidence(
        ['a', 'b', 'c', 'd'], [['a', 'b', 'c'], ['b', 'd'], ['c', 'd']],
    )
    assert missing_edges_first['variable_key'] == 'a'
    assert missing_edges_first['selection_key'] == [0, 2, 'a']

    def contribution(*, full_all: bool = True, active_seen: bool = False):
        value = module._local_contribution_identity_non_evidence(bank_hash, roles)
        value['conservative_member_full_all'] = full_all
        value['active_delete_witness_seen'] = active_seen
        return value

    left_factor = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 1}, contribution(full_all=False)),
    ])
    incompatible_factor = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 2}, contribution(active_seen=True)),
    ])
    incompatible, incompatible_trace = module._join_relation_factors_non_evidence(
        left_factor, incompatible_factor,
    )
    assert incompatible['scope_variable_keys'] == ['x']
    assert incompatible['relation_rows'] == []
    assert incompatible_trace == []

    compatible_factor = module._relation_factor_non_evidence([
        module._relation_row_non_evidence(
            {'x': 1, 'y': 2}, contribution(active_seen=True),
        ),
    ])
    compatible, compatible_trace = module._join_relation_factors_non_evidence(
        left_factor, compatible_factor,
    )
    assert compatible['scope_variable_keys'] == ['x', 'y']
    assert len(compatible['relation_rows']) == 1
    compatible_value = json.loads(
        compatible['relation_rows'][0]['contribution_bytes'].decode('ascii')
    )
    assert compatible_value['conservative_member_full_all'] is False
    assert compatible_value['active_delete_witness_seen'] is True
    assert len(compatible_trace) == 1
    assert set(json.loads(compatible_trace[0]['joined_row_bytes'].decode('ascii'))) == {
        'scope_variable_keys', 'assignment_bytes', 'contribution_bytes',
        'contribution_sha256',
    }

    alternatives = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 1}, contribution(full_all=False)),
        module._relation_row_non_evidence({'x': 2}, contribution(active_seen=True)),
    ])
    projected, elimination_trace = module._eliminate_relation_variable_non_evidence(
        alternatives, 'x',
    )
    assert projected['scope_variable_keys'] == []
    assert len(projected['relation_rows']) == 2
    assert len(elimination_trace) == 2
    projected_values = {
        row['contribution_bytes'] for row in projected['relation_rows']
    }
    assert len(projected_values) == 2  # union, not an AND/OR merge

    duplicates = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 1}, contribution()),
        module._relation_row_non_evidence({'x': 2}, contribution(active_seen=True)),
        module._relation_row_non_evidence({'x': 3}, contribution()),
    ])
    deduplicated, _ = module._eliminate_relation_variable_non_evidence(
        duplicates, 'x',
    )
    assert len(deduplicated['relation_rows']) == 2  # A,B,A -> {A,B}

    chain_result = module._eliminate_factor_graph_non_evidence(
        [left_factor, compatible_factor], ['x', 'y'],
    )
    assert [
        row['eliminated_variable_key'] for row in chain_result['ve_trace_rows']
    ] == ['x', 'y']
    assert chain_result['output_factor']['scope_variable_keys'] == []
    assert len(chain_result['output_factor']['relation_rows']) == 1
    for ordinal, row in enumerate(chain_result['ve_trace_rows']):
        assert row['step_ordinal'] == ordinal
        assert hashlib.sha256(row['output_factor_bytes']).hexdigest() == (
            row['output_factor_sha256']
        )

    def edge_factor(left_key: str, right_key: str):
        return module._relation_factor_non_evidence([
            module._relation_row_non_evidence(
                {left_key: 0, right_key: 0}, contribution(),
            ),
        ])

    k22 = module._eliminate_factor_graph_non_evidence([
        edge_factor('a', 'c'), edge_factor('a', 'd'),
        edge_factor('b', 'c'), edge_factor('b', 'd'),
    ], ['d', 'c', 'b', 'a'])
    assert [
        row['eliminated_variable_key'] for row in k22['ve_trace_rows']
    ] == ['a', 'b', 'c', 'd']

    domains = {'x': [0, 1], 'y': [0, 1], 'p': [0, 1], 'z': [0, 1]}

    def ternary_cell(assignment):
        value = contribution()
        value['active_delete_witness_seen'] = assignment['p'] == 1
        return value

    ternary = module._relation_factor_from_callable_non_evidence(
        ['p', 'x', 'y'], domains, ternary_cell,
    )
    assert ternary['scope_variable_keys'] == ['p', 'x', 'y']
    fixed_xy = {}
    for row in ternary['relation_rows']:
        assignment = json.loads(row['assignment_bytes'].decode('ascii'))
        assignment = {item['variable_key']: item['query_token'] for item in assignment}
        if assignment['x'] == assignment['y'] == 0:
            fixed_xy[assignment['p']] = row['contribution_sha256']
    assert len(set(fixed_xy.values())) == 2
    with pytest.raises(ValueError, match='undeclared leaf'):
        module._relation_factor_from_callable_non_evidence(
            ['x', 'y'], domains, ternary_cell,
        )

    def omitted_z_cell(assignment):
        value = contribution()
        value['local_delete_witness_seen'] = assignment['z'] == 1
        return value

    with pytest.raises(ValueError, match='undeclared leaf'):
        module._relation_factor_from_callable_non_evidence(
            ['p', 'x', 'y'], domains, omitted_z_cell,
        )

    bank_one_identity = module._local_contribution_identity_non_evidence(
        '1' * 64, ['HASH_01'],
    )
    bank_one_negative = deepcopy(bank_one_identity)
    bank_one_negative['conservative_member_full_all'] = False
    bank_two_identity = module._local_contribution_identity_non_evidence(
        '2' * 64, ['HASH_02'],
    )
    outer = module._outer_gate_dp_non_evidence([
        {
            'canonical_bank_sha256': '2' * 64,
            'local_contributions': [bank_two_identity],
        },
        {
            'canonical_bank_sha256': '1' * 64,
            'local_contributions': [bank_one_identity, bank_one_negative],
        },
    ])
    assert len(outer['transition_rows']) == 4
    assert len(outer['terminal_state_rows']) == 2
    assert outer['reachable_ordinary_verdicts'] == [6, 8]


def test_fix_round2c3b2b2_real_factor_layer_and_nine_equivalence_rows() -> None:
    module = _load_module()
    plan = module.build_gate_execution_plan()
    receipt = module._small_instance_equivalence_receipt_non_evidence()
    suite = plan['small_instance_equivalence_suite']
    assert len(suite) == 9
    assert [(row['median_convention'], row['bank_count']) for row in suite] == [
        (median, count)
        for median in ('lower', 'midpoint_integer', 'upper')
        for count in (1, 2, 3)
    ]
    assert all(row['leaf_variable_keys'] for row in suite)
    assert all(row['toy_instance_sha256'] != hashlib.sha256(
        module._canonical_json_bytes({
            'schema_version': 'TOY_FACTOR_INSTANCE_V1',
            'median_convention': row['median_convention'],
            'bank_group_sha256s': [],
            'leaf_variable_rows': [],
            'factor_rows': [],
        })
    ).hexdigest() for row in suite)
    assert receipt['schema_version'] == 'SMALL_INSTANCE_EQUIVALENCE_RECEIPT_NON_EVIDENCE_V1'
    assert receipt['eligible_bank_counts_by_median'] == {
        'lower': 3, 'midpoint_integer': 3, 'upper': 3,
    }
    assert receipt['suite_sha256'] == plan[
        'small_instance_equivalence_suite_sha256'
    ]
    assert receipt['all_nine_equivalent'] is True
    assert 2 <= receipt['maximum_factor_scope_size'] <= 3
    assert receipt['maximum_factor_table_rows'] <= 64
    assert receipt['explicit_oracle_called_ve_helpers'] is False

    first = receipt['selected_bank_layers_by_median']['lower'][0]
    assert len(first['retained_leaf_variable_rows']) == 3
    assert len(first['retained_factor_rows']) >= 2
    f0, f1 = first['retained_factor_rows'][:2]
    assert len(f0['scope_variable_keys']) == 2
    assert len(f1['scope_variable_keys']) == 2
    assert len(set(f0['scope_variable_keys']) & set(f1['scope_variable_keys'])) == 1
    assert len(set(f0['scope_variable_keys']) | set(f1['scope_variable_keys'])) == 3
    assert first['compatible_pair_seen'] is True
    assert first['incompatible_pair_seen'] is True
    assert first['distinct_partial_contribution_count'] >= 2

    ternary = next(
        descriptor
        for descriptor in first['authority_factor_descriptors']
        if descriptor['factor_kind'] == 'TERNARY_GATE'
        and descriptor['gate_ids'] in (
            ['CAUSAL_EFFECT:ABL_NO_UPDATE'],
            ['CAUSAL_EFFECT:ABL_QUERY_OUTCOME_MASK'],
        )
    )
    assert module.PUBLIC_ARM_ID in {
        key.split('\x1f')[1] for key in ternary['scope_variable_keys']
    }
    separable_bank = next(
        row for row in plan['bank_groups'] if 'B_SEPARABLE' in row['role_ids']
    )
    separable_descriptors = module._real_factor_descriptors_non_evidence(
        separable_bank, 'lower',
    )
    assert any(
        row['gate_ids'] == ['PROPERTY_B_SEPARABLE']
        and row['factor_kind'] == 'UNARY_GATE'
        for row in separable_descriptors
    )


def test_fix_round2c3b2b2_r1_source_delete_and_fixed_first_f1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()

    # The source-delete factor must exercise the registered ablation producer;
    # comparing two direct PUBLIC calls is a tautology and cannot detect a
    # disconnected registered transform.
    bank_row = next(
        row for row in module._gate_bank_groups() if 'HASH_00' in row['role_ids']
    )
    target = tuple(bank_row['canonical_member'])
    c = module._frozen_design()['arm_registry']['primary_conservative']
    p = module.PUBLIC_ARM_ID
    c_key = module._leaf_variable_key_non_evidence(
        bank_row['canonical_bank_sha256'], c, target[0],
    )
    p_key = module._leaf_variable_key_non_evidence(
        bank_row['canonical_bank_sha256'], p, target[0],
    )
    descriptor = {
        'factor_id': '0' * 64,
        'factor_kind': 'PAIR_GATE',
        'canonical_bank_sha256': bank_row['canonical_bank_sha256'],
        'role_id': 'HASH_00',
        'target_mapping': list(target),
        'h1_outcome': None,
        'gate_ids': ['SOURCE_DELETE'],
        'scope_variable_keys': sorted([c_key, p_key]),
        'left_arm_id': c,
        'right_arm_id': p,
    }

    def fake_metric(_context, arm_id, _target, _candidate, _public):
        full = 0 if arm_id == p else -100000
        return {
            'metric_rationals': {
                'candidate_full_endpoint_mae': module._rational(full),
                'common_unqueried_forward_improvement': module._rational(0),
                'same_history_forward_improvement': module._rational(0),
            },
        }

    monkeypatch.setattr(module, '_factor_metric_non_evidence', fake_metric)
    monkeypatch.setattr(
        module, '_run_live_semantic_trace', lambda *args, **kwargs: ({}, {}),
    )

    def registered_spy(*args, **kwargs):
        raise RuntimeError('registered-source-delete-spy')

    monkeypatch.setattr(module, 'execute_registered_ablation', registered_spy)
    with pytest.raises(RuntimeError, match='registered-source-delete-spy'):
        module._factor_cell_contribution_non_evidence(
            descriptor,
            {c_key: 1, p_key: 1},
            bank_row,
            'lower',
            {'bank': tuple(map(tuple, bank_row['canonical_bank'])),
             'median': 'lower', 'metrics': {}},
        )

    # F1 is the fixed first structurally compatible descriptor. If that exact
    # pair fails the frozen table receipt, the bank is ineligible; the selector
    # may not skip to a later passing F1.
    def factor_descriptor(fid, scope):
        return {
            'factor_id': fid * 64,
            'factor_kind': 'PAIR_GATE',
            'canonical_bank_sha256': 'a' * 64,
            'role_id': 'HASH_00',
            'target_mapping': [0, 1, 2, 3, 4],
            'h1_outcome': None,
            'gate_ids': ['MEMBER_FORWARD_CONSERVATIVE'],
            'scope_variable_keys': scope,
            'left_arm_id': c,
            'right_arm_id': p,
        }

    descriptors = [
        factor_descriptor('0', ['bank\x1farm0\x1f0', 'bank\x1farm1\x1f0']),
        factor_descriptor('1', ['bank\x1farm0\x1f0', 'bank\x1farm2\x1f0']),
        factor_descriptor('2', ['bank\x1farm1\x1f0', 'bank\x1farm2\x1f0']),
    ]
    monkeypatch.setattr(
        module, '_real_factor_descriptors_non_evidence',
        lambda _bank, _median: deepcopy(descriptors),
    )
    monkeypatch.setattr(
        module, '_leaf_variable_row_non_evidence',
        lambda bank, arm, outcome, median: {
            'variable_key': f'bank\x1f{arm}\x1f{outcome}',
            'canonical_bank_sha256': 'a' * 64,
            'arm_id': arm,
            'h1_outcome': int(outcome),
            'domain_tokens': [1, 2],
        },
    )

    def fake_factor(desc, *_args):
        return {
            **{key: deepcopy(desc[key]) for key in (
                'factor_id', 'factor_kind', 'canonical_bank_sha256', 'role_id',
                'target_mapping', 'h1_outcome', 'gate_ids',
                'scope_variable_keys',
            )},
            'table_rows': [],
            'factor_sha256': desc['factor_id'],
        }

    monkeypatch.setattr(module, '_build_real_factor_non_evidence', fake_factor)
    monkeypatch.setattr(
        module, '_compatibility_receipt_non_evidence',
        lambda left, right: {
            'compatible_pair_seen': True,
            'incompatible_pair_seen': True,
            'distinct_partial_contribution_count': (
                1 if right['factor_id'] == '1' * 64 else 2
            ),
        },
    )
    assert module._eligible_bank_motif_non_evidence({
        'canonical_bank_sha256': 'a' * 64,
        'canonical_bank': [[0, 1, 2, 3, 4]],
        'role_ids': ['HASH_00'],
        'canonical_member': [0, 1, 2, 3, 4],
        'target_mappings': [list(row) for row in module.mapping_space()],
    }, 'lower') is None


def test_fix_round2c3b2b2_r1_ve_uses_complete_input_factor_hash_order() -> None:
    module = _load_module()
    contribution = module._local_contribution_identity_non_evidence(
        'a' * 64, ['HASH_00'],
    )
    left = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 0}, contribution),
    ], ['x'])
    right_contribution = deepcopy(contribution)
    right_contribution['active_delete_witness_seen'] = True
    right = module._relation_factor_non_evidence([
        module._relation_row_non_evidence({'x': 0}, right_contribution),
    ], ['x'])
    result = module._eliminate_factor_graph_non_evidence(
        [left, right], ['x'],
        factor_sha256s=['f' * 64, '0' * 64],
    )
    step = result['ve_trace_rows'][0]
    assert step['input_factor_sha256s'] == ['0' * 64, 'f' * 64]
    assert step['join_trace_rows'][0]['left_factor_sha256'] == '0' * 64
    assert step['join_trace_rows'][0]['right_factor_sha256'] == 'f' * 64


def test_fix_round2c3b2c1_ledger_rows_are_lexical_deep_and_nonempty() -> None:
    module = _load_module()
    plan = module.build_gate_execution_plan()
    bank_row = next(
        row for row in plan['bank_groups'] if row['role_ids'] == ['HASH_07']
    )
    bank = tuple(map(tuple, bank_row['canonical_bank']))
    arm_id = 'ARM_I_CONSISTENCY__A_EIG__D_L1_MEDIAN'
    decisions = [
        module.query_decision(
            arm_id, bank,
            [{'token_index': 0, 'prototype_index': outcome}],
            median_convention='lower',
        )
        for outcome in range(5)
    ]
    assert decisions[0]['minimizing_tokens'] == [1, 2, 3, 4]
    row = {
        'canonical_bank_sha256': bank_row['canonical_bank_sha256'],
        'arm_id': arm_id,
        'choices_by_h1_outcome': [item['selected_token'] for item in decisions],
    }
    assert module._validate_query_policy_row_non_evidence(
        plan, row, median_convention='lower',
    ) == row
    nonlexical = deepcopy(row)
    nonlexical['choices_by_h1_outcome'][0] = 2
    with pytest.raises(ValueError, match='lexical'):
        module._validate_query_policy_row_non_evidence(
            plan, nonlexical, median_convention='lower',
        )

    target = tuple(bank_row['target_mappings'][0])
    envelope = {
        'schema_version': 'VERIFIER_PRIVATE_ENVELOPE_V1',
        'bank_role_ids': list(bank_row['role_ids']),
        'canonical_bank_sha256': bank_row['canonical_bank_sha256'],
        'target_mapping': list(target),
        **module.classify_target(bank, target),
        'scorer_truth': [
            list(module._prototype_table()[target[token]]) for token in range(5)
        ],
        'metric_rows': [module.evaluate_target(
            bank, target, arm_id, median_convention='lower',
            query_policy={
                'candidate': row['choices_by_h1_outcome'][target[0]],
                'public': None,
            },
        )],
        'artifact_receipts': [],
    }
    assert module._validate_envelope_row_non_evidence(
        plan, envelope,
        expected_bank_row=bank_row,
        expected_target_mapping=list(target),
        expected_arm_id=arm_id,
        median_convention='lower',
        query_policy_rows={
            (bank_row['canonical_bank_sha256'], arm_id): row,
        },
    ) == envelope
    with pytest.raises(ValueError, match='envelope'):
        module._validate_envelope_row_non_evidence(
            plan, {},
            expected_bank_row=bank_row,
            expected_target_mapping=list(target),
            expected_arm_id=arm_id,
            median_convention='lower',
            query_policy_rows={
                (bank_row['canonical_bank_sha256'], arm_id): row,
            },
        )

    lexical = {
        'variant_id': 'MEDIAN_LOWER__LEXICAL',
        'median_convention': 'lower',
        'variant_kind': 'lexical',
        'query_policy_sha256': '1' * 64,
        'envelope_rows_sha256': '2' * 64,
        'symbolic_dp_sha256': None,
    }
    symbolic = {
        'variant_id': 'MEDIAN_LOWER__SYMBOLIC_GLOBAL_POLICY_DP_V1',
        'median_convention': 'lower',
        'variant_kind': 'symbolic_global_policy_dp_v1',
        'query_policy_sha256': '1' * 64,
        'envelope_rows_sha256': '2' * 64,
        'symbolic_dp_sha256': '3' * 64,
    }
    with pytest.raises(ValueError, match='exact six'):
        module._validate_ledger_collection_headers_non_evidence(
            plan, [lexical, symbolic],
        )
    headers = []
    for variant in plan['variant_registry']:
        template = lexical if variant['variant_kind'] == 'lexical' else symbolic
        header = deepcopy(template)
        header.update(variant)
        headers.append(header)
    assert module._validate_ledger_collection_headers_non_evidence(
        plan, headers,
    ) == headers
    drift = deepcopy(headers)
    drift[1]['envelope_rows_sha256'] = '4' * 64
    with pytest.raises(ValueError, match='same-median lexical anchor'):
        module._validate_ledger_collection_headers_non_evidence(plan, drift)

    identity = module._global_state_identity_non_evidence()
    identity_bytes = module._canonical_json_bytes(identity)
    identity_branch = module._terminal_ordinary_branch_non_evidence(identity)
    symbolic_state = {
        'schema_version': 'GATE_SYMBOLIC_QUERY_DP_V1',
        'median_convention': 'lower',
        'leaf_variable_rows': [{}],
        'factor_rows': [{}],
        've_trace_rows': [{}],
        'local_state_rows': [{}],
        'transition_rows': [{}],
        'initial_state_bytes': identity_bytes.decode('ascii'),
        'initial_state_sha256': hashlib.sha256(identity_bytes).hexdigest(),
        'terminal_state_rows': [{
            'state_bytes': identity_bytes.decode('ascii'),
            'state_sha256': hashlib.sha256(identity_bytes).hexdigest(),
            'ordinary_branch': identity_branch,
        }],
        'reachable_ordinary_verdicts': [identity_branch],
        'equivalence_suite_sha256': plan[
            'small_instance_equivalence_suite_sha256'
        ],
    }
    symbolic_ledger = {
        'median_convention': 'lower',
        'reachable_ordinary_verdicts': [identity_branch],
    }
    with pytest.raises(ValueError, match='leaf variable'):
        module._validate_symbolic_dp_state_non_evidence(
            plan, symbolic_ledger, symbolic_state,
        )


def test_fix_round2c3b2c2_packet_outputs_are_closed_and_preread_is_linked() -> None:
    module = _load_module()
    plan = module.build_gate_execution_plan()
    plan_sha = hashlib.sha256(module._canonical_json_bytes(plan)).hexdigest()

    def empty_packet():
        return {
            'schema_version': 'GATE_PREREQUISITE_PACKET_V1',
            'execution_plan_sha256': plan_sha,
            **{name: [] for name in module._PACKET_COLLECTIONS},
        }

    bank_case = next(module._iter_collection_cases(plan, 'bank_receipts'))
    bank_input = json.loads(bank_case['canonical_input_bytes'].decode('ascii'))
    bank_row = next(
        row for row in plan['bank_groups']
        if row['canonical_bank_sha256'] == bank_input['canonical_bank_sha256']
    )
    bank_output = {
        'schema_version': 'BANK_COVERAGE_OUTPUT_V1',
        **deepcopy(bank_row),
    }

    def record(case, producer_id, output_schema_id, output):
        output_bytes = module._canonical_json_bytes(output)
        return {
            'schema_version': 'PREREQUISITE_CASE_RECORD_V1',
            'case_id': case['case_id'],
            'case_kind': case['case_kind'],
            'scope_id': case['scope_id'],
            'canonical_input_bytes': case['canonical_input_bytes'],
            'input_sha256': case['input_sha256'],
            'producer_records': [{
                'producer_id': producer_id,
                'producer_function': producer_id.lower(),
                'code_path_sha256': '1' * 64,
                'call_count': 1,
                'output_schema_id': output_schema_id,
                'canonical_output_bytes': output_bytes,
                'output_sha256': hashlib.sha256(output_bytes).hexdigest(),
                'pre_read_order_receipt_bytes': None,
                'pre_read_order_receipt_sha256': None,
            }],
        }

    packet = empty_packet()
    packet['bank_receipts'] = [record(
        bank_case, 'BANK_CONSTRUCTOR_RECOMPUTE',
        'BANK_COVERAGE_OUTPUT_V1', bank_output,
    )]
    assert module._validate_bounded_prerequisite_packet_prefix_non_evidence(
        plan, packet,
    ) == packet
    malformed = deepcopy(packet)
    malformed_output = module._canonical_json_bytes({})
    malformed['bank_receipts'][0]['producer_records'][0].update({
        'canonical_output_bytes': malformed_output,
        'output_sha256': hashlib.sha256(malformed_output).hexdigest(),
    })
    with pytest.raises(ValueError, match='bank coverage output schema'):
        module._validate_bounded_prerequisite_packet_prefix_non_evidence(
            plan, malformed,
        )
    wrong_function = deepcopy(packet)
    wrong_function['bank_receipts'][0]['producer_records'][0][
        'producer_function'
    ] = 'arbitrary_callable'
    with pytest.raises(ValueError, match='producer function'):
        module._validate_bounded_prerequisite_packet_prefix_non_evidence(
            plan, wrong_function,
        )

    fresh_case = next(module._iter_collection_cases(plan, 'replay_records'))
    fresh_input = json.loads(fresh_case['canonical_input_bytes'].decode('ascii'))
    fresh_bank = next(
        row for row in plan['bank_groups']
        if row['canonical_bank_sha256'] == fresh_input['canonical_bank_sha256']
    )
    median = next(
        row['median_convention'] for row in plan['variant_registry']
        if row['variant_id'] == fresh_input['variant_id']
    )
    child = module.evaluate_target(
        tuple(map(tuple, fresh_bank['canonical_bank'])),
        fresh_input['target_mapping'], fresh_input['arm_ids'][0],
        median_convention=median,
    )
    child_bytes = module._canonical_json_bytes(child)
    recompute_output = {
        'schema_version': 'RECOMPUTE_OUTPUT_V1',
        'recompute_kind': 'TRAJECTORY_ROW',
        'case_key': fresh_case['case_id'],
        'canonical_row_or_aggregate_bytes': child_bytes.decode('ascii'),
    }
    fresh_record = record(
        fresh_case, 'FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE',
        'RECOMPUTE_OUTPUT_V1', recompute_output,
    )
    receipt = {
        'producer_id': 'FRESH_PROCESS_TRAJECTORY_ROW_RECOMPUTE',
        'input_sha256': fresh_case['input_sha256'],
        'recompute_start_ordinal': 0,
        'recompute_complete_ordinal': 2,
        'stored_bundle_read_ordinal': 1,
        'recomputed_output_sha256': hashlib.sha256(child_bytes).hexdigest(),
        'stored_bundle_sha256': hashlib.sha256(child_bytes).hexdigest(),
    }
    receipt_bytes = module._canonical_json_bytes(receipt)
    fresh_record['producer_records'][0].update({
        'pre_read_order_receipt_bytes': receipt_bytes,
        'pre_read_order_receipt_sha256': hashlib.sha256(receipt_bytes).hexdigest(),
    })
    replay_packet = empty_packet()
    replay_packet['replay_records'] = [fresh_record]
    with pytest.raises(ValueError, match='start < complete < stored'):
        module._validate_bounded_prerequisite_packet_prefix_non_evidence(
            plan, replay_packet,
        )


def test_fix_round2c3b2c3_public_reducer_fails_closed_without_synthetic_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    calls = []
    plan = {'sentinel': 'plan'}
    ledgers = [{'sentinel': index} for index in range(6)]
    packet = {'sentinel': 'packet'}

    monkeypatch.setattr(
        module, 'validate_gate_execution_plan',
        lambda value: calls.append(('plan', value)) or value,
    )
    monkeypatch.setattr(
        module, '_validate_ledger_collection_headers_non_evidence',
        lambda validated_plan, values: calls.append(('headers', values)) or values,
    )
    monkeypatch.setattr(
        module, 'validate_gate_variant_ledger',
        lambda validated_plan, value: calls.append(('ledger', value)) or value,
    )
    monkeypatch.setattr(
        module, '_validate_bounded_prerequisite_packet_prefix_non_evidence',
        lambda validated_plan, value: calls.append(('packet', value)) or value,
    )

    def forbidden_synthetic():
        raise AssertionError('evidence reducer called synthetic truth table')

    monkeypatch.setattr(
        module, '_synthetic_dispatch_truth_table_non_evidence',
        forbidden_synthetic,
    )
    with pytest.raises(module.FormalRunNotAuthorized, match='I2'):
        module.reduce_gate_evidence(plan, ledgers, packet)
    assert [name for name, _ in calls] == [
        'plan', 'headers', *(['ledger'] * 6), 'packet',
    ]


def test_fix_round2c3b2c3_dispatch_recomputes_closed_priority() -> None:
    module = _load_module()
    verdict_by_branch = {
        5: 'ACTIVE_TRANSFER_RAW_UPSIDE_WITH_UNCONTROLLED_TAIL',
        6: 'ACTIVE_TRANSFER_CONSERVATIVE_SELECTION_FAILED',
        7: 'ACTIVE_TRANSFER_NO_TWO_SIDED_HEADROOM',
        8: 'ACTIVE_TRANSFER_CAUSAL_ATTRIBUTION_FAILED',
        9: 'ACTIVE_TRANSFER_BOUNDED_REGRET_ONLY',
        10: 'ACTIVE_TRANSFER_OBSERVATION_OR_LOOKUP_SATURATED',
        11: 'ACTIVE_TRANSFER_STATIC_REFERENCE_FEASIBLE',
    }

    def fixture():
        facts = next(
            row for row in module._synthetic_dispatch_truth_table_non_evidence()['rows']
            if row['ordinary_branch'] == 11
        )
        control_id = module._invalidating_control_ids()[0]
        return {
            'schema_version': 'GATE_REDUCTION_V1',
            'execution_plan_sha256': '0' * 64,
            'variant_ledger_sha256s': [str(index) * 64 for index in range(1, 7)],
            'prerequisite_packet_sha256': '7' * 64,
            'coverage_summary': {
                'expected_case_count': 0,
                'observed_case_count': 0,
                'expected_case_id_digest': '8' * 64,
                'observed_case_id_digest': '8' * 64,
                'first_case_mismatch_ordinal': None,
                'expected_case_id_at_mismatch': None,
                'observed_case_id_at_mismatch': None,
                'expected_ledger_count': 6,
                'observed_ledger_count': 6,
                'missing_variant_ids': [],
                'extra_variant_ids': [],
                'duplicate_variant_ids': [],
            },
            'metric_extrema': [],
            'causal_effect_witnesses': [],
            'control_comparison_witnesses': [],
            'property_witnesses': [],
            'private_truth_leakage': False,
            'instrument_invalid': False,
            'raw_upside': facts['raw_upside'],
            'raw_bounded_safety': facts['raw_bounded_safety'],
            'conservative_member_and_forward': facts['conservative_member_and_forward'],
            'conservative_bounded_safety': facts['conservative_bounded_safety'],
            'conservative_strict_safety': facts['conservative_strict_safety'],
            'bounded_core': facts['bounded_core'],
            'strict_core': facts['strict_core'],
            'attribution_gate': facts['attribution_gate'],
            'bounded_joint': facts['bounded_joint'],
            'strict_joint': facts['strict_joint'],
            'pareto_match_arm_ids': [] if not facts['control_match'] else [control_id],
            'consistency_positive_non_equivalence': True,
            'control_match': facts['control_match'],
            'ordinary_branch_by_median': {
                median: facts['ordinary_branch']
                for median in ('lower', 'midpoint_integer', 'upper')
            },
            'median_sensitive': False,
            'query_sensitive': False,
            'ordinary_branch': facts['ordinary_branch'],
            'verdict': verdict_by_branch[facts['ordinary_branch']],
            'claim_ceiling': module._frozen_design()['claim_ceiling'],
        }

    reduction = fixture()
    assert module.dispatch_gate_reduction(reduction) == (
        'ACTIVE_TRANSFER_STATIC_REFERENCE_FEASIBLE'
    )
    priority_cases = [
        ('private_truth_leakage', 'ACTIVE_TRANSFER_PRIVATE_TRUTH_LEAKAGE'),
        ('instrument_invalid', 'ACTIVE_TRANSFER_INSTRUMENT_INVALID'),
        ('median_sensitive', 'ACTIVE_TRANSFER_MEDIAN_SELECTION_SENSITIVE'),
        ('query_sensitive', 'ACTIVE_TRANSFER_QUERY_TIE_SENSITIVE'),
    ]
    for field, verdict in priority_cases:
        active = fixture()
        active[field] = True
        if field == 'median_sensitive':
            active['ordinary_branch_by_median']['lower'] = 5
        active['verdict'] = verdict
        assert module.dispatch_gate_reduction(active) == verdict
    precedence = fixture()
    for field, _ in priority_cases:
        precedence[field] = True
    precedence['ordinary_branch_by_median']['lower'] = 5
    precedence['verdict'] = 'ACTIVE_TRANSFER_PRIVATE_TRUTH_LEAKAGE'
    assert module.dispatch_gate_reduction(precedence) == (
        'ACTIVE_TRANSFER_PRIVATE_TRUTH_LEAKAGE'
    )

    for branch, expected_verdict in verdict_by_branch.items():
        facts = next(
            row for row in module._synthetic_dispatch_truth_table_non_evidence()['rows']
            if row['ordinary_branch'] == branch
        )
        candidate = fixture()
        for key in module._ORDINARY_FACT_KEYS:
            candidate[key] = facts[key]
        for key in ('bounded_core', 'strict_core', 'bounded_joint', 'strict_joint'):
            candidate[key] = facts[key]
        candidate['ordinary_branch_by_median'] = {
            median: branch for median in ('lower', 'midpoint_integer', 'upper')
        }
        candidate['ordinary_branch'] = branch
        candidate['pareto_match_arm_ids'] = (
            [module._invalidating_control_ids()[0]]
            if facts['control_match'] else []
        )
        candidate['control_match'] = facts['control_match']
        candidate['verdict'] = expected_verdict
        assert module.dispatch_gate_reduction(candidate) == expected_verdict

    mismatch = fixture()
    mismatch['verdict'] = 'ACTIVE_TRANSFER_INSTRUMENT_INVALID'
    with pytest.raises(ValueError, match='stored verdict mismatch'):
        module.dispatch_gate_reduction(mismatch)
    extra = fixture()
    extra['evidence_eligible'] = True
    with pytest.raises(ValueError, match='schema drift'):
        module.dispatch_gate_reduction(extra)
