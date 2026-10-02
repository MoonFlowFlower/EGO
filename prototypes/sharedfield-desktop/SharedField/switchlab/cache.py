"""Recency-weighted action/outcome graph-cache baseline; no explicit self factors."""
from __future__ import annotations
from copy import deepcopy
import math
from .model import OUTCOMES

class CacheModel:
    def __init__(self, counts=None):
        self.counts={a:dict(row) for a,row in counts.items()} if counts is not None else {
            a:{o:1. for o in outcomes} for a,outcomes in OUTCOMES.items()}

    def predict(self,a):
        row=self.counts[a];total=sum(row.values())
        return [(o,v/total) for o,v in row.items()]

    def condition(self,a,o,advance=True):
        m=CacheModel(self.counts)
        if advance:
            for row in m.counts.values():
                for key in row: row[key]=1.+.94*(row[key]-1.)
        if o in m.counts[a]:m.counts[a][o]+=1.
        return m

    def update(self,a,o):self.counts=self.condition(a,o).counts
    def copy(self):return CacheModel(self.counts)
    def entropy(self):
        return sum(-p*math.log2(p) for a in self.counts for _,p in self.predict(a))/len(self.counts)
    def marginals(self):return {'energy_mode_1':None,'coolant_mode_1':None,'tool_healthy':None}
    def snapshot(self):return {'kind':'cache','counts':deepcopy(self.counts)}
    @classmethod
    def from_snapshot(cls,d):return cls(d['counts'])
