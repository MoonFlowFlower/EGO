"""Deterministic bounded scene for model verification, never a Minecraft client."""
import concurrent.futures
import math

from .verify_turn_v2 import InterruptedBody


class SceneBody(InterruptedBody):
    def block(self, position):
        xyz = tuple(position[k] for k in ('x', 'y', 'z'))
        return self.blocks.get(xyz, 'stone' if position['y'] <= 63 else 'air')

    def start_action(self, action, **kw):
        name, args = action['name'], action['args']
        if name == 'inspect_area':
            radius = args['radius']
            if type(radius) is not int or not 1 <= radius <= 4:
                raise ValueError('invalid_radius')
            self.actions.append(action)
            center = {k: math.floor(v) for k, v in self.state['position'].items()}
            cells = []
            for dx in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    for dy in range(-1, 3):
                        p = {'x': center['x'] + dx, 'y': center['y'] + dy, 'z': center['z'] + dz}
                        cells.append([p['x'], p['y'], p['z'], self.block(p)])
            future = concurrent.futures.Future()
            future.set_result({'verified': True, 'status': 'local_area_observed', 'scope': 'loaded_chunks_only',
                               'center': center, 'cells': cells, 'observed': self.snapshot()})
            return future
        if name in ('place', 'place_at'):
            p = args.get('position', {'x': len(self.blocks) + 1, 'y': 64, 'z': 0})
            if (args['block'] != 'oak_planks' or self.state['inventory'].get('oak_planks', 0) <= 0
                    or self.block(p) != 'air' or self.block({**p, 'y': p['y'] - 1}) == 'air'):
                raise RuntimeError('invalid_simulated_placement')
            # The test fixture's placement and readback share canonical xyz order.
            action = {'name': name, 'args': {**args, **({'position': {k: p[k] for k in ('x', 'y', 'z')}} if name == 'place_at' else {})}}
        elif name == 'verify_blocks':
            action = {'name': name, 'args': {'targets': [{**t, 'position': {k: t['position'][k] for k in ('x', 'y', 'z')}} for t in args['targets']]}}
        return super().start_action(action, **kw)
