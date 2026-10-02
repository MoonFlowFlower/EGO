from dataclasses import replace
import torch
from evolab.config import Config,generator
from evolab.es import OpenES,centered_rank
from evolab.rollout import rollout

def test_baseline_smoke():
    c=replace(Config(),horizon=400)
    r,_=rollout(c,'static','R',16,90); h,_=rollout(c,'static','H',16,90)
    assert h.mean()>r.mean()

def test_es_ties_antithetic_and_direction():
    c=replace(Config(),population=256)
    es=OpenES(torch.zeros(2,device='cuda'),c);pop=es.ask(generator(55))
    assert torch.equal(es.noise[:128],-es.noise[128:])
    assert torch.equal(centered_rank(torch.ones(4,device='cuda')),torch.zeros(4,device='cuda'))
    assert torch.allclose(centered_rank(torch.tensor([1.,1.,2.,3.],device='cuda')),torch.tensor([-1/3,-1/3,1/6,.5],device='cuda'))
    es.tell(pop[:,0]); assert es.mean[0]>0
