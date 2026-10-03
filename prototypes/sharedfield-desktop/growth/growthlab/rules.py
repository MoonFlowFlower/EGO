"""Rule-card hypotheses; only this module compares their predictions to data."""
import json
from .contract import ITEMS, MATERIALS, ENTITIES, NEEDS
from .changes import cell_at, changes
from .contract import validate


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
    if not isinstance(card, dict) or set(card) != {'action', 'preconditions', 'expected', 'experiences'}: raise ValueError('rule_schema')
    if card['action'] not in actions: raise ValueError('rule_action')
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


def application(card, observation):
    """Apply a stored hypothesis, never consult a recipe or environment object."""
    obs=validate(observation);pre=card['preconditions'];front=cell_at(obs,obs['facing'])
    nearby={c['material'] for c in obs['cells'] if abs(c['dx'])<=1 and abs(c['dy'])<=1}
    checks=[]
    for item,minimum in sorted(pre['inventory_min'].items()):
        actual=obs['inventory'].get(item,0)
        checks.append({'met':actual>=minimum,'text':f'背包 {item} 至少 {minimum}，现在 {actual}'})
    for material in pre['nearby']:
        checks.append({'met':material in nearby,'text':f'身边 3×3 需要 {material}，现在'+('有' if material in nearby else '没有')})
    if pre['front_materials']:
        checks.append({'met':front['material'] in pre['front_materials'],
                       'text':f"前方材质需要 {'/'.join(pre['front_materials'])}，现在 {front['material']}"})
    if pre['front_entity'] is not None:
        actual=front['entity'] or 'none'
        checks.append({'met':actual==pre['front_entity'],'text':f"前方实体需要 {pre['front_entity']}，现在 {actual}"})
    applies=all(x['met'] for x in checks);effects=[]
    needs={'health':'血量','food':'食物','drink':'水','energy':'精力'}
    for field in ('inventory','needs'):
        for key,delta in card['expected'][field].items():
            label=needs.get(key,key) if field=='needs' else f'背包 {key}'
            effects.append(label+('不变' if delta==0 else f' {delta:+d}'))
    for key,value in card['expected']['front'].items():
        effects.append(f"前方{'材质' if key=='material' else '实体'}变为 {value if value is not None else 'none'}")
    outcome='预计'+('、'.join(effects) if applies else '没有本卡所列效果；其他后果未预测')
    explanation='；'.join(x['text']+('（满足）' if x['met'] else '（不满足）') for x in checks) or '本卡没有限制前提'
    return {'type':'action_rule_prediction','action':card['action'],'rule_id':card['id'],
            'applicable':applies,'checks':checks,'expected':card['expected'] if applies else None,
            'text':f"现在做 {card['action']}：按规则卡 {card['id']}（支持 {card.get('support',0)} 次、反例 {card.get('counterexamples',0)} 次），{explanation}；{outcome}。这是卡片预测。"}


class Rules:
    def __init__(self, store, world, actions): self.store, self.world, self.actions = store, world, actions

    def cards(self):
        # Rules describe effects, not locations. Even legacy rule records are
        # read across worlds; historical revision-2 databases are never migrated.
        rows=self.store.db.execute("SELECT id,body FROM records WHERE kind IN ('general_rule','fact') AND status='active' AND personal=0")
        return [dict(body,id=identity,scope='global') for identity,text in rows
                if (body:=json.loads(text)).get('format') in ('rule.v1','rule.v2')]

    def register(self, card, *, replaces=None):
        validate_card(card,self.actions)
        evidence=experience_rows(self.store,card['experiences'])
        old = next((r for r in self.cards() if r['id']==replaces),None) if replaces else None
        if replaces and old is None: raise ValueError('missing_rule_to_replace')
        checked=[];world_counts={};worlds=set();contradiction=False
        for identity,row in zip(card['experiences'],evidence):
            if row.get('type')!='transition' or row.get('action')!=card['action']:raise ValueError('rule_requires_action_evidence')
            before,after=validate(row['before']),validate(row['after'])
            source_world=self.store.db.execute('SELECT world FROM records WHERE id=?',(identity,)).fetchone()[0]
            if before['world']!=after['world'] or before['world']!=source_world:raise ValueError('evidence_world_mismatch')
            worlds.add(source_world)
            # Non-applicable same-action evidence may delimit a precondition or
            # refute the old rule; it never counts as support for the new rule.
            if applicable(card,before,row['action']):
                if not matches(card,before,after):raise ValueError('prediction_mismatch')
                checked.append(identity)
                world_counts.setdefault(source_world,{'support':0,'counterexamples':0})['support']+=1
            if old and applicable(old,before,row['action']) and not matches(old,before,after):contradiction=True
        if not checked:raise ValueError('no_applicable_supporting_evidence')
        if old and not contradiction:raise ValueError('replacement_requires_counterexample')
        body = dict(card,format='rule.v2',scope='global',evidence_worlds=sorted(worlds),
                    support=len(checked),counterexamples=0,checked=checked,world_counts=world_counts)
        identity = self.store.put('general_rule',body,'model_proposal',parents=card['experiences'])
        if old:
            with self.store.db:
                self.store.db.execute("INSERT INTO deps VALUES (?,?,'correction')",(identity,replaces))
                self.store.db.execute("UPDATE records SET status='superseded' WHERE id=?",(replaces,))
        return identity

    def predict(self, before, action):
        return [{'id':c['id'],'expected':c['expected']} for c in self.cards() if applicable(c,before,action)]

    def applied(self, observation):
        return [application(c,observation) for c in self.cards() if c['action'] in observation['actions']]

    def score(self, before, after, action, experience):
        experience_rows(self.store,[experience])
        scored = []
        for card in self.cards():
            if not applicable(card,before,action) or experience in card['checked']: continue
            match = bool(matches(card,before,after))
            identity = card.pop('id'); field='support' if match else 'counterexamples';card[field] += 1
            card.setdefault('world_counts',{}).setdefault(before['world'],{'support':0,'counterexamples':0})[field]+=1
            card['checked'].append(experience)
            with self.store.db:
                self.store.db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(card,ensure_ascii=False),identity))
                self.store.db.execute("INSERT OR IGNORE INTO deps VALUES (?,?,'derived')",(identity,experience))
            scored.append({'id':identity,'match':match,'expected':card['expected']})
        return scored
