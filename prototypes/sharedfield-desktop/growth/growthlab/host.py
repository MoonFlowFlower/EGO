"""Trusted sensor/actuator driver, never exposed as a skill object.

Only this boundary reads local tile occupancy, player inventory/facing and
position (for local sampling and displacement). No full semantic map is used.
"""
import uuid
from .runtime import GrowthEnv
from .contract import ACTIONS, ITEMS, MATERIALS, ENTITIES, NEEDS, validate, public_action
from .changes import changes


class Host:
    def __init__(self, seed=11, length=300, aliases=None):
        self.env = GrowthEnv(seed=seed, length=length)
        # Disable upstream full-map info construction in the live policy path.
        self.env._sem_view = lambda: None
        self.aliases = aliases or {}
        self.actions = [self.aliases.get(x,x) for x in ACTIONS]
        if len(set(self.actions)) != len(ACTIONS): raise ValueError('action_alias_collision')
        self.action_indices = {public: i for i, public in enumerate(self.actions)}
        if aliases: self.actions.sort()  # Do not leak the original action order.
        self.done = False
        self.world = uuid.uuid4().hex  # opaque; no seed or rule identity
        self.last_frame = self.env.reset().copy()
        self.previous = self.env._player.pos.copy()
        self.delta = [0,0]
        self.last_event = None

    def observe(self):
        p = self.env._player
        light = float(self.env._world.daylight)
        radius = 4 if light >= .5 else (2 if light >= .2 else 1)
        cells = []
        for dx in range(-radius,radius+1):
            for dy in range(-min(radius,3),min(radius,3)+1):
                material, obj = self.env._world[p.pos + (dx,dy)]
                material = material if material in MATERIALS else 'unknown'
                entity = type(obj).__name__.lower() if obj else None
                if entity not in ENTITIES: entity = None
                visible_state=None
                if entity=='plant':visible_state={'plant_ripe':obj.texture=='plant-ripe'}
                if entity=='arrow':visible_state={'arrow_direction':obj.texture.removeprefix('arrow-')}
                cells.append({'dx':dx,'dy':dy,'material':self.aliases.get(material,material),
                              'entity':self.aliases.get(entity,entity),'visible_state':visible_state})
        return validate({'schema':'growth.obs.v1.1','tick':int(self.env._step),'world':self.world,
            'needs':{k:int(p.inventory[k]) for k in NEEDS},
            'inventory':{self.aliases.get(k,k):int(p.inventory[k]) for k in ITEMS},
            'light':round(light,4),'radius':radius,'cells':cells,
            'displacement':list(self.delta),'facing':list(p.facing),'sleeping':bool(p.sleeping),
            'done':bool(self.done),'actions':self.actions.copy()})

    def act(self, action):
        public_action(action,self.actions)
        if self.done: raise ValueError('episode_finished')
        observation_before = self.observe()
        before = self.env._player.pos.copy()
        frame, _, self.done, _ = self.env.step(self.action_indices[action])
        self.last_frame=frame.copy()
        self.delta = [int(v) for v in self.env._player.pos - before]
        observation_after = self.observe()
        self.last_event = changes(observation_before, observation_after, action)
        return observation_after

    def render(self):
        return self.env.render((512,512))  # owner-only; callers serialize access


def walk_until(host, direction, material, max_steps=8):
    """Inherited bounded macro; observes only v1 fields, stops at target/block/done."""
    if direction not in ('move_left','move_right','move_up','move_down'): raise ValueError('macro_direction')
    if type(max_steps) is not int or not 1 <= max_steps <= 8: raise ValueError('macro_limit')
    used = 0
    for _ in range(max_steps):
        obs = host.observe()
        if obs['done'] or any(c['material'] == material for c in obs['cells']): break
        obs = host.act(direction); used += 1
        if obs['displacement'] == [0,0] or 'health_lost' in host.last_event['events']: break
    return used
