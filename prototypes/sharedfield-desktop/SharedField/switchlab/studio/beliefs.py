"""Source-separated claims. An extraction is not a truth oracle or a ToM proof."""
from __future__ import annotations
from copy import deepcopy
import math
from .protocol import text, obj, arr
from .learning import text_vector

class BeliefGraph:
    def __init__(self):self.claims=[]
    def add(self,items,sources):
        new=[]
        for item in arr(items,6,'claims'):
            obj(item,('holder','subject','relation','value','source','quote','confidence'),
                ('holder','subject','relation','value','source','quote'))
            h=text(item['holder'],'holder',80)
            if h not in ('user','self','world') and not h.startswith('other:'):raise ValueError('holder must distinguish self/user/world/other:name')
            sid=item['source'];quote=text(item['quote'],'quote',600)
            if sid not in sources or quote not in sources[sid]:raise ValueError('claim must quote an exact substring of a real source')
            fields={k:text(item[k],k,n) for k,n in [('subject',100),('relation',100),('value',800)]}
            confidence=item.get('confidence',.5)
            if type(confidence) not in (float,int) or not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError('confidence 0..1')
            same=next((c for c in self.claims if c['holder']==h and all(c[k]==v for k,v in fields.items()) and c['status']!='withdrawn'),None)
            provenance={'source':sid,'quote':quote}
            if same:
                if provenance not in same['sources']:same['sources'].append(provenance)
                # Repetition neither votes a claim true nor increases confidence.
                continue
            if len(self.claims)>=600:raise ValueError('belief capacity reached; export this life')
            c={**fields,'holder':h,'id':f'B{len(self.claims)+1:04d}','sources':[provenance],
               'confidence':float(confidence),'confidence_origin':'language_model_estimate',
               'verification':'unverified_extraction','status':'open','corrections':[]}
            self.claims.append(c);new.append(c['id'])
        return new
    def conflicts(self):
        groups={}
        for c in self.claims:
            if c['status']=='withdrawn':continue
            key=(c['holder'],c['subject'],c['relation']);groups.setdefault(key,[]).append(c)
        return [{'holder':h,'subject':s,'relation':r,'claims':[x['id'] for x in cs],
                 'values':[x['value'] for x in cs],'sources':sorted({p['source'] for c in cs for p in c['sources']}),
                 'meaning':'possible conflict or change, not an automatic contradiction verdict'}
                for (h,s,r),cs in groups.items() if len({c['value'] for c in cs})>1]
    def resolve(self,claim_id,action,source):
        c=next((c for c in self.claims if c['id']==claim_id),None)
        if not c or action not in ('withdraw','confirm'):raise ValueError('unknown claim or correction action')
        c['status']='withdrawn' if action=='withdraw' else 'confirmed_report'
        c['verification']='user_corrected_report_not_world_ground_truth'
        c['corrections'].append({'source':source,'action':action})
    def retrieve(self,query,limit=18):
        v=text_vector(query)
        def score(c):
            t=text_vector(c['subject']+' '+c['relation']+' '+c['value'])
            return sum(a*b for a,b in zip(v,t))
        items=[c for c in self.claims if c['status']!='withdrawn']
        return deepcopy(sorted(items,key=score,reverse=True)[:limit])
    def snapshot(self):return {'claims':deepcopy(self.claims)}
    @classmethod
    def restore(cls,data):
        if not isinstance(data,dict) or not isinstance(data.get('claims'),list) or len(data['claims'])>600:raise ValueError('belief snapshot')
        g=cls();g.claims=deepcopy(data['claims']);return g
