"""One bounded end-of-episode call. Proposals never supply truth counts."""
import json
from .contract import ITEMS, MATERIALS, ENTITIES, NEEDS
from .decision import obj, string, format_schema
from .memory import all_records, short_experience, compact
from .rules import experience_rows

B_SYSTEM = '''Consolidate this episode into candidate rule cards and reusable skill programs.
Use only the supplied allowed experiences and public action names. Each proposal
must cite one or more supplied experience IDs. A citation is provenance, not proof.
Rules predict exact deltas only for named inventory/need fields, and/or the final
contents of the same facing tile. Preconditions: inventory minimums, materials
within 3x3, facing materials (any one), facing entity (empty=unconstrained,
none=no entity). Expected facing fields empty=unconstrained, entity none=no entity.
Use scope global for a proposed general rule, world only for a fact confined to
this world. Counts are computed by the program, never claim support yourself.
If evidence does not warrant a proposal, return an empty list. Use replaces only
for an existing rule ID to correct. Rules are hypotheses and may have counterexamples.
Skills use the same closed language: act, run, observe, seen, count, need,
comparisons, and/or/not, if/while, for _ in range(N<=32); no variables/arithmetic.
Every skill needs a boolean completion condition. No recursion; depth <=3.
Do not invent observations, teaching, action meanings or experience IDs.'''
A_SYSTEM = '''Write one plain-text reflection about this episode, for later BM25 retrieval.
Use only supplied allowed experiences. Describe useful observations, mistakes,
uncertainties and possible next steps, with relevant public action/item names.
Do not invent events or treat guesses as facts. No rule cards or self ratings.
Return JSON with reflection only. Keep it concise enough to retrieve later.'''


def array(item,limit=6):return {'type':'array','items':item,'maxItems':limit}


def sleep_format(arm,actions):
    if arm=='A':return format_schema('reflection',obj({'reflection':string(6000)}))
    ids=array(string(32),12)
    rules=obj({'action':string(enum=actions),'inventory_min':array(obj({'item':string(enum=list(ITEMS)),'count':{'type':'integer','minimum':0,'maximum':9}}),12),
        'nearby':array(string(enum=list(MATERIALS)),9),'front_materials':array(string(enum=list(MATERIALS)),13),
        'front_entity':string(enum=['','none',*ENTITIES]),
        'inventory_delta':array(obj({'item':string(enum=list(ITEMS)),'delta':{'type':'integer','minimum':-9,'maximum':9}}),12),
        'needs_delta':array(obj({'need':string(enum=list(NEEDS)),'delta':{'type':'integer','minimum':-9,'maximum':9}}),4),
        'front_material':string(enum=['',*MATERIALS]),'expected_front_entity':string(enum=['','none',*ENTITIES]),
        'scope':string(enum=['global','world']),'experiences':ids,'replaces':string(32)})
    skills=obj({'name':string(64),'description':string(),'source':string(8192),'completion':string(512),'experiences':ids})
    return format_schema('consolidation',obj({'rules':array(rules),'skills':array(skills,4)}))


def packet(episode):
    allowed=set(episode.experiences)
    rows=[r for r in all_records(episode.store,'experience') if r['id'] in allowed and r['body'].get('type') in ('transition','teaching','skill_result')]
    teaching=[r for r in rows if r['body'].get('type')=='teaching']
    steps=[r for r in rows if r['body'].get('type')=='transition']
    informative=[r for r in steps if r['body']['change']['effects']['inventory'] or r['body']['change']['effects']['consumption']]
    # Same deterministic evidence selection in A and B, before seeing proposals.
    # Include ending evidence before repeated early attempts can fill the budget.
    # Remaining steps are sampled across the whole episode, not cherry-picked
    # using target-rule correctness or the eventual test outcome.
    stride=max(1,len(steps)//32)
    ordered=teaching+steps[-8:]+steps[:8]+informative+steps[::stride]
    selected=[];seen=set()
    for row in ordered:
        if row['id'] in seen:continue
        value=short_experience(row['id'],row['body'])
        if len(json.dumps(selected+[value]).encode())>24000:continue
        selected.append(value);seen.add(row['id'])
    return selected


def apply_proposals(memory,proposal,allowed_ids):
    results=[]
    if memory.arm=='A':
        if set(proposal)!={'reflection'}:raise ValueError('reflection_schema')
        identity=memory.reflect(proposal['reflection'],list(allowed_ids)[:64])
        return [{'type':'reflection','accepted':True,'id':identity}]
    if not isinstance(proposal,dict) or set(proposal)!={'rules','skills'}:raise ValueError('consolidation_schema')
    if not isinstance(proposal['rules'],list) or not isinstance(proposal['skills'],list) or len(proposal['rules'])>6 or len(proposal['skills'])>4:raise ValueError('proposal_limit')
    for kind in ('rules','skills'):
        for item in proposal[kind]:
            try:
                ids=item['experiences']
                if not isinstance(ids,list) or not set(ids)<=set(allowed_ids):raise ValueError('unsupplied_experience')
                experience_rows(memory.store,ids)
                if kind=='rules':
                    expected_fields={'action','inventory_min','nearby','front_materials','front_entity','inventory_delta','needs_delta','front_material','expected_front_entity','scope','experiences','replaces'}
                    if set(item)!=expected_fields:raise ValueError('rule_proposal_schema')
                    front={}
                    if item['front_material']:front['material']=item['front_material']
                    if item['expected_front_entity']:front['entity']=None if item['expected_front_entity']=='none' else item['expected_front_entity']
                    card={'action':item['action'],'scope':item['scope'],'experiences':ids,
                          'preconditions':{'inventory_min':{x['item']:x['count'] for x in item['inventory_min']},
                            'nearby':item['nearby'],'front_materials':item['front_materials'],'front_entity':item['front_entity'] or None},
                          'expected':{'inventory':{x['item']:x['delta'] for x in item['inventory_delta']},
                            'needs':{x['need']:x['delta'] for x in item['needs_delta']},'front':front}}
                    identity=memory.rules.register(card,replaces=item['replaces'] or None)
                else:
                    if set(item)!={'name','description','source','completion','experiences'}:raise ValueError('skill_proposal_schema')
                    identity=memory.library.register(item['name'],item['description'],item['source'],item['completion'],parents=ids)['id']
                results.append({'type':kind,'accepted':True,'id':identity})
            except (ValueError,KeyError,TypeError):results.append({'type':kind,'accepted':False,'reason':'invalid_proposal_or_provenance','proposal':json.loads(json.dumps(item))})
    return results


def consolidate(episode):
    evidence=packet(episode)
    if not evidence:return {'status':'no_experiences','results':[]}
    memory=episode.memory
    # Previous memories share the SAME budget as decision-time retrieval.
    prompt=[{'role':'system','content':B_SYSTEM if memory.arm=='B' else A_SYSTEM},
            {'role':'user','content':compact({'goal':episode.goal,'actions':episode.host.actions,
                'memory':memory.retrieve(episode.host.observe(),episode.goal),'experiences':evidence})}]
    episode.write({'type':'sleep_input','messages':prompt})
    content,meta=episode.client.decide(prompt,response_format=sleep_format(memory.arm,episode.host.actions),max_tokens=2048)
    episode.calls.append(dict(meta,purpose='consolidation'))
    try:results=apply_proposals(memory,json.loads(content),[e['id'] for e in evidence])
    except (ValueError,KeyError,TypeError):results=[{'accepted':False,'reason':'invalid_consolidation'}]
    episode.write({'type':'sleep_result','output':content,'results':results,'meta':meta})
    return {'status':'returned','results':results,'output':content,'meta':meta,'supplied_experiences':[e['id'] for e in evidence]}
