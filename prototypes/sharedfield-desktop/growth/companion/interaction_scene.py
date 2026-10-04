"""Deterministic body for interaction checks; no Minecraft connection."""
import concurrent.futures
import copy
import math
import threading
from .test_harness import Body
from .interaction import item_matches


class InteractionScene(Body):
    def __init__(self, *, hold=None, items=True):
        super().__init__()
        self.state['inventory'] = {'oak_planks': 2}
        self.state['owner'] = {'name': 'Moonlight', 'position': {'x': 4, 'y': 64, 'z': 0}}
        self.state['dropped_items'] = {'scope': 'visible_entities_only', 'origin': 'dropper_unknown', 'range': 16,
            'items': [self.item(41, 4)] if items else []}
        self.hold = hold
        self.entered = threading.Event()
        self.pending = None

    @staticmethod
    def item(identity, x):
        return {'entity_id': identity, 'entity_key': f'fixture:{identity}', 'item': 'oak_log', 'count': 8,
                'position': {'x': x, 'y': 64, 'z': 0}, 'distance': abs(x)}

    def snapshot(self):
        state = super().snapshot()
        owner = state['owner']
        owner['distance'] = math.dist(list(state['position'].values()), list(owner['position'].values()))
        owner['height_difference'] = abs(state['position']['y'] - owner['position']['y'])
        return state

    def release(self):
        if self.pending and not self.pending[0].done():
            self.pending[0].set_result(self.pending[1])

    def start_action(self, action, **kw):
        name, args = action['name'], action['args']
        if name in ('inspect', 'observe_items', 'approach', 'pickup_items', 'search'):
            self.actions.append(copy.deepcopy(action))
            receipt = {'verified': True, 'status': 'observed'}
            if name == 'approach':
                self.state['position'] = {**self.state['owner']['position'], 'x': self.state['owner']['position']['x'] - 1}
                receipt['status'] = 'approach_checked'
            elif name == 'observe_items':
                receipt.update(status='items_observed', dropped_items=copy.deepcopy(self.state['dropped_items']))
            elif name == 'pickup_items':
                entities = {e['entity_id']: e for e in self.state['dropped_items']['items']}
                if not set(args['entity_ids']) <= set(entities):
                    receipt = {'verified': False, 'status': 'pickup_target_missing'}
                else:
                    events, gained = [], {}
                    for identity in args['entity_ids']:
                        e = entities[identity]
                        if not item_matches(args['item'], e['item']):
                            raise ValueError('scene_item_mismatch')
                        events.append({k: e[k] for k in ('entity_id', 'entity_key', 'item', 'count')})
                        self.state['position'] = {**e['position'], 'x': e['position']['x'] - .5}
                        gained[e['item']] = gained.get(e['item'], 0) + e['count']
                        self.state['inventory'][e['item']] = self.state['inventory'].get(e['item'], 0) + e['count']
                    self.state['dropped_items']['items'] = [e for e in entities.values() if e['entity_id'] not in args['entity_ids']]
                    receipt.update(status='pickup_checked', evidence='self_collect_events_and_inventory',
                                   pickup_events=events, inventory_gained=gained, gained=sum(gained.values()))
            elif name == 'search':
                receipt.update(status='block_located', found=True, block_position={'x': 100, 'y': 64, 'z': 0})
            receipt['observed'] = self.snapshot()
            future = concurrent.futures.Future()
            if name == self.hold and not self.entered.is_set():
                self.pending = (future, receipt); self.entered.set()
            else:
                future.set_result(receipt)
            return future
        if name in ('go_to_block', 'collect'):
            raise AssertionError('scene_forbids_tree_substitution')
        future = super().start_action(action, **kw)
        if name == self.hold and not self.entered.is_set():
            held = concurrent.futures.Future(); self.pending = (held, future.result()); self.entered.set()
            return held
        return future
