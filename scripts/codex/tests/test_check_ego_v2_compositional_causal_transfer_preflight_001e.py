from __future__ import annotations

import importlib.util
import ast
import base64
import json
from fractions import Fraction
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'check_ego_v2_compositional_causal_transfer_preflight_001e.py'
if not MODULE_PATH.exists():
    raise FileNotFoundError(f'Missing module: {MODULE_PATH}')
RECOMPUTE_MODULE_PATH = Path(__file__).resolve().parents[1] / 'recompute_ego_v2_compositional_causal_transfer_preflight_001e.py'

SPEC = importlib.util.spec_from_file_location('caot001e', MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def _load_recompute():
    if not RECOMPUTE_MODULE_PATH.exists():
        raise FileNotFoundError(f'Missing independent recompute module: {RECOMPUTE_MODULE_PATH}')
    spec = importlib.util.spec_from_file_location('caot001e_recompute', RECOMPUTE_MODULE_PATH)
    recompute = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(recompute)
    return recompute

TASK_CARD_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'codex' / 'tasks' / 'EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-IMPLEMENTATION-001E-I1.md'
AUTHORITY_CARD_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'codex' / 'tasks' / 'EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E.md'
COLLISION_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'codex' / 'tasks' / 'ego-v2-p1-compositional-causal-transfer-preflight-001e' / 'COLLISION_RECORD.md'
FROZEN_DESIGN_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'codex' / 'tasks' / 'ego-v2-p1-compositional-causal-transfer-preflight-001e' / 'FROZEN_DESIGN.json'


def _fixture_input(*, source_program: int = 0b0101010, target_program: int = 0b0101011) -> dict:
    source_table = module.build_source_truth_table(source_program)
    target_history = [
        {'composition': '000', 'outcome': module.evaluate_program(target_program, '000')['outcome']},
    ]
    return module.build_public_input(
        source_table=source_table,
        target_history=target_history,
        query_budget=1,
        arm_id='MIXTURE_BMA_ACTIVE_BRIER',
        serialized_state={'token': 'fixture-state'},
    )


def _aggregate_fixture(**overrides) -> dict:
    data = {
        'private_truth_leakage': False,
        'instrument_invalid': False,
        'query_tie_sensitive': False,
        'control_match': False,
        'complete_population': True,
        'fresh_replay_equal': True,
        'independent_recompute_equal': True,
        'leakage_positive_controls_rejected': True,
        'nominal_gain_pass': True,
        'exact_gain_pass': True,
        'local_gain_pass': True,
        'nonlocal_safety_pass': True,
        'scratch_heavy_gain_pass': True,
        'active_vs_best_fixed_pass': True,
        'unique_nonlexical_positive_forward_pass': True,
        'source_delete_pass': True,
        'local_delete_pass': True,
        'feedback_mask_pass': True,
        'active_delete_pass': True,
    }
    data.update(overrides)
    return data


def test_authority_hashes_match_and_design_parses():
    assert module.AUTHORITY_SHA256['001e_card'] == module.compute_sha256(AUTHORITY_CARD_PATH)
    assert module.AUTHORITY_SHA256['001e_collision'] == module.compute_sha256(COLLISION_PATH)
    assert module.AUTHORITY_SHA256['001e_design'] == module.compute_sha256(FROZEN_DESIGN_PATH)
    assert module.AUTHORITY_SHA256['001e_i1_card'] == module.compute_sha256(TASK_CARD_PATH)
    design = module.load_frozen_design()
    assert design['task_id'] == 'EGO-V2-P1-COMPOSITIONAL-CAUSAL-TRANSFER-PREFLIGHT-001E'
    broken = dict(design)
    broken.pop('verdict_priority')
    with pytest.raises(module.DesignValidationError):
        module.validate_design_schema(broken)


def test_all_programs_and_compositions_are_enumerated_with_exact_trace_shape():
    tables = {}
    for program_id in range(128):
        table = []
        for composition in module.iter_compositions():
            result = module.evaluate_program(program_id, composition)
            assert len(result['term_trace']) == 7
            assert set(result) >= {'program_id', 'composition', 'outcome', 'term_trace', 'cumulative_xor'}
            table.append(result['outcome'])
        tables[program_id] = tuple(table)
    assert len(tables) == 128
    assert len(set(tables.values())) == 128
    assert module.build_source_truth_table(0) == [
        {'composition': composition, 'outcome': 0}
        for composition in module.iter_compositions()
    ]


def test_scratch_prior_normalizes_and_local_neighbors_have_frozen_shape():
    total = sum(module.scratch_prior_mass(program_id) for program_id in range(128))
    assert total == Fraction(1, 1)
    for source_program in (0, 1, 85, 127):
        neighbors = module.local_neighbors(source_program)
        assert len(neighbors) == 6
        assert len(set(neighbors)) == 6
        source_coefficients = module.program_bits(source_program)
        for neighbor in neighbors:
            neighbor_coefficients = module.program_bits(neighbor)
            assert neighbor_coefficients[0] == source_coefficients[0]
            nonintercept_distance = sum(
                a != b for a, b in zip(source_coefficients[1:], neighbor_coefficients[1:])
            )
            assert nonintercept_distance == 1


def test_integer_weight_identity_matches_frozen_formula():
    for source_program in (0, 37, 64, 127):
        weights = module.unconditional_program_weights(source_program)
        assert sum(weights.values()) == 73728
        assert all(isinstance(value, int) and value >= 0 for value in weights.values())
        for program_id, weight in weights.items():
            expected = 3 * (3 ** (6 - sum(module.program_bits(program_id)[1:])))
            if program_id == source_program:
                expected += 24576
            if program_id in module.local_neighbors(source_program):
                expected += 4096
            assert weight == expected


def test_toy_posterior_predictive_brier_and_query_ties_are_exact():
    source_program = 0b0101010
    target_program = 0b0101011
    public_input = _fixture_input(source_program=source_program, target_program=target_program)
    history = module.history_from_public_input(public_input)
    posterior = module.compute_primary_posterior(public_input, history)
    assert posterior['posterior_total_weight'] > 0
    assert sum(posterior['family_posteriors'].values(), Fraction(0, 1)) == Fraction(1, 1)
    predictive = module.predictive_probability(posterior, '001')
    assert isinstance(predictive, Fraction)
    assert Fraction(0, 1) <= predictive <= Fraction(1, 1)
    risk = module.endpoint_brier_risk(public_input, history, fixed_query='001')
    assert risk >= 0
    query_info = module.choose_query(public_input, history, mode='primary')
    assert query_info['selected_query'] in module.SECOND_QUERY_CANDIDATES
    assert query_info['selected_query'] == min(query_info['minimizers'])
    assert query_info['optimistic_terminal_loss'] <= query_info['lexical_terminal_loss'] <= query_info['pessimistic_terminal_loss']
    hard_audit = module.hard_family_tie_audit(public_input)
    assert hard_audit['lexical_family'] == hard_audit['tied_families'][0]
    assert tuple(f for f in module.FAMILY_ORDER if f in hard_audit['tied_families']) == hard_audit['tied_families']
    assert set(hard_audit['branch_public_state_signatures']) == set(hard_audit['tied_families'])
    assert hard_audit['control_match_reducer'] == 'reduce_hard_family_tie_sensitivity'
    equal = module.reduce_hard_family_tie_sensitivity(
        ('SCRATCH', 'EXACT_SOURCE'), {'SCRATCH': False, 'EXACT_SOURCE': False},
    )
    assert equal['instrument_invalid'] is False
    different = module.reduce_hard_family_tie_sensitivity(
        ('SCRATCH', 'EXACT_SOURCE'), {'SCRATCH': False, 'EXACT_SOURCE': True},
    )
    assert different['instrument_invalid'] is True


def test_population_shape_and_weights_without_formal_execution():
    summary = module.population_summary()
    assert summary['pair_count_per_arm'] == 16384
    assert summary['source_program_count'] == 128
    assert summary['target_program_count'] == 128
    assert summary['stratum_counts'] == {'EXACT': 128, 'LOCAL': 768, 'NONLOCAL': 15488}
    for source_program in (0, 17, 127):
        weights = module.nonlocal_target_weights(source_program)
        assert sum(weights.values(), Fraction(0, 1)) == Fraction(1, 1)
        assert all(target not in weights for target in {source_program, *module.local_neighbors(source_program)})
        exact_weight = module.population_case_weight(source_program, source_program)
        local_weight = sum(module.population_case_weight(source_program, target) for target in module.local_neighbors(source_program))
        nonlocal_weight = sum(module.population_case_weight(source_program, target) for target in weights)
        assert exact_weight == local_weight == nonlocal_weight == Fraction(1, 128)
    with pytest.raises(module.ArtifactValidationError):
        module.reduce_complete_population_rows([], expected_arm_id='MIXTURE_BMA_ACTIVE_BRIER')
    invalid_status_row = {
        'source_program': 0, 'target_program': 0, 'stratum': 'EXACT',
        'status': 'FAILED', 'arm_id': 'MIXTURE_BMA_ACTIVE_BRIER',
        'lexical_loss': Fraction(0),
    }
    with pytest.raises(module.ArtifactValidationError):
        module.reduce_complete_population_rows(
            [invalid_status_row] * 16384,
            expected_arm_id='MIXTURE_BMA_ACTIVE_BRIER',
        )
    mixed_arm_row = {**invalid_status_row, 'status': 'OK', 'arm_id': 'WRONG_ARM'}
    with pytest.raises(module.ArtifactValidationError):
        module.reduce_complete_population_rows(
            [mixed_arm_row] * 16384,
            expected_arm_id='MIXTURE_BMA_ACTIVE_BRIER',
        )
    with pytest.raises(module.ArtifactValidationError):
        module.select_global_fixed_query([])


def test_exact_risk_tail_and_pareto_reducers_have_hand_checked_witnesses():
    candidate = {
        'NONLOCAL': Fraction(3, 10), 'EXACT': Fraction(1, 10),
        'LOCAL': Fraction(1, 5), 'NOMINAL': Fraction(1, 5),
        'SCRATCH_HEAVY': Fraction(9, 40),
    }
    baseline = {
        'NONLOCAL': Fraction(1, 4), 'EXACT': Fraction(1, 4),
        'LOCAL': Fraction(1, 4), 'NOMINAL': Fraction(1, 4),
        'SCRATCH_HEAVY': Fraction(1, 4),
    }
    summary = module.reduce_risk_summary(candidate, baseline)
    assert summary == {
        'nominal_relative_gain': Fraction(1, 5),
        'exact_relative_gain': Fraction(3, 5),
        'local_relative_gain': Fraction(1, 5),
        'nonlocal_relative_regret': Fraction(1, 5),
        'scratch_heavy_relative_gain': Fraction(1, 10),
    }
    tails = module.weighted_tail_disclosures([
        (Fraction(1, 1), Fraction(1, 20)),
        (Fraction(1, 2), Fraction(1, 20)),
        (Fraction(0, 1), Fraction(9, 10)),
    ])
    assert tails['maximum_nonlocal_regret'] == 1
    assert tails['nonlocal_negative_transfer_weighted_mass'] == Fraction(1, 10)
    assert tails['worst_10_percent_mass_nonlocal_cvar'] == Fraction(3, 4)
    assert module.control_pareto_matches(candidate, candidate) is True
    worse_control = dict(candidate, NONLOCAL=Fraction(31, 100))
    assert module.control_pareto_matches(candidate, worse_control) is False
    gate_kwargs = {
        'active_vs_best_fixed_relative_gain': Fraction(1, 50),
        'unique_nonlexical_positive_forward': True,
        'source_delete_pass': True, 'local_delete_pass': True,
        'feedback_mask_pass': True, 'active_delete_pass': True,
        'complete_population': True, 'fresh_replay_equal': True,
        'independent_recompute_equal': True,
        'leakage_positive_controls_rejected': True,
    }
    failing_flags = module._compute_gate_flags_from_values(summary, **gate_kwargs)
    assert failing_flags['nonlocal_safety_pass'] is False
    assert module.dispatch_verdict(failing_flags) == 'CAOT_BOOL_V2_NO_REFERENCE_HEADROOM'
    passing_metrics = {
        'nominal_relative_gain': Fraction(1, 10),
        'exact_relative_gain': Fraction(1, 10),
        'local_relative_gain': Fraction(1, 10),
        'nonlocal_relative_regret': Fraction(1, 100),
        'scratch_heavy_relative_gain': Fraction(1, 50),
    }
    passing_flags = module._compute_gate_flags_from_values(passing_metrics, **gate_kwargs)
    assert module.dispatch_verdict(passing_flags) == 'CAOT_BOOL_V2_REFERENCE_HEADROOM_ADMITTED'


def test_control_registry_and_ablation_registry_are_complete_and_callable():
    assert set(module.CONTROL_REGISTRY) == {
        'SCRATCH_SPIKE_SLAB_ACTIVE_BAYES',
        'EXACT_SOURCE_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK',
        'LOCAL_ONLY_ACTIVE_WITH_SCRATCH_FALLBACK',
        'SOURCE_CONSISTENCY_WITH_SCRATCH_FALLBACK',
        'MARGINAL_MDL_MAP_HARD_FAMILY',
        'MINIMUM_HAMMING_NEAREST_SOURCE',
        'FIXED_QUERY_001', 'FIXED_QUERY_010', 'FIXED_QUERY_011',
        'FIXED_QUERY_100', 'FIXED_QUERY_101', 'FIXED_QUERY_110',
        'FIXED_QUERY_111', 'PASSIVE_LEXICAL', 'UNIFORM_FIXED_QUERY_MIXTURE',
        'OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN',
        'COUNT_TABLE_TARGET_MEAN', 'GRAPH_LOOKUP_MIN_HAMMING_MEAN',
        'EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY',
        'CANDIDATE_RULE_AMORTIZED_LOOKUP',
        'TRANSITION_TABLE', 'SUCCESSOR_MAP', 'FSM_PLANNER',
    }
    assert set(module.ABLATION_REGISTRY) == {
        'SOURCE_DELETE', 'LOCAL_DELETE', 'FEEDBACK_MASK', 'ACTIVE_DELETE',
        'UNIFORM_SCRATCH_PRIOR', 'SOURCE_TABLE_ROW_PERMUTE', 'VARIABLE_RELABEL',
        'SERIALIZED_STATE_RESET', 'SERIALIZED_STATE_SWAP',
        'HIDDEN_COEFFICIENT_POSITIVE_CONTROL', 'HIDDEN_RELATION_POSITIVE_CONTROL',
    }
    public_input = _fixture_input()
    candidate = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input)
    scratch = module.run_arm('SCRATCH_SPIKE_SLAB_ACTIVE_BAYES', public_input)
    assert candidate['arm_id'] == 'MIXTURE_BMA_ACTIVE_BRIER'
    assert scratch['arm_id'] == 'SCRATCH_SPIKE_SLAB_ACTIVE_BAYES'
    assert scratch['source_table_read_count'] == 0
    assert scratch['source_access_receipt']['schema_validation_source_read_allowed'] is True
    assert scratch['source_access_receipt']['inference_source_access_count'] == 0
    assert scratch['source_access_receipt']['positive_control_detected'] is True
    ceiling = module.run_arm('CANDIDATE_RULE_AMORTIZED_LOOKUP', public_input)
    assert module.public_state_signature(candidate) == module.public_state_signature(ceiling)
    for source_program, target_program in ((0, 0), (37, 36), (85, 127)):
        bounded = _fixture_input(source_program=source_program, target_program=target_program)
        live = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', bounded)
        lookup = module.run_arm('CANDIDATE_RULE_AMORTIZED_LOOKUP', bounded)
        assert module.public_state_signature(live) == module.public_state_signature(lookup)
    for arm_id in module.CONTROL_REGISTRY:
        record = module.run_arm(arm_id, public_input)
        if arm_id in {'TRANSITION_TABLE', 'SUCCESSOR_MAP', 'FSM_PLANNER'}:
            assert record['status'] == 'NOT_APPLICABLE'
        else:
            assert record['status'] == 'OK'
    for ablation_id in module.ABLATION_REGISTRY:
        record = module.run_ablation(ablation_id, public_input)
        assert record['ablation_id'] == ablation_id


def test_public_history_shortcuts_have_frozen_prediction_semantics():
    public_input = _fixture_input(source_program=0b0101010, target_program=0b0101011)
    history = (('000', 0), ('011', 1))
    exact = module.shortcut_prediction(
        'OBSERVATION_HISTORY_EXACT_LOOKUP_SOURCE_VALUE_FOR_UNSEEN',
        public_input, history, '001',
    )
    assert exact == dict((row['composition'], row['outcome']) for row in public_input['source_truth_table'])['001']
    assert module.shortcut_prediction('COUNT_TABLE_TARGET_MEAN', public_input, history, '001') == Fraction(1, 2)
    assert module.shortcut_prediction('GRAPH_LOOKUP_MIN_HAMMING_MEAN', public_input, history, '001') == Fraction(1, 2)
    assert module.shortcut_prediction('EPISODIC_TRAVERSAL_LEXICAL_MIN_HAMMING_COPY', public_input, history, '001') == 0
    endpoint = module.shortcut_fixed_query_endpoint(
        'COUNT_TABLE_TARGET_MEAN', public_input, fixed_query='001', query_outcome=1,
    )
    assert endpoint['history'][-1] == ('001', 1)
    assert set(endpoint['predictions']) == set(module.COMPOSITIONS) - {'000', '001'}


def test_scratch_inference_is_source_content_invariant_after_public_validation():
    left = _fixture_input(source_program=1, target_program=37)
    right = _fixture_input(source_program=126, target_program=37)
    left_scratch = module.run_arm('SCRATCH_SPIKE_SLAB_ACTIVE_BAYES', left)
    right_scratch = module.run_arm('SCRATCH_SPIKE_SLAB_ACTIVE_BAYES', right)
    assert left_scratch['source_table_read_count'] == right_scratch['source_table_read_count'] == 0
    assert left_scratch['source_access_receipt']['inference_source_access_count'] == 0
    assert right_scratch['source_access_receipt']['inference_source_access_count'] == 0
    assert module.public_state_signature(left_scratch) == module.public_state_signature(right_scratch)


def test_source_delete_matches_scratch_and_invariances_hold_for_bounded_fixture():
    public_input = _fixture_input()
    source_delete = module.run_ablation('SOURCE_DELETE', public_input)
    scratch = module.run_arm('SCRATCH_SPIKE_SLAB_ACTIVE_BAYES', public_input)
    assert module.public_state_signature(source_delete['result']) == module.public_state_signature(scratch)

    permuted = module.run_ablation('SOURCE_TABLE_ROW_PERMUTE', public_input)
    relabeled = module.run_ablation('VARIABLE_RELABEL', public_input)
    primary = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input)
    assert module.public_state_signature(permuted['result']) == module.public_state_signature(primary)
    assert module.public_state_signature(relabeled['result']) == module.public_state_signature(primary)
    local_delete_receipt = module.compute_posterior_receipt(public_input, mode='local_delete')
    assert local_delete_receipt['family_marginals']['LOCAL_SHIFT'] == 0
    assert local_delete_receipt['family_posteriors']['LOCAL_SHIFT'] == 0
    uniform_receipt = module.compute_posterior_receipt(public_input, mode='uniform_scratch_primary')
    compatible_count = sum(
        all(module.evaluate_program(pid, composition)['outcome'] == outcome for composition, outcome in module.history_from_public_input(public_input))
        for pid in range(128)
    )
    assert uniform_receipt['family_marginals']['SCRATCH'] == Fraction(compatible_count, 128)


def test_candidate_lookup_materializes_complete_domain_and_retrieves_without_live_primary(monkeypatch):
    receipt = module.materialize_candidate_rule_lookup()
    assert receipt['complete'] is True
    assert receipt['state_count'] == receipt['expected_state_count'] == 3840
    assert receipt['query_state_count'] == 256
    assert receipt['prediction_state_count'] == 3584
    assert len(receipt['table_sha256']) == 64
    public_input = _fixture_input(source_program=37, target_program=36)
    live = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input)
    selected = live['selected_query']
    target_outcome = module.evaluate_program(36, selected)['outcome']
    h2_input = module.build_public_input(
        source_table=public_input['source_truth_table'],
        target_history=[*public_input['target_history'], {'composition': selected, 'outcome': target_outcome}],
        query_budget=1,
        arm_id='MIXTURE_BMA_ACTIVE_BRIER',
        serialized_state={'unrelated': 'ignored'},
    )
    posterior = module.compute_primary_posterior(h2_input, module.history_from_public_input(h2_input))
    expected_predictions = {
        composition: module.predictive_probability(posterior, composition)
        for composition in module.COMPOSITIONS
        if composition not in dict(module.history_from_public_input(h2_input))
    }
    assert module.candidate_lookup_predictions(h2_input) == expected_predictions
    def forbidden_live_call(*args, **kwargs):
        raise AssertionError('lookup retrieval called live primary')
    monkeypatch.setattr(module, '_record_for_mode', forbidden_live_call)
    lookup = module.run_arm('CANDIDATE_RULE_AMORTIZED_LOOKUP', public_input)
    assert lookup['lookup_table_sha256'] == receipt['table_sha256']


def test_feedback_mask_recomputes_from_h1_and_state_tests_report_statelessness():
    public_input = _fixture_input()
    feedback = module.run_ablation('FEEDBACK_MASK', public_input)['result']
    assert feedback['feedback_used'] is False
    assert feedback['masked_predictions_by_query_outcome']['0'] == feedback['masked_predictions_by_query_outcome']['1']
    assert len(feedback['masked_predictions_by_query_outcome']['0']) == 6
    assert feedback['mask_semantics'] == 'same_H1_query_second_outcome_not_added_to_posterior'
    pair_primary = module.evaluate_pair(42, 43)
    pair_masked = module.evaluate_feedback_mask_pair(42, 43)
    assert pair_masked['selected_query'] == pair_primary['selected_query']
    assert pair_masked['masked_history'] == (('000', module.evaluate_program(43, '000')['outcome']),)
    assert pair_masked['selected_predictions'] != pair_primary['selected_predictions']
    comparator = module.evaluate_pair(42, 43, arm_id='FIXED_QUERY_001')
    common = module.common_unqueried_gain(pair_primary, comparator)
    assert common['candidate_query'] == pair_primary['selected_query']
    assert common['comparator_query'] == '001'
    assert common['common_unqueried_count'] == (5 if pair_primary['selected_query'] != '001' else 6)
    manual_candidate = sum(
        (pair_primary['selected_predictions'][node] - pair_primary['selected_truth'][node]) ** 2
        for node in common['common_unqueried']
    ) / common['common_unqueried_count']
    manual_comparator = sum(
        (comparator['selected_predictions'][node] - comparator['selected_truth'][node]) ** 2
        for node in common['common_unqueried']
    ) / common['common_unqueried_count']
    assert common['gain'] == manual_comparator - manual_candidate
    reset = module.run_ablation('SERIALIZED_STATE_RESET', public_input)
    swap = module.run_ablation('SERIALIZED_STATE_SWAP', public_input)
    for record in (reset, swap):
        assert record['state_bytes_changed'] is True
        assert record['behavior_changed'] is False
        assert record['state_dependency_detected'] is False
        assert module.public_state_signature(record['baseline_result']) == module.public_state_signature(record['result'])
        assert record['claim_ceiling'] == 'state_mutation_test_only_no_state_history_dependence_claim'


def test_leakage_scanner_rejects_direct_and_encoded_private_truth_and_positive_controls():
    legal = _fixture_input()
    legal_report = module.scan_public_input(legal)
    assert legal_report['accepted'] is True

    direct = dict(legal)
    direct['target_program_id'] = 3
    with pytest.raises(module.PrivateTruthLeakageError):
        module.scan_public_input(direct)

    encoded = dict(legal)
    encoded['serialized_state'] = {'encoded_private_alias': 'target:3'}
    with pytest.raises(module.PrivateTruthLeakageError):
        module.scan_public_input(encoded)

    base64_encoded = dict(legal)
    base64_encoded['serialized_state'] = {
        'token': base64.b64encode(b'target_program_id=3').decode('ascii'),
    }
    with pytest.raises(module.PrivateTruthLeakageError):
        module.scan_public_input(base64_encoded)

    for ablation_id in ('HIDDEN_COEFFICIENT_POSITIVE_CONTROL', 'HIDDEN_RELATION_POSITIVE_CONTROL'):
        result = module.run_ablation(ablation_id, legal)
        assert result['status'] == 'REJECTED_PRIVATE_TRUTH'


def test_serialization_and_tamper_detection_reject_invalid_rows_metrics_and_artifacts():
    public_input = _fixture_input()
    row = module.serialize_row(module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input))
    restored = module.deserialize_row(row)
    assert restored['arm_id'] == 'MIXTURE_BMA_ACTIVE_BRIER'
    tampered_row = json.loads(json.dumps(row))
    tampered_row['selected_query'] = '222'
    with pytest.raises(module.ArtifactValidationError):
        module.deserialize_row(tampered_row)

    metric = module.fraction_to_json(Fraction(2, 3))
    assert module.fraction_from_json(metric) == Fraction(2, 3)
    with pytest.raises(module.ArtifactValidationError):
        module.fraction_from_json({'numerator': 2, 'denominator': 0})

    with pytest.raises(module.ArtifactValidationError):
        module.validate_artifact_record({'metric_id': 'bad'})

    tie_tampered = json.loads(json.dumps(row))
    tie_tampered['minimizers'] = ['222']
    with pytest.raises(module.ArtifactValidationError):
        module.deserialize_row(tie_tampered)

    threshold_tampered = json.loads(json.dumps(row))
    threshold_tampered['query_scores']['001'] = {'numerator': 1, 'denominator': 0}
    with pytest.raises(module.ArtifactValidationError):
        module.deserialize_row(threshold_tampered)

    with pytest.raises(module.ArtifactValidationError):
        module.validate_artifact_record({'status': 'OK', 'arm_id': 'x', 'stratum': 'NONLOCAL'})


def test_verdict_priority_and_branches_follow_frozen_order():
    assert module.dispatch_verdict(_aggregate_fixture(private_truth_leakage=True)) == 'CAOT_BOOL_V2_PRIVATE_TRUTH_LEAKAGE'
    assert module.dispatch_verdict(_aggregate_fixture(instrument_invalid=True)) == 'CAOT_BOOL_V2_INSTRUMENT_INVALID'
    assert module.dispatch_verdict(_aggregate_fixture(query_tie_sensitive=True)) == 'CAOT_BOOL_V2_QUERY_TIE_SENSITIVE'
    assert module.dispatch_verdict(_aggregate_fixture(control_match=True)) == 'CAOT_BOOL_V2_EQUAL_ACCESS_CONTROL_MATCH'
    assert module.dispatch_verdict(_aggregate_fixture(nominal_gain_pass=False)) == 'CAOT_BOOL_V2_NO_REFERENCE_HEADROOM'
    assert module.dispatch_verdict(_aggregate_fixture(nominal_gain_pass=True)) == 'CAOT_BOOL_V2_REFERENCE_HEADROOM_ADMITTED'
    for field in module.POSITIVE_GATE_FIELDS:
        assert module.dispatch_verdict(_aggregate_fixture(**{field: False})) == 'CAOT_BOOL_V2_NO_REFERENCE_HEADROOM'
    for field in module.INTEGRITY_GATE_FIELDS:
        assert module.dispatch_verdict(_aggregate_fixture(**{field: False})) == 'CAOT_BOOL_V2_INSTRUMENT_INVALID'
    incomplete = _aggregate_fixture()
    incomplete.pop('local_gain_pass')
    assert module.dispatch_verdict(incomplete) == 'CAOT_BOOL_V2_INSTRUMENT_INVALID'


def test_gate_receipts_are_computed_from_complete_sources_and_fail_closed():
    def complete_rows(arm_id: str, loss: Fraction, *, selected_query: str = '010', minimizers=('010',)):
        return [
            {
                'source_program': source,
                'target_program': target,
                'stratum': module.classify_pair(source, target),
                'status': 'OK',
                'arm_id': arm_id,
                'producer_function': 'evaluate_pair',
                'lexical_loss': loss,
                'optimistic_loss': loss,
                'pessimistic_loss': loss,
                'selected_query': selected_query,
                'minimizers': minimizers,
                'selected_predictions': {'111': Fraction(0)},
                'selected_truth': {'111': 0},
            }
            for source in range(128)
            for target in range(128)
        ]

    fixed_losses = {query: Fraction(1, 4) for query in module.SECOND_QUERY_CANDIDATES}
    fixed_endpoints = {
        query: {'predictions': {'111': Fraction(1)}, 'truth': {'111': 0}}
        for query in module.SECOND_QUERY_CANDIDATES
    }
    fixed_rows = [
        {
            'source_program': source,
            'target_program': target,
            'stratum': module.classify_pair(source, target),
            'status': 'OK',
            'arm_id': 'FIXED_QUERY_PANEL_PRIMARY',
            'producer_function': 'evaluate_all_fixed_queries',
            'fixed_query_losses': fixed_losses,
            'fixed_query_endpoints': fixed_endpoints,
        }
        for source in range(128)
        for target in range(128)
    ]
    scratch_rows = complete_rows('SCRATCH_SPIKE_SLAB_ACTIVE_BAYES', Fraction(1, 4))
    candidate_rows = complete_rows('MIXTURE_BMA_ACTIVE_BRIER', Fraction(1, 5))
    source_delete_rows = [{**row, 'arm_id': 'SOURCE_DELETE'} for row in scratch_rows]
    local_delete_rows = complete_rows('LOCAL_DELETE', Fraction(1, 4), selected_query='001', minimizers=module.SECOND_QUERY_CANDIDATES)
    feedback_mask_rows = complete_rows('FEEDBACK_MASK', Fraction(1, 4), selected_query='001', minimizers=module.SECOND_QUERY_CANDIDATES)
    active_delete_rows = complete_rows('ACTIVE_DELETE', Fraction(1, 4), selected_query='UNIFORM_MIXTURE', minimizers=module.SECOND_QUERY_CANDIDATES)

    reference = module.reduce_reference_population(candidate_rows, scratch_rows)
    source_delete_reference = module.reduce_reference_population(source_delete_rows, scratch_rows, candidate_arm_id='SOURCE_DELETE')
    local_delete_reference = module.reduce_reference_population(local_delete_rows, scratch_rows, candidate_arm_id='LOCAL_DELETE')
    feedback_active = module.reduce_active_necessity(feedback_mask_rows, fixed_rows, candidate_arm_id='FEEDBACK_MASK')
    active_delete_active = module.reduce_active_necessity(active_delete_rows, fixed_rows, candidate_arm_id='ACTIVE_DELETE')
    ablation = module.reduce_ablation_evidence(
        source_delete_reference_receipt=source_delete_reference,
        local_delete_reference_receipt=local_delete_reference,
        feedback_mask_active_receipt=feedback_active,
        active_delete_active_receipt=active_delete_active,
    )
    assert reference['status'] == 'OK'
    assert reference['coverage']['candidate_row_count'] == 16384
    assert ablation['source_delete_pass'] is True
    assert ablation['coverage']['source_delete_behavior_sha256']
    assert ablation['coverage']['source_delete_behavior_sha256'] == ablation['coverage']['scratch_behavior_sha256']

    tampered_source = dict(source_delete_reference)
    tampered_source['relative_metrics'] = dict(source_delete_reference['relative_metrics'])
    tampered_source['relative_metrics']['nominal_relative_gain'] = Fraction(1)
    with pytest.raises(module.ArtifactValidationError, match='hash'):
        module.reduce_ablation_evidence(
            source_delete_reference_receipt=tampered_source,
            local_delete_reference_receipt=local_delete_reference,
            feedback_mask_active_receipt=feedback_active,
            active_delete_active_receipt=active_delete_active,
        )
    with pytest.raises(module.ArtifactValidationError, match='control receipt set'):
        module.reduce_control_evidence(reference, {})
    with pytest.raises(module.FormalExecutionNotAuthorizedError, match=module.FORMAL_BLOCK):
        module.compute_gate_flags_from_evidence()
    with pytest.raises(module.FormalExecutionNotAuthorizedError, match=module.FORMAL_BLOCK):
        module.dispatch_verdict_evidence()
    with pytest.raises(module.FormalExecutionNotAuthorizedError, match=module.FORMAL_BLOCK):
        module._make_evidence_receipt(
            'dispatch_verdict_evidence',
            input_sources=('computed_gate_receipt',),
            coverage={
                'gate_phase': 'FINAL',
                'branch_kind': 'FINAL',
                'gate_receipt_sha256': '0' * 64,
            },
            payload={'verdict': 'CAOT_BOOL_V2_REFERENCE_HEADROOM_ADMITTED'},
        )
    pass_shaped = _aggregate_fixture()
    pass_shaped['producer_function'] = 'compute_gate_flags_from_evidence'
    with pytest.raises(module.FormalExecutionNotAuthorizedError, match=module.FORMAL_BLOCK):
        module.dispatch_verdict(pass_shaped)

    recompute = _load_recompute()
    independent_reference = recompute.reduce_reference_population(candidate_rows, scratch_rows)
    independent_source = recompute.reduce_reference_population(source_delete_rows, scratch_rows, candidate_arm_id='SOURCE_DELETE')
    independent_local = recompute.reduce_reference_population(local_delete_rows, scratch_rows, candidate_arm_id='LOCAL_DELETE')
    independent_feedback = recompute.reduce_active_necessity(feedback_mask_rows, fixed_rows, candidate_arm_id='FEEDBACK_MASK')
    independent_active_delete = recompute.reduce_active_necessity(active_delete_rows, fixed_rows, candidate_arm_id='ACTIVE_DELETE')
    independent_ablation = recompute.reduce_ablation_evidence(
        source_delete_reference_receipt=independent_source,
        local_delete_reference_receipt=independent_local,
        feedback_mask_active_receipt=independent_feedback,
        active_delete_active_receipt=independent_active_delete,
    )
    assert independent_reference['relative_metrics'] == reference['relative_metrics']
    for field in ('source_delete_pass', 'local_delete_pass', 'feedback_mask_pass', 'active_delete_pass'):
        assert independent_ablation[field] == ablation[field]
    with pytest.raises(recompute.FormalExecutionNotAuthorizedError, match=recompute.FORMAL_BLOCK):
        recompute.compute_gate_flags_from_evidence()


def test_population_stream_receipts_require_distinct_row_producer_lineage():
    case_pairs = ((0, 0), (37, 36), (85, 127))
    primary_stream = module.produce_primary_population_stream(case_pairs)
    replay_stream = module.produce_fresh_replay_stream(primary_stream)
    recompute = _load_recompute()
    independent_stream = recompute.produce_independent_recompute_stream(case_pairs)
    assert {row['producer_function'] for row in primary_stream['rows']} == {'evaluate_pair'}
    assert {row['producer_function'] for row in replay_stream['rows']} == {'replay_pair'}
    assert {row['producer_function'] for row in independent_stream['rows']} == {'recompute_pair'}
    for primary, replayed, independent in zip(primary_stream['rows'], replay_stream['rows'], independent_stream['rows']):
        assert {key: value for key, value in primary.items() if key != 'producer_function'} == {
            key: value for key, value in replayed.items() if key != 'producer_function'
        }
        assert primary['selected_query'] == independent['selected_query']
        assert primary['minimizer_losses'] == independent['minimizer_losses']
    leakage_stream = module.produce_leakage_scan_stream([
        {'case_id': 'CLEAN_LEGAL_INPUT', 'status': 'OK', 'producer_function': 'scan_public_input', 'positive_control': False, 'accepted': True},
        {'case_id': 'HIDDEN_COEFFICIENT_DIRECT', 'status': 'OK', 'producer_function': 'scan_public_input', 'positive_control': True, 'accepted': False},
        {'case_id': 'HIDDEN_RELATION_DIRECT', 'status': 'OK', 'producer_function': 'scan_public_input', 'positive_control': True, 'accepted': False},
        {'case_id': 'HIDDEN_COEFFICIENT_ENCODED', 'status': 'OK', 'producer_function': 'scan_public_input', 'positive_control': True, 'accepted': False},
        {'case_id': 'HIDDEN_RELATION_ENCODED', 'status': 'OK', 'producer_function': 'scan_public_input', 'positive_control': True, 'accepted': False},
    ])
    with pytest.raises(module.ArtifactValidationError, match='arm/count/hash'):
        module.reduce_formal_integrity_evidence(
            primary_stream, replay_stream, independent_stream, leakage_stream,
        )
    primary_rows = list(primary_stream['rows'])
    with pytest.raises(ValueError, match='invalid case pair'):
        recompute.produce_independent_recompute_stream(primary_rows)


def test_replay_comparison_detects_mismatch():
    public_input = _fixture_input()
    record = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input)
    replay_report = module.replay_row(record)
    assert replay_report['match'] is True
    tampered = dict(record)
    tampered['selected_query'] = '111' if record['selected_query'] != '111' else '110'
    mismatch = module.replay_row(tampered)
    assert mismatch['match'] is False


def test_independent_recompute_parity_and_fail_closed_entrypoint(tmp_path: Path):
    recompute = _load_recompute()
    public_input = _fixture_input()
    primary = module.run_arm('MIXTURE_BMA_ACTIVE_BRIER', public_input)
    parity = recompute.recompute_public_state(public_input)
    assert module.public_state_signature(primary) == module.public_state_signature(parity)
    assert recompute.recompute_posterior_receipt(public_input) == module.compute_posterior_receipt(public_input)
    assert recompute.recompute_posterior_receipt(public_input, mode='scratch') == module.compute_posterior_receipt(public_input, mode='scratch')
    assert recompute.compare_against_primary(public_input, primary)['match'] is True
    source_text = Path(RECOMPUTE_MODULE_PATH).read_text(encoding='utf-8')
    imported_modules = {
        alias.name
        for node in ast.walk(ast.parse(source_text))
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or '')])
    }
    assert 'check_ego_v2_compositional_causal_transfer_preflight_001e' not in imported_modules
    alternate = next(query for query in module.SECOND_QUERY_CANDIDATES if query != primary['selected_query'])
    mismatch = recompute.compare_against_primary(public_input, {**primary, 'selected_query': alternate})
    assert mismatch['match'] is False
    encoded_for_recompute = dict(public_input)
    encoded_for_recompute['serialized_state'] = {
        'token': base64.b64encode(b'target_program_id=3').decode('ascii'),
    }
    with pytest.raises(recompute.PrivateTruthLeakageError):
        recompute.recompute_public_state(encoded_for_recompute)
    for source_program, target_program in ((0, 0), (37, 36), (85, 127)):
        primary_pair = module.evaluate_pair(source_program, target_program)
        independent_pair = recompute.recompute_pair(source_program, target_program)
        assert primary_pair['stratum'] == independent_pair['stratum']
        assert primary_pair['selected_query'] == independent_pair['selected_query']
        assert primary_pair['minimizers'] == independent_pair['minimizers']
        assert primary_pair['minimizer_losses'] == independent_pair['minimizer_losses']
        assert primary_pair['lexical_loss'] == independent_pair['lexical_loss']
        primary_scratch = module.evaluate_pair(
            source_program, target_program,
            arm_id='SCRATCH_SPIKE_SLAB_ACTIVE_BAYES',
        )
        independent_scratch = recompute.recompute_pair(source_program, target_program, mode='scratch')
        assert primary_scratch['selected_query'] == independent_scratch['selected_query']
        assert primary_scratch['minimizer_losses'] == independent_scratch['minimizer_losses']
    independent_scratch_left = recompute.recompute_pair(1, 37, mode='scratch')
    independent_scratch_right = recompute.recompute_pair(126, 37, mode='scratch')
    assert independent_scratch_left['selected_query'] == independent_scratch_right['selected_query']
    assert independent_scratch_left['minimizer_losses'] == independent_scratch_right['minimizer_losses']
    assert recompute.population_summary() == module.population_summary()
    for source_program in (0, 37, 127):
        assert recompute.nonlocal_target_weights(source_program) == module.nonlocal_target_weights(source_program)
        for target_program in (source_program, module.local_neighbors(source_program)[0], 127 - source_program):
            assert recompute.population_case_weight(source_program, target_program) == module.population_case_weight(source_program, target_program)
    assert recompute.dispatch_verdict(_aggregate_fixture(control_match=True)) == module.dispatch_verdict(_aggregate_fixture(control_match=True))
    risk_candidate = {
        'NONLOCAL': Fraction(3, 10), 'EXACT': Fraction(1, 10),
        'LOCAL': Fraction(1, 5), 'NOMINAL': Fraction(1, 5),
        'SCRATCH_HEAVY': Fraction(9, 40),
    }
    risk_baseline = {key: Fraction(1, 4) for key in risk_candidate}
    assert recompute.reduce_risk_summary(risk_candidate, risk_baseline) == module.reduce_risk_summary(risk_candidate, risk_baseline)
    relative = module.reduce_risk_summary(risk_candidate, risk_baseline)
    gate_kwargs = {
        'active_vs_best_fixed_relative_gain': Fraction(1, 50),
        'unique_nonlexical_positive_forward': True,
        'source_delete_pass': True, 'local_delete_pass': True,
        'feedback_mask_pass': True, 'active_delete_pass': True,
        'complete_population': True, 'fresh_replay_equal': True,
        'independent_recompute_equal': True,
        'leakage_positive_controls_rejected': True,
    }
    assert recompute._compute_gate_flags_from_values(relative, **gate_kwargs) == module._compute_gate_flags_from_values(relative, **gate_kwargs)
    tail_fixture = [(Fraction(1), Fraction(1, 20)), (Fraction(1, 2), Fraction(1, 20)), (Fraction(0), Fraction(9, 10))]
    assert recompute.weighted_tail_disclosures(tail_fixture) == module.weighted_tail_disclosures(tail_fixture)
    before = sorted(tmp_path.iterdir())
    with pytest.raises(recompute.FormalExecutionNotAuthorizedError):
        recompute.run_formal_population(output_dir=tmp_path)
    assert before == sorted(tmp_path.iterdir())


def test_formal_execution_fails_closed_and_writes_no_artifacts(tmp_path: Path):
    before = sorted(tmp_path.iterdir())
    with pytest.raises(module.FormalExecutionNotAuthorizedError):
        module.run_formal_population(output_dir=tmp_path)
    after = sorted(tmp_path.iterdir())
    assert before == after
