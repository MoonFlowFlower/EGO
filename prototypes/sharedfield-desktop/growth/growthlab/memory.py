"""Local A/B memories. Retrieval budget and execution capabilities are shared."""
import json
import math
import re
from collections import Counter
from .decision import MEMORY_TOKENS
from .rules import Rules, experience_rows
from .skills import SkillLibrary


def compact(value): return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def tokens(text):
    text=text.lower()
    words=re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]',text)
    # Chinese unigrams and adjacent bigrams avoid an English-only baseline.
    words += [a+b for a,b in zip(words,words[1:]) if len(a)==len(b)==1 and ord(a)>127 and ord(b)>127]
    return words


def rank(query, documents):
    if not documents:return []
    terms=[Counter(tokens(text)) for _,text in documents];lengths=[sum(x.values()) for x in terms]
    average=sum(lengths)/len(lengths) or 1
    query=set(tokens(query));df={term:sum(term in d for d in terms) for term in query}
    scores=[]
    for index,d in enumerate(terms):
        score=0.
        for term in query:
            freq=d[term]
            if freq:
                idf=math.log(1+(len(terms)-df[term]+.5)/(df[term]+.5))
                score+=idf*freq*2.2/(freq+1.2*(.25+.75*lengths[index]/average))
        scores.append((score,index))
    return [(documents[i][0],score) for score,i in sorted(scores,key=lambda x:(-x[0],x[1])) if score>0]


def summary_observation(obs):
    return {'inventory':{k:v for k,v in obs['inventory'].items() if v},'needs':obs['needs'],
            'nearby':sorted({c['material'] for c in obs['cells'] if abs(c['dx'])<=1 and abs(c['dy'])<=1}),
            'visible':sorted({c['material'] for c in obs['cells']}),
            'front':next(({k:c[k] for k in ('material','entity')} for c in obs['cells'] if [c['dx'],c['dy']]==obs['facing']),None)}


def short_experience(identity,body):
    kind=body.get('type')
    if kind=='transition':
        return {'id':identity,'type':kind,'before':summary_observation(body['before']),
                'action':body['action'],'change':body['change']}
    if kind=='observation': return {'id':identity,'type':kind,'observation':summary_observation(body['observation'])}
    return dict(body,id=identity)


def all_records(store,kind=None):
    sql="SELECT id,kind,world,body,source FROM records WHERE status='active' AND personal=0"
    params=()
    if kind:sql+=' AND kind=?';params=(kind,)
    return [dict(zip(('id','kind','world','body','source'),(r[0],r[1],r[2],json.loads(r[3]),r[4]))) for r in store.db.execute(sql,params)]


def bounded(items,budget=MEMORY_TOKENS):
    # Conservative UTF-8 byte bound, not an estimate such as chars/4.
    # Includes serialized list syntax; identical in both arms. For byte/subword
    # tokenizers this bounds memory tokens from above; no tokenizer API needed.
    out=[]
    for item in items:
        if len(compact([*out,item]).encode('utf-8'))<=budget:out.append(item)
    return out


class Memory:
    def __init__(self,store,world,actions,arm,*,restarted=False):
        if arm not in ('A','B'):raise ValueError('arm')
        self.store,self.world,self.arm=store,world,arm
        self.restarted=restarted
        self.library=SkillLibrary(store,world,actions)
        self.rules=Rules(store,world,actions) if arm=='B' else None

    def profiles(self):
        profiles={}
        for row in all_records(self.store,'experience'):
            body=row['body']
            if body.get('type')!='skill_result':continue
            calls=body['result'].get('calls',[])
            dependency_versions=[(c['name'],c['version']) for c in calls]
            for call in calls:
                if call['name']=='<inline>':continue
                key=f"{call['name']}@{call['version']}"
                p=profiles.setdefault(key,{'attempts':0,'success':0,'unsuccessful':0,'not_needed':0,
                    'independent_success_worlds':[],'worlds':[],'taught_runs':0,'takeovers':0,
                    'execution_status':{},'dependency_versions':[],'contexts':[],'restart_attempts':0,
                    'restart_successes':0,'certification':None})
                p[call['outcome']]+=1
                if call['outcome']!='not_needed':p['attempts']+=1
                if call['outcome']=='success' and row['world'] not in p['independent_success_worlds']:p['independent_success_worlds'].append(row['world'])
                if row['world'] not in p['worlds']:p['worlds'].append(row['world'])
                p['taught_runs']+=bool(body.get('taught'));p['takeovers']+=bool(body.get('takeover'))
                context=body.get('context',{})
                if context and context not in p['contexts']:p['contexts'].append(context)
                if context.get('restarted') and call['outcome']!='not_needed':
                    p['restart_attempts']+=1;p['restart_successes']+=call['outcome']=='success'
                status=call.get('execution_status','not_needed');p['execution_status'][status]=p['execution_status'].get(status,0)+1
                if dependency_versions not in p['dependency_versions']:p['dependency_versions'].append(dependency_versions)
        return profiles

    def self_model(self):
        transitions=[r['body'] for r in all_records(self.store,'experience') if r['body'].get('type')=='transition']
        actions=Counter(b['action'] for b in transitions);events=Counter(e for b in transitions for e in b['change']['events'])
        profiles=self.profiles()
        return {'type':'self_statistics','observed_actions':dict(actions),'events':dict(events),
                'skill_attempts':sum(p['attempts'] for p in profiles.values()),
                'skill_successes':sum(p['success'] for p in profiles.values()),
                'scope':'descriptive counts; no capability certification; no inferred emotion'}

    def retrieve(self,obs,goal):
        query=goal+' '+compact(summary_observation(obs))
        skills=list(self.library.current().values())
        # Callable names available equally; source programs also retrievable.
        index={'type':'skill_index','skills':[{k:s[k] for k in ('name','version','description','completion')} for s in skills]}
        if self.arm=='B':
            cards=[{k:v for k,v in c.items() if k not in ('checked','format')} for c in self.rules.cards()]
            ordered=[cards[i] for i,_ in rank(query,[(i,compact(c)) for i,c in enumerate(cards)])]
            stats=self.self_model();profile=self.profiles()
            # Evaluate EVERY card before ranking/packing. The same memory cap
            # applies; compact action-linked prose takes priority over raw cards.
            applications=self.rules.applied(obs)
            lookup={p['rule_id']:p for p in applications}
            predictions=[{'type':'action_rule_prediction','action':c['action'],'text':lookup[c['id']]['text']} for c in ordered]
            return bounded(predictions+[{'type':'rule_card',**c} for c in ordered]+[index,stats]+[{'type':'skill','program':s,'profile':profile.get(f"{s['name']}@{s['version']}",{})} for s in skills])
        docs=[]
        for row in all_records(self.store):
            if row['kind']=='experience':
                body=short_experience(row['id'],row['body'])
            elif row['kind'] in ('reflection','skill'):body=dict(row['body'],id=row['id'])
            else:continue
            doc={'type':row['kind'],'content':body}
            docs.append((doc,compact(doc)))
        return bounded([index]+[doc for doc,_ in rank(query,docs)])

    def reflect(self,text,experiences):
        if type(text) is not str or not text.strip() or len(text)>6000:raise ValueError('reflection_schema')
        experience_rows(self.store,experiences)
        return self.store.put('reflection',{'text':text},'model_reflection',parents=experiences)

    def export(self):
        return {'arm':self.arm,'records':all_records(self.store),
                'profiles':self.profiles() if self.arm=='B' else None,
                'self':self.self_model() if self.arm=='B' else None}
