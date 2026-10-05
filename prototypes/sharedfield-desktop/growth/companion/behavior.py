"""Finite, memoryful behavior trees over fixed predicates and body actions.

Trees are data. There are no expressions, imports, user functions or loops.
Action outcomes and cursors are persisted with the work, never replayed on boot.
"""
import copy
from .work import validate_action, validate_goal, preliminary_completion
from .engine import completed_negative_search


def validate_tree(tree):
    identities = set()
    def visit(node, depth):
        if not isinstance(node, dict) or depth > 6:
            raise ValueError('tree_depth_or_node')
        identity, kind = node.get('id'), node.get('type')
        if not isinstance(identity, str) or not 1 <= len(identity) <= 40 or identity in identities:
            raise ValueError('tree_node_id')
        identities.add(identity)
        if len(identities) > 32:
            raise ValueError('tree_node_cap')
        if kind in ('sequence', 'fallback') and set(node) == {'id', 'type', 'children'}:
            children = node['children']
            if not isinstance(children, list) or not 1 <= len(children) <= 8:
                raise ValueError('tree_children')
            for child in children: visit(child, depth + 1)
        elif kind == 'action' and set(node) == {'id', 'type', 'action'}:
            validate_action(node['action'])
        elif kind == 'condition' and set(node) == {'id', 'type', 'condition'}:
            condition = node['condition']
            goal = validate_goal({'title': 'condition', 'steps': ['observe'], 'done_when': [condition]})
            if goal['done_when'][0]['kind'] not in ('inventory', 'inventory_clear', 'near_owner'):
                raise ValueError('tree_condition_not_observable')
        else:
            raise ValueError('tree_node_schema')
    visit(tree, 0)
    return copy.deepcopy(tree)


def next_action(policy, state):
    """Return one leaf or a terminal status; never execute an action here."""
    outcomes = policy.setdefault('outcomes', {})
    def visit(node):
        identity = node['id']
        if identity in outcomes:
            return outcomes[identity], None
        if node['type'] == 'action':
            return 'running', node
        if node['type'] == 'condition':
            condition = node['condition']
            required = {'inventory': ('inventory',), 'inventory_clear': ('crafting_grid', 'cursor', 'window'),
                        'near_owner': ('owner',)}[condition['kind']]
            known = all(key in state for key in required)
            work = {'done_when': [condition]}
            ok = known and preliminary_completion(work, state)['satisfied']
            outcomes[identity] = 'success' if ok else 'failure'
            return outcomes[identity], None
        sequence = node['type'] == 'sequence'
        for child in node['children']:
            status, pending = visit(child)
            if pending: return status, pending
            if status == ('failure' if sequence else 'success'):
                outcomes[identity] = status
                return status, None
        outcomes[identity] = 'success' if sequence else 'failure'
        return outcomes[identity], None
    status, node = visit(policy['tree'])
    policy['status'] = status
    policy['pending'] = node['id'] if node else None
    return copy.deepcopy(node['action']) if node else None


def accept_result(policy, action, receipt):
    pending = policy.get('pending')
    if pending:
        ok = receipt.get('verified') is True or completed_negative_search(action, receipt)
        policy.setdefault('outcomes', {})[pending] = 'success' if ok else 'failure'
        policy['pending'] = None


def actions(tree):
    if tree['type'] == 'action':
        yield tree['action']
    for child in tree.get('children', []):
        yield from actions(child)
