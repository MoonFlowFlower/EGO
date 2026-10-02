"""Rule-card hypotheses; only this module compares their predictions to data."""
import json
from .contract import ITEMS, MATERIALS, ENTITIES, NEEDS
from .changes import cell_at, changes


def experience_rows(store, ids, world=None):
    if not isinstance(ids, list) or not ids or len(ids) > 64 or len(set(ids)) != len(ids): raise ValueError('experience_required')
    rows = []
    for identity in ids:
        row = store.db.execute("SELECT kind,world,body FROM records WHERE id=? AND status='active' AND personal=0", (identity,)).fetchone()
        if not row or row[0] != 'experience': raise ValueError('unknown_experience')
        if world is not None and row[1] != world: raise ValueError('scope_leak')
        rows.append(json.loads(row[2]))
    return rows


def validate_card(card, actions):
    if not isinstance(card, dict) or set(card) != {'action', 'preconditions', 'expected', 'scope', 'experiences'}: raise ValueError('rule_schema')
    if card['action'] not in actions or card['scope'] not in ('global', 'world'): raise ValueError('rule_action_or_scope')
    pre, expected = card['preconditions'], card['expected']
    if not isinstance(pre, dict) or set(pre) != {'inventory_min','nearby','front_materials','front_entity'}: raise ValueError('precondition_schema')
    if not isinstance(pre['inventory_min'],dict) or any(k not in ITEMS or type(v) is not int or not 0 <= v <= 9 for k,v in pre['inventory_min'].items()): raise ValueError('inventory_precondition')
    for field in ('nearby','front_materials'):
        if not isinstance(pre[field],list) or any(x not in MATERIALS for x in pre[field]): raise ValueError('material_precondition')
    if pre['front_entity'] not in (None,'none',*ENTITIES): raise ValueError('entity_precondition')
    if not isinstance(expected,dict) or set(expected) != {'inventory','needs','front'}: raise ValueError('expected_schema')
    for field, allowed in [('inventory',ITEMS),('needs',NEEDS)]:
        if not isinstance(expected[field],dict) or any(k not in allowed or type(v) is not int or not -9 <= v <= 9 for k,v in expected[field].items()): raise ValueError('expected_delta')
    front = expected['front']
    if not isinstance(front,dict) or set(front)-{'material','entity'}: raise ValueError('expected_front')
    if 'material' in front and front['material'] not in MATERIALS: raise ValueError('expected_material')
    if 'entity' in front and front['entity'] not in (None,*ENTITIES): raise ValueError('expected_entity')
    if not any(expected.values()): raise ValueError('empty_prediction')


def applicable(card, obs, action):
    if action != card['action']: return False
    pre = card['preconditions']; front = cell_at(obs,obs['facing'])
    nearby = {c['material'] for c in obs['cells'] if abs(c['dx']) <= 1 and abs(c['dy']) <= 1}
    return (all(obs['inventory'].get(k,0) >= v for k,v in pre['inventory_min'].items())
            and set(pre['nearby']) <= nearby
            and (not pre['front_materials'] or front['material'] in pre['front_materials'])
            and (pre['front_entity'] is None or front['entity'] == (None if pre['front_entity']=='none' else pre['front_entity'])))


def matches(card, before, after):
    expected = card['expected']
    for field in ('inventory','needs'):
        if any(after[field].get(k,0)-before[field].get(k,0) != v for k,v in expected[field].items()): return False
    target = [before['facing'][i]-after['displacement'][i] for i in (0,1)]
    front = cell_at(after,target)
    return not expected['front'] or (front is not None and all(front[k] == v for k,v in expected['front'].items()))


class Rules:
    def __init__(self, store, world, actions): self.store, self.world, self.actions = store, world, actions

    def cards(self):
        return [dict(r['body'],id=r['id']) for r in self.store.load(self.world)
                if r['kind'] in ('general_rule','fact') and r['body'].get('format') == 'rule.v1']

    def register(self, card, *, replaces=None):
        validate_card(card,self.actions)
        world = self.world if card['scope']=='world' else None
        experience_rows(self.store,card['experiences'],world)
        old = next((r for r in self.cards() if r['id']==replaces),None) if replaces else None
        if replaces and (old is None or old['scope'] != card['scope']): raise ValueError('correction_scope')
        body = dict(card,format='rule.v1',support=0,counterexamples=0,checked=[])
        identity = self.store.put('general_rule' if world is None else 'fact',body,'model_proposal',world=world,parents=card['experiences'])
        if old:
            with self.store.db:
                self.store.db.execute("INSERT INTO deps VALUES (?,?,'correction')",(identity,replaces))
                self.store.db.execute("UPDATE records SET status='superseded' WHERE id=?",(replaces,))
        return identity

    def predict(self, before, action):
        return [{'id':c['id'],'expected':c['expected']} for c in self.cards() if applicable(c,before,action)]

    def score(self, before, after, action, experience):
        experience_rows(self.store,[experience])
        scored = []
        for card in self.cards():
            if not applicable(card,before,action) or experience in card['checked']: continue
            match = bool(matches(card,before,after))
            identity = card.pop('id'); card['support' if match else 'counterexamples'] += 1
            card['checked'].append(experience)
            with self.store.db:
                self.store.db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(card,ensure_ascii=False),identity))
                self.store.db.execute("INSERT OR IGNORE INTO deps VALUES (?,?,'derived')",(identity,experience))
            scored.append({'id':identity,'match':match,'expected':card['expected']})
        return scored
