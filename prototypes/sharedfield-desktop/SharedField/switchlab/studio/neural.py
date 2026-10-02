"""Small trainable neural predictor, using only Python's standard library.

All hidden and output weights are trained by backpropagation. No LLM weights are
updated. A masked loss never creates labels for unobserved outcomes. This is a
bounded online-learning implementation, not an implementation of lifelong AGI.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import math
import random


def vector(values, length, name, bound=100.):
    if not isinstance(values, (list, tuple)) or len(values) != length:
        raise ValueError(f'{name}: expected {length} numbers')
    if any(type(v) not in (float, int) or not math.isfinite(v) or abs(v)>bound for v in values):
        raise ValueError(f'{name}: finite bounded numbers required')
    return [float(v) for v in values]


class TinyNet:
    """tanh hidden layer, sigmoid utility heads and tanh transition heads."""
    def __init__(self, inputs=80, hidden=24, outputs=27, utility_heads=3, seed=73):
        for n in (inputs, hidden, outputs):
            if type(n) is not int or not 1<=n<=256:raise ValueError('network size out of bounds')
        if type(utility_heads) is not int or not 0<=utility_heads<=outputs:raise ValueError('utility heads')
        self.inputs,self.hidden,self.outputs,self.utility_heads=inputs,hidden,outputs,utility_heads
        self.seed=seed;self.updates=0
        rng=random.Random(seed);scale=math.sqrt(3./inputs)
        self.w1=[[rng.uniform(-scale,scale) for _ in range(inputs)] for _ in range(hidden)]
        self.b1=[0.]*hidden
        # Neutral unknown outcomes at cold start; no synthetic personal preferences.
        self.w2=[[0.]*hidden for _ in range(outputs)];self.b2=[0.]*outputs

    def _forward(self,x):
        h=[math.tanh(b+sum(w*v for w,v in zip(row,x))) for row,b in zip(self.w1,self.b1)]
        logits=[b+sum(w*v for w,v in zip(row,h)) for row,b in zip(self.w2,self.b2)]
        y=[(1./(1.+math.exp(-max(-40.,min(40.,z)))) if i<self.utility_heads else math.tanh(z))
           for i,z in enumerate(logits)]
        return h,y

    def predict(self,x):return self._forward(vector(x,self.inputs,'input'))[1]

    def _validate(self,x,y,mask):
        x=vector(x,self.inputs,'input');y=vector(y,self.outputs,'target');mask=vector(mask,self.outputs,'mask')
        if any(v<0 or v>1 for v in mask):raise ValueError('mask weights must be in [0,1]')
        if any(not (0<=v<=1 if i<self.utility_heads else -1<=v<=1) for i,v in enumerate(y)):
            raise ValueError('target out of range')
        return x,y,mask

    def loss(self,x,y,mask):
        x,y,mask=self._validate(x,y,mask);pred=self._forward(x)[1]
        return sum(m*(p-t)**2 for p,t,m in zip(pred,y,mask))/max(1.,sum(mask))

    def gradients(self,x,y,mask):
        x,y,mask=self._validate(x,y,mask);h,pred=self._forward(x);den=max(1.,sum(mask))
        d=[2.*m*(p-t)*(p*(1.-p) if i<self.utility_heads else 1.-p*p)/den
           for i,(p,t,m) in enumerate(zip(pred,y,mask))]
        dh=[(1.-v*v)*sum(self.w2[i][j]*d[i] for i in range(self.outputs)) for j,v in enumerate(h)]
        return {'w1':[[g*v for v in x] for g in dh], 'b1':dh,
                'w2':[[g*v for v in h] for g in d], 'b2':d}

    def train(self,x,y,mask,lr=.18):
        x,y,mask=self._validate(x,y,mask)
        if type(lr) not in (float,int) or not math.isfinite(lr) or not 0<lr<=1:raise ValueError('learning rate')
        before=self.loss(x,y,mask)
        if not any(mask):return {'loss_before':before,'loss_after':before,'updated':False}
        g=self.gradients(x,y,mask)
        norm=math.sqrt(sum(v*v for k in ('w1','w2') for row in g[k] for v in row)
                       +sum(v*v for k in ('b1','b2') for v in g[k]))
        step=lr*min(1.,5./max(norm,1e-12))
        for k in ('w1','w2'):
            w=getattr(self,k)
            for i,row in enumerate(w):
                for j in range(len(row)):row[j]-=step*g[k][i][j]
        for k in ('b1','b2'):
            w=getattr(self,k)
            for i in range(len(w)):w[i]-=step*g[k][i]
        self.updates+=1
        return {'loss_before':before,'loss_after':self.loss(x,y,mask),'gradient_norm':norm,'updated':True}

    def snapshot(self):
        return {'inputs':self.inputs,'hidden':self.hidden,'outputs':self.outputs,'utility_heads':self.utility_heads,
                'seed':self.seed,'updates':self.updates,'w1':deepcopy(self.w1),'w2':deepcopy(self.w2),
                'b1':list(self.b1),'b2':list(self.b2)}

    @classmethod
    def restore(cls,data):
        if not isinstance(data,dict):raise ValueError('network snapshot')
        m=cls(**{k:data[k] for k in ('inputs','hidden','outputs','utility_heads','seed')})
        for k,n,width in [('w1',m.hidden,m.inputs),('w2',m.outputs,m.hidden)]:
            if not isinstance(data[k],list) or len(data[k])!=n:raise ValueError('matrix shape')
            setattr(m,k,[vector(row,width,k,10000.) for row in data[k]])
        m.b1=vector(data['b1'],m.hidden,'b1',10000.);m.b2=vector(data['b2'],m.outputs,'b2',10000.)
        if type(data['updates']) is not int or data['updates']<0:raise ValueError('updates')
        m.updates=data['updates'];return m

    def weight_digest(self):
        weights={k:getattr(self,k) for k in ('w1','w2','b1','b2')}
        return hashlib.sha256(json.dumps(weights,separators=(',',':'),sort_keys=True,allow_nan=False).encode()).hexdigest()

    @property
    def parameter_count(self):return self.inputs*self.hidden+self.hidden+self.hidden*self.outputs+self.outputs
