"""Bounded online outcome learning; scores are predictions, never terminal values.

A small backprop network competes with a similarity predictor using prequential
errors on real, unique samples. Replaying does not add evidence or validation
points. Synthetic demonstrations are never injected into a fresh user's life.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import math
import re
from .neural import TinyNet, vector

INPUTS, OUTPUTS = 80, 27
WEIGHTS = (.5, .3, .2)  # Engineered objective: task, constraints, understanding.

def text_vector(text, size=24):
    if not isinstance(text,str):text=str(text)
    text=text[:16000].lower()
    tokens=re.findall(r'[a-z0-9_]+|[\u3400-\u9fff]',text)
    chars=''.join(t for t in tokens if len(t)==1 and '\u3400'<=t<='\u9fff')
    tokens += [chars[i:i+2] for i in range(max(0,len(chars)-1))]
    out=[0.]*size
    for token in tokens:
        h=hashlib.blake2s(token.encode(),digest_size=8).digest()
        out[int.from_bytes(h[:4],'big')%size]+=1 if h[4]&1 else -1
    norm=math.sqrt(sum(v*v for v in out))
    return [v/max(1.,norm) for v in out]

def features(context, action, state):
    """Feature hashing is a bounded lexical representation, not semantic understanding."""
    x=text_vector(context,48)+text_vector(action,24)
    names=('uncertainty','commitments','conflicts','budget_used','knowledge','capability','social','progress')
    for name in names:
        v=state.get(name,0.)
        if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('finite state feature required')
        x.append(max(-1.,min(1.,float(v))))
    return x

class OutcomeLearner:
    def __init__(self,capacity=192,seed=73):
        if type(capacity) is not int or not 8<=capacity<=512:raise ValueError('capacity 8..512')
        self.capacity=capacity;self.seed=seed;self.net=TinyNet(seed=seed)
        self.samples=[];self.ids=[];self.retracted=[];self.seen=0;self.enabled=True
        self.replay_updates=0;self.generation=0
        self.errors={k:{'sum':[0.]*OUTPUTS,'n':[0]*OUTPUTS} for k in ('neural','similarity')}

    @property
    def active_samples(self):return len(self.samples)

    def _nearest(self,x):
        out=[.5]*3+[0.]*24
        ranked=sorted(self.samples,key=lambda s:sum((a-b)**2 for a,b in zip(x,s['x'])))[:12]
        confidence=[]
        for j in range(OUTPUTS):
            usable=[s for s in ranked if s['mask'][j]>0][:3]
            if usable:
                weights=[1./(.015+sum((a-b)**2 for a,b in zip(x,s['x']))) for s in usable]
                out[j]=sum(w*s['y'][j] for w,s in zip(weights,usable))/sum(weights)
                confidence.append(max(weights)/(1/.015))
            else:confidence.append(0.)
        return out,confidence

    def predict(self,x,mode='adaptive'):
        x=vector(x,INPUTS,'features')
        if mode not in ('adaptive','neural','similarity'):raise ValueError('predictor mode')
        neural=self.net.predict(x);nearest,conf=self._nearest(x)
        pred=[];winners=[]
        for j in range(OUTPUTS):
            labelled=sum(s['mask'][j]>0 for s in self.samples)
            if not labelled:pred.append(.5 if j<3 else 0.);winners.append('unknown');continue
            chosen=mode
            if mode=='adaptive':
                # Similarity wins ties; before enough chronological evaluations use the simpler learner.
                n=self.errors['neural']['n'][j]
                chosen=('neural' if n>=8 and self.errors['neural']['sum'][j]<self.errors['similarity']['sum'][j] else 'similarity')
            pred.append((neural if chosen=='neural' else nearest)[j]);winners.append(chosen)
        labels=sum(any(s['mask'][:3]) for s in self.samples)
        reliability=min(1.,labels/8.)*min(1.,max(conf[:3])*2.)
        return {'outcomes':pred[:3], 'next_observation':pred[3:],
                'utility':sum(w*p for w,p in zip(WEIGHTS,pred[:3])),
                'utility_labels':labels,'confidence':reliability,'heads':winners,
                'mode':mode,'neural_outcomes':neural[:3],'similarity_outcomes':nearest[:3]}

    def learn(self,sample_id,x,y,mask):
        if not isinstance(sample_id,str) or not sample_id or len(sample_id)>120:raise ValueError('sample ID')
        if sample_id in self.ids:raise ValueError('duplicate external sample')
        if len(self.ids)>=12000:raise ValueError('external sample budget reached')
        x,y,mask=self.net._validate(x,y,mask)
        p=self.predict(x);neural=self.net.predict(x);near,_=self._nearest(x)
        # Evaluation happens BEFORE adding or training on the target.
        if self.enabled:
            for k,preds in (('neural',neural),('similarity',near)):
                for i,(a,b,m) in enumerate(zip(preds,y,mask)):
                    if m:
                        self.errors[k]['sum'][i]+=m*(a-b)**2;self.errors[k]['n'][i]+=1
        self.ids.append(sample_id);self.seen+=1
        if self.enabled:
            sample={'id':sample_id,'order':self.seen,'x':x,'y':y,'mask':mask,
                    'priority':hashlib.sha256(f'{self.seed}:{sample_id}'.encode()).hexdigest()}
            self.samples.append(sample)
            if len(self.samples)>self.capacity:
                self.samples.remove(max(self.samples,key=lambda s:s['priority']))
        before=self.net.weight_digest()
        update=self.net.train(x,y,mask) if self.enabled else {'updated':False}
        return {'sample_id':sample_id,'prequential_prediction':p,
                'prequential_mse':sum(m*(a-b)**2 for a,b,m in zip(p['outcomes']+p['next_observation'],y,mask))/max(1.,sum(mask)),
                'weights_before':before,'weights_after':self.net.weight_digest(),
                'actual_gradient_update':update['updated'],'external_samples':self.seen,
                'labels_are_user_reports':bool(any(mask[:3]))}

    def replay(self,steps=8):
        if type(steps) is not int or not 0<=steps<=64:raise ValueError('replay budget 0..64')
        before=self.net.weight_digest();count=0
        if self.enabled and self.samples:
            for i in range(steps):
                s=self.samples[(self.replay_updates+i)%len(self.samples)]
                if self.net.train(s['x'],s['y'],s['mask'])['updated']:count+=1
            self.replay_updates+=count
        return {'gradient_updates':count,'external_samples':self.seen,'new_external_evidence':False,
                'weights_before':before,'weights_after':self.net.weight_digest()}

    def retract(self,sample_id):
        if sample_id not in self.ids or sample_id in self.retracted:raise ValueError('unknown or already withdrawn sample')
        self.retracted.append(sample_id)
        self.samples=[s for s in self.samples if s['id']!=sample_id]
        self.net=TinyNet(seed=self.seed);self.errors={k:{'sum':[0.]*OUTPUTS,'n':[0]*OUTPUTS} for k in ('neural','similarity')}
        self.replay_updates=0;self.generation+=1
        # Reset from retained raw samples: also discards influence of evicted samples.
        for s in sorted(self.samples,key=lambda s:s['order']):
            self.net.train(s['x'],s['y'],s['mask'])
        return {'retracted':sample_id,'rebuilt_from_retained':len(self.samples),
                'evicted_influence_also_removed':True,'generation':self.generation}

    def summary(self):
        def mse(k,indices):
            n=sum(self.errors[k]['n'][j] for j in indices)
            return sum(self.errors[k]['sum'][j] for j in indices)/n if n else None
        return {'enabled':self.enabled,'parameters':self.net.parameter_count,'updates':self.net.updates,
                'replay_updates':self.replay_updates,'external_samples':self.seen,
                'retained_samples':len(self.samples),'capacity':self.capacity,'weight_sha256':self.net.weight_digest(),
                'generation':self.generation,'withdrawn':len(self.retracted),
                'prequential_utility_mse':{k:mse(k,range(3)) for k in self.errors},
                'prequential_transition_mse':{k:mse(k,range(3,27)) for k in self.errors},
                'objective_weights':list(WEIGHTS),'objective_source':'engineered, not learned terminal values'}

    def snapshot(self):
        return {k:deepcopy(getattr(self,k)) for k in ('capacity','seed','samples','ids','retracted','seen','enabled','replay_updates','generation','errors')}|{'net':self.net.snapshot()}

    @classmethod
    def restore(cls,data):
        if not isinstance(data,dict):raise ValueError('learner snapshot')
        l=cls(data['capacity'],data['seed']);l.net=TinyNet.restore(data['net'])
        if (l.net.inputs,l.net.outputs)!=(INPUTS,OUTPUTS):raise ValueError('learner shape mismatch')
        if type(data['enabled']) is not bool:raise ValueError('learning flag')
        for k in ('seen','replay_updates','generation'):
            if type(data[k]) is not int or data[k]<0:raise ValueError('invalid count')
        if len(data['samples'])>l.capacity or len(data['ids'])>12000:raise ValueError('sample storage bound')
        if len(set(data['ids']))!=len(data['ids']):raise ValueError('duplicate sample IDs')
        for s in data['samples']:l.net._validate(s['x'],s['y'],s['mask'])
        for k in ('samples','ids','retracted','seen','enabled','replay_updates','generation','errors'):setattr(l,k,deepcopy(data[k]))
        return l
