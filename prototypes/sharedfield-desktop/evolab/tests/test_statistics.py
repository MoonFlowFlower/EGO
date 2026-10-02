import torch
from evolab.statistics import paired_difference,decide

def test_bootstrap_constant_effect():
    x=torch.ones(5,2,8);y=torch.zeros_like(x)
    r=paired_difference(x,y,1000)
    assert r['difference']==1 and r['ci95']==[1.,1.] and r['seed_pairs_positive']==5

def test_preregistered_decision_branches():
    a=torch.full((5,2,8),.4);b=torch.full_like(a,.5);b0=a
    sa=torch.full((5,1,8),.4)
    assert decide(a,b,b0,sa,sa)['outcome']=='positive'
    assert decide(a,b,b0,sa,sa+.1)['outcome']=='partial_static'
    assert decide(a,b,b,sa,sa)['outcome']=='partial_ablation'
    assert decide(a,a,b0,sa,sa)['outcome']=='negative'
