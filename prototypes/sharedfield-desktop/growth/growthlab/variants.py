"""Trusted-only development variants; never put rules/seeds in a policy prompt."""
import copy
import random
from crafter import constants, objects
from .contract import ACTIONS,ITEMS,MATERIALS,ENTITIES
from .host import Host


def generate(kind,seed):
    rng=random.Random(seed)
    rules={'make':copy.deepcopy(constants.make),'collect':copy.deepcopy(constants.collect),'aliases':{}}
    if kind=='rename_actions':
        names=[x for x in ACTIONS if x.startswith(('place_','make_'))]
        ids=list(range(10));rng.shuffle(ids)
        rules['aliases']={k:f's{v:03}' for k,v in zip(names,ids)}
    elif kind=='rename':
        names=sorted(set(ACTIONS+ITEMS+MATERIALS+ENTITIES)); ids=list(range(len(names)));rng.shuffle(ids)
        rules['aliases']={k:f's{v:03}' for k,v in zip(names,ids)}
    elif kind=='recipe':
        rules['make']['wood_pickaxe']['uses']={'wood':rng.randint(2,3)}
        rules['make']['wood_pickaxe']['nearby']=[rng.choice(['table','furnace'])]
    elif kind=='consequence':
        rules['collect']['tree']['receive']['wood']=rng.choice([2,3])
    elif kind=='composition':
        rules['make']['wood_sword']['uses']={'wood':rng.randint(2,3),'wood_pickaxe':1}
        rules['make']['wood_sword']['nearby']=['table','furnace']
    else: raise ValueError('unknown_variant')
    return rules


def check_rules(rules):
    # Inventory constraints plus prerequisite closure, not a universal planner.
    reachable={'wood','sapling','drink'}; reasons=[]
    for name,recipe in rules['make'].items():
        if any(k not in constants.items or type(v) is not int or not 0<v<=9 for k,v in recipe['uses'].items()): reasons.append('inventory_bound')
        if any(x not in ('table','furnace') for x in recipe['nearby']): reasons.append('unknown_station')
    changed=True
    while changed:
        old=set(reachable)
        stations=set()
        if 'wood' in reachable: stations.add('table')
        if 'stone' in reachable: stations.add('furnace')
        for material,rule in rules['collect'].items():
            if set(rule['require'])<=reachable: reachable.update(rule['receive'])
        for item,rule in rules['make'].items():
            if set(rule['uses'])<=reachable and set(rule['nearby'])<=stations: reachable.add(item)
        changed=reachable!=old
    if 'wood_pickaxe' not in reachable or 'wood_sword' not in reachable: reasons.append('unreachable_dependency')
    return {'accepted':not reasons,'reasons':sorted(set(reasons)),'scope':'dependency/capacity; arena witness separately required'}


class VariantPlayer(objects.Player):
    def _make(self,name):
        nearby,_=self.world.nearby(self.pos,1)
        info=self.growth_rules['make'][name]
        if not all(x in nearby for x in info['nearby']): return
        if any(self.inventory[k]<v for k,v in info['uses'].items()): return
        for k,v in info['uses'].items(): self.inventory[k]-=v
        self.inventory[name]+=info['gives'];self.achievements[f'make_{name}']+=1

    def _do_material(self,target,material):
        if material=='water': self._thirst=0
        info=self.growth_rules['collect'].get(material)
        if not info or any(self.inventory[k]<v for k,v in info['require'].items()): return
        self.world[target]=info['leaves']
        if self.random.uniform()<=info.get('probability',1):
            for k,v in info['receive'].items():
                self.inventory[k]+=v;self.achievements[f'collect_{k}']+=1


def arena(rules):
    """Evaluator-constructed small solvable fixture, not a sampled natural world."""
    h=Host(aliases=rules['aliases']);p=h.env._player;w=h.env._world
    for obj in w.objects:
        if obj is not p:w.remove(obj)
    for dx in range(-5,6):
        for dy in range(-5,6):w[p.pos+(dx,dy)]='grass'
    for delta,material in [((-1,0),'table'),((-1,-1),'furnace'),((1,0),'tree'),((0,1),'tree'),((0,-1),'tree')]:w[p.pos+delta]=material
    p.inventory['wood']=2
    p.__class__=VariantPlayer;p.growth_rules=copy.deepcopy(rules)
    h.env._balance_chunk=lambda *args:None  # fixed fixture; no spawn noise
    return h
