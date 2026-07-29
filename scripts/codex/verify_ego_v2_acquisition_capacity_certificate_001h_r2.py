from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import json
import re
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

R1_SCRIPT_PATH = REPO_ROOT / 'scripts' / 'codex' / 'verify_ego_v2_acquisition_benchmark_admission_001h_r1.py'
_ACTION_ORDER = ('turn_left', 'turn_right', 'move_forward', 'interact', 'rest')
ACTION_ORDER = _ACTION_ORDER
_PANEL_NAV_ACTIONS = ('turn_left', 'turn_right', 'move_forward')
_FROZEN_CONTEXTS = (
    {
        'context_id': 'p0_cross_v1:world=52:policy=711',
        'layout_id': 'p0_cross_v1',
        'world_seed': 52,
        'policy_seed': 711,
        'panel_rollout_ids': [9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
        'context_id': 'p2_vertical_v1:world=54:policy=711',
        'layout_id': 'p2_vertical_v1',
        'world_seed': 54,
        'policy_seed': 711,
        'panel_rollout_ids': [9, 10, 11, 12, 13, 14, 15, 16],
    },
)
_PANEL_TARGET_MULTISET = ['v0', 'v1', 'v2', 'v3', 'v4', 'empty', 'wall', 'empty', 'wall']
_PANEL_FLOORS = {'v0': 8, 'v1': 8, 'v2': 8, 'v3': 8, 'v4': 8, 'empty': 16, 'wall': 16}
_FROZEN_SOURCE_PINS = {
    'docs/codex/tasks/EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H.md': '2f34b8c6e378f88a8cf66db957ec58c8e9adb44a3f8f712aea04ece797d2ddfc',
    'docs/codex/tasks/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1.md': '915610ed949db8f670c7bba83f9fc0786b1130652185a3ead05c04e9c37295bb',
    'docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/COLLISION_RECORD.md': '76e0cb8c9687d20fe8df131b1b52bf359b62789736c9f6e42937f749fd89a73e',
    'artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/result.json': 'e6c7ef8aec16363e7888cf4f07de809b2e72a0c8d672806b2c206a985d77edcb',
    'artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/support_report.json': '969d92c1e4126ec6573b3586b0e93dde7935879888b34e07f9a115192cc2bf8a',
    'artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/panel_manifest.json': '347eb90b55d0fabbdfe6ee5e3db0da1321fd584e6ffa3aa49d9fb03a117f1522',
    'artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/recompute_report.json': '62ab3413a379f45b2b8b055fba277aa791be0bbe31fb985cc190ac44469d64fd',
    'scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py': '5495d1a69977bdf195bcc239d8e5424c4e89ea498810d797814978a342f0c01a',
    'labs/ego_life_playground_v0/engine.py': '867ced15abc356daa0d5cae3f4c1cb1412a15766239ee82e9a8d280e5b214385',
    'labs/ego_life_playground_v0/microworld.py': 'd87ba9530d32d2b504c75a132ae1163dfe8e8cd0a8879e6cbdd09807a9daa923',
    'labs/ego_life_playground_v0/predictive_control.py': '1763ee3e2b755529559311fb99f247b8bc1034d0cc89708dafdd4b15e8529aae',
    'labs/ego_life_playground_v0/store.py': '3e399471c89ec5046ae3bffe1de3419e61f8b1e0f8d3bb55d216ef6578616b84',
    'requirements-ego-v2.txt': 'a23aaf94250a9f53031a592980142245a848e2372b6c6c3093e8260b129265b8',
}
_STALE_WORLD_SEEDS = frozenset({60, 61, 62, 63, 64, 65})
_STALE_POLICY_SEEDS = frozenset({721, 722})
_BASE64_PATTERN = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')


def _load_r1_module():
    spec = importlib.util.spec_from_file_location('verify_001h_r1_for_r2', R1_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('failed to load pinned R1 verifier')
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


_R1 = _load_r1_module()
engine = _R1.engine
runtime_receipt = _R1.runtime_receipt
quotient_features = _R1.quotient_features
build_public_checkpoint = _R1.build_public_checkpoint
advance_evaluator_action = _R1.advance_evaluator_action
advance_evaluator_respawn = _R1.advance_evaluator_respawn
initialize_evaluator_state = _R1.initialize_evaluator_state
private_shortest_front_path = _R1.private_shortest_front_path
scan_learner_projection = _R1.scan_learner_projection


def build_frozen_contract() -> dict[str, Any]:
    return {
        'task_id': 'EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2',
        'contexts': deepcopy(list(_FROZEN_CONTEXTS)),
        'witness_search': {
            'action_budget': 89,
            'max_life_index': 4,
            'max_respawns': 3,
            'processed_node_cap': 2_000_000,
            'action_order': list(ACTION_ORDER),
            'analytic_root_lower_bound': 76,
        },
        'panel_search': {
            'processed_node_cap': 250_000,
            'action_order': list(_PANEL_NAV_ACTIONS),
        },
        'panel_target_multiset': deepcopy(_PANEL_TARGET_MULTISET),
        'panel_floors': deepcopy(_PANEL_FLOORS),
        'source_pins': deepcopy(_FROZEN_SOURCE_PINS),
        'stale_world_seed_firewall': sorted(_STALE_WORLD_SEEDS),
        'stale_policy_seed_firewall': sorted(_STALE_POLICY_SEEDS),
    }


def validate_frozen_contract(contract: dict[str, Any]) -> dict[str, Any]:
    expected = build_frozen_contract()
    reasons: list[str] = []
    if contract.get('task_id') != expected['task_id']:
        reasons.append('task_id')
    if contract.get('witness_search', {}).get('action_budget') != expected['witness_search']['action_budget']:
        reasons.append('witness_search.action_budget')
    if contract.get('witness_search', {}).get('max_life_index') != expected['witness_search']['max_life_index']:
        reasons.append('witness_search.max_life_index')
    if contract.get('witness_search', {}).get('max_respawns') != expected['witness_search']['max_respawns']:
        reasons.append('witness_search.max_respawns')
    if contract.get('witness_search', {}).get('processed_node_cap') != expected['witness_search']['processed_node_cap']:
        reasons.append('witness_search.processed_node_cap')
    if contract.get('panel_search', {}).get('processed_node_cap') != expected['panel_search']['processed_node_cap']:
        reasons.append('panel_search.processed_node_cap')
    if list(contract.get('panel_target_multiset', [])) != expected['panel_target_multiset']:
        reasons.append('panel_target_multiset')
    if dict(contract.get('panel_floors', {})) != expected['panel_floors']:
        reasons.append('panel_floors')
    if dict(contract.get('source_pins', {})) != expected['source_pins']:
        reasons.append('source_pins')

    contexts = list(contract.get('contexts', []))
    if contexts != expected['contexts']:
        for index, (actual, wanted) in enumerate(zip(contexts, expected['contexts'], strict=False)):
            if actual != wanted:
                for key in sorted(set(actual) | set(wanted)):
                    if actual.get(key) != wanted.get(key):
                        reasons.append(f'contexts[{index}].{key}')
        if len(contexts) != len(expected['contexts']):
            reasons.append('contexts.length')
    for index, context in enumerate(contexts):
        if context.get('world_seed') in _STALE_WORLD_SEEDS:
            reasons.append(f'contexts[{index}].world_seed_stale_firewall')
        if context.get('policy_seed') in _STALE_POLICY_SEEDS:
            reasons.append(f'contexts[{index}].policy_seed_stale_firewall')
    valid = not reasons
    return {
        'valid': valid,
        'verdict': 'CONTRACT_OK' if valid else 'INVALID_POSTRESULT_RESCUE',
        'failure_reasons': reasons,
        'contract_digest': engine.canonical_hash(contract),
        'expected_contract_digest': engine.canonical_hash(expected),
    }


def remaining_action_lower_bound(*, support_deficits: dict[str, int], rank_gaps: dict[str, int]) -> int:
    total = 0
    for action in ACTION_ORDER:
        total += max(int(support_deficits.get(action, 0)), int(rank_gaps.get(action, 0)))
    return total


def root_analytic_lower_bound(contract: dict[str, Any] | None = None) -> int:
    _ = contract
    return remaining_action_lower_bound(
        support_deficits={'interact': 24, 'move_forward': 13, 'rest': 13, 'turn_left': 13, 'turn_right': 13},
        rank_gaps={action: 0 for action in ACTION_ORDER},
    )


def assess_budget_feasibility(*, action_budget: int, support_deficits: dict[str, int], rank_gaps: dict[str, int], g: int) -> dict[str, int | str]:
    h = remaining_action_lower_bound(support_deficits=support_deficits, rank_gaps=rank_gaps)
    f = int(g) + h
    if f > int(action_budget):
        return {'status': 'bound_pruned', 'g': int(g), 'h': h, 'f': f, 'action_budget': int(action_budget)}
    return {'status': 'within_budget', 'g': int(g), 'h': h, 'f': f, 'action_budget': int(action_budget)}


def make_search_node(*, evaluator_state: dict[str, Any], g: int, prefix: tuple[int, ...], support_counts: dict[str, int], rank_rows: dict[str, Any], accepted_rows: list[dict[str, Any]], life_index: int, respawn_count: int) -> dict[str, Any]:
    return {
        'evaluator_state': deepcopy(evaluator_state),
        'g': int(g),
        'prefix': tuple(int(item) for item in prefix),
        'support_counts': {str(key): int(value) for key, value in support_counts.items()},
        'rank_rows': deepcopy(rank_rows),
        'accepted_rows': deepcopy(accepted_rows),
        'life_index': int(life_index),
        'respawn_count': int(respawn_count),
    }


def search_node_digest(node: dict[str, Any]) -> str:
    payload = {
        'evaluator_state': node['evaluator_state'],
        'g': int(node['g']),
        'support_counts': node['support_counts'],
        'rank_rows': node['rank_rows'],
        'accepted_rows': node['accepted_rows'],
        'life_index': int(node['life_index']),
        'respawn_count': int(node['respawn_count']),
    }
    return engine.canonical_hash(payload)


class DuplicateLedger:
    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def observe(self, node: dict[str, Any], digest_override: str | None = None) -> dict[str, Any]:
        digest = str(digest_override or search_node_digest(node))
        prefix = tuple(node['prefix'])
        entry = self._entries.get(digest)
        if entry is None:
            self._entries[digest] = {'g': int(node['g']), 'prefix': prefix}
            return {'status': 'new', 'digest': digest, 'representative_prefix': prefix}
        if int(entry['g']) != int(node['g']):
            raise ValueError('same digest with different g')
        if prefix < entry['prefix']:
            entry['prefix'] = prefix
            return {'status': 'replaced', 'digest': digest, 'representative_prefix': prefix}
        return {'status': 'duplicate', 'digest': digest, 'representative_prefix': entry['prefix']}


def depth_first_branch_and_bound(*, root: dict[str, Any], expand_fn, goal_fn, bound_fn, action_budget: int, processed_node_cap: int) -> dict[str, Any]:
    ledger = DuplicateLedger()
    receipts: list[dict[str, Any]] = []
    processed_nodes = 0
    stack = [root]
    unprocessed_legal_child = False
    while stack:
        node = stack.pop()
        ledger.observe(node)
        processed_nodes += 1
        digest = search_node_digest(node)
        h = int(bound_fn(node))
        if goal_fn(node):
            receipts.append({'processed_node_index': processed_nodes, 'node_digest': digest, 'g': int(node['g']), 'h': h, 'node_disposition': 'goal'})
            return {'status': 'goal_found', 'goal_node': deepcopy(node), 'processed_nodes': processed_nodes, 'complete_search': False, 'unprocessed_legal_child': False, 'receipts': receipts}
        if int(node['g']) >= int(action_budget):
            receipts.append({'processed_node_index': processed_nodes, 'node_digest': digest, 'g': int(node['g']), 'h': h, 'node_disposition': 'horizon_non_goal'})
            continue
        if int(node['g']) + h > int(action_budget):
            receipts.append({'processed_node_index': processed_nodes, 'node_digest': digest, 'g': int(node['g']), 'h': h, 'node_disposition': 'bound_pruned'})
            continue
        children = list(expand_fn(node))
        dispositions = []
        for action_index, action_name in enumerate(ACTION_ORDER):
            child = children[action_index] if action_index < len(children) else None
            if child is None:
                dispositions.append({'action': action_name, 'disposition': 'missing_child'})
                continue
            child_digest = search_node_digest(child)
            dispositions.append({'action': action_name, 'disposition': 'child', 'child_digest': child_digest})
        receipts.append({'processed_node_index': processed_nodes, 'node_digest': digest, 'g': int(node['g']), 'h': h, 'dispositions': dispositions})
        for child in reversed(children):
            if processed_nodes >= int(processed_node_cap):
                unprocessed_legal_child = True
                return {'status': 'WITNESS_SEARCH_INCONCLUSIVE', 'processed_nodes': processed_nodes, 'complete_search': False, 'unprocessed_legal_child': True, 'receipts': receipts}
            stack.append(child)
    return {'status': 'search_exhausted', 'processed_nodes': processed_nodes, 'complete_search': True, 'unprocessed_legal_child': unprocessed_legal_child, 'receipts': receipts}


def run_warm_start(*, prefix: tuple[int, ...], candidate_specs: list[dict[str, Any]], simulate_candidate) -> dict[str, Any]:
    ordered = sorted(candidate_specs, key=lambda item: item['score'])
    for candidate in ordered:
        result = simulate_candidate(prefix, candidate)
        if result.get('passed'):
            return {
                'status': 'warm_start_certificate',
                'candidate_name': candidate['name'],
                'node': result['node'],
                'dfs_root_untouched': True,
            }
    return {'status': 'warm_start_failed', 'dfs_root_untouched': True}


def _claim_token_if_available(front_token: str | None, remaining: Counter[str], claimed_hashes: set[str], checkpoint_hash: str) -> str | None:
    if front_token is None or remaining[front_token] <= 0 or checkpoint_hash in claimed_hashes:
        return None
    return front_token


def search_panel_certificate(*, start_state: dict[str, Any], target_multiset: list[str], expand_fn, checkpoint_hash_fn, processed_node_cap: int) -> dict[str, Any]:
    remaining = Counter(target_multiset)
    start_hash = str(checkpoint_hash_fn(start_state))
    claimed_hashes: set[str] = set()
    claimed = _claim_token_if_available(start_state.get('front_token'), remaining, claimed_hashes, start_hash)
    if claimed is not None:
        remaining[claimed] -= 1
        claimed_hashes.add(start_hash)
    queue = deque([{'state': deepcopy(start_state), 'remaining': remaining, 'claimed_targets': [claimed] if claimed else [], 'claimed_hashes': claimed_hashes, 'actions': []}])
    processed = 0
    while queue:
        current = queue.popleft()
        processed += 1
        if sum(current['remaining'].values()) == 0:
            return {'status': 'panel_certificate_found', 'claimed_targets': current['claimed_targets'], 'action_sequence': current['actions'], 'processed_nodes': processed}
        expansions = expand_fn(current['state'])
        for action in _PANEL_NAV_ACTIONS:
            if action not in expansions:
                continue
            next_state = deepcopy(expansions[action])
            next_remaining = current['remaining'].copy()
            next_claimed_hashes = set(current['claimed_hashes'])
            next_claimed_targets = list(current['claimed_targets'])
            checkpoint_hash = str(checkpoint_hash_fn(next_state))
            claimed_token = _claim_token_if_available(next_state.get('front_token'), next_remaining, next_claimed_hashes, checkpoint_hash)
            if claimed_token is not None:
                next_remaining[claimed_token] -= 1
                next_claimed_hashes.add(checkpoint_hash)
                next_claimed_targets.append(claimed_token)
            if processed >= int(processed_node_cap):
                return {'status': 'PANEL_SEARCH_INCONCLUSIVE', 'processed_nodes': processed, 'unprocessed_legal_child': True}
            queue.append({'state': next_state, 'remaining': next_remaining, 'claimed_targets': next_claimed_targets, 'claimed_hashes': next_claimed_hashes, 'actions': [*current['actions'], action]})
    return {'status': 'PANEL_CAPACITY_NOT_CERTIFIED', 'processed_nodes': processed, 'unprocessed_legal_child': False}


def scan_forbidden_leakage(payload: Any) -> dict[str, Any]:
    detected: list[str] = []
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if 'world=' in current or 'policy=' in current:
                detected.append('direct')
            if len(current) >= 8 and len(current) % 4 == 0 and _BASE64_PATTERN.match(current):
                detected.append('base64')
        elif isinstance(current, int) and current in {52, 54, *sorted(_STALE_WORLD_SEEDS)}:
            detected.append('numeric_index')
    unique = sorted(set(detected))
    return {'clean': not unique, 'positive_controls_detected': unique}


def semantic_tamper_report(*, baseline: dict[str, Any], tampered: dict[str, Any]) -> dict[str, Any]:
    reasons = [key for key in ('search_digest', 'verdict') if baseline.get(key) != tampered.get(key)]
    return {'failed_closed': bool(reasons), 'failure_reasons': reasons, 'baseline_digest': engine.canonical_hash(baseline), 'tampered_digest': engine.canonical_hash(tampered)}
