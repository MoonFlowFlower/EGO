import math
import torch
from evolab.config import Config,generator
from evolab.brains import Brain

def test_param_budget_matched():
    a=Brain('gru_fixed',Config());b=Brain('gru_mb_plastic',Config())
    assert abs(a.nparams-b.nparams)/a.nparams<=.1
    assert b.nparams-a.nparams==8

def test_plasticity_rule_two_steps():
    b=Brain('gru_mb_plastic',Config())
    genome=torch.zeros((1,b.nparams),device='cuda'); params=b.unpack(genome)
    params[-1][:]=torch.tensor([math.log(.2),0.,0.,0.,0.,0.,0.,math.atanh(.5)],device='cuda')
    state=b.reset(1,1); obs=torch.zeros((1,134),device='cuda');obs[:,125]=.6
    _,first,_=b.forward(params,obs,state,torch.tensor([.2],device='cuda'),torch.tensor([True],device='cuda'))
    assert first[1].count_nonzero()==0
    _,second,_=b.forward(params,obs,first,torch.tensor([.2],device='cuda'),torch.tensor([True],device='cuda'))
    expected=first[3][:,:,:,None]*first[4][:,:,None,:]
    assert torch.allclose(second[2],expected)
    assert torch.allclose(second[1],.1*expected)
    _,third,_=b.forward(params,obs,second,torch.tensor([.2],device='cuda'),torch.tensor([True],device='cuda'))
    expected_e=.5*expected+second[3][:,:,:,None]*second[4][:,:,None,:]
    assert torch.allclose(third[1],.5*second[1]+.1*expected_e)

def test_eta_zero_and_modulation_zero():
    for arm in ('gru_mb_frozen','gru_mb_plastic'):
        b=Brain(arm,Config());genome=b.initial_mean(generator(1))[None];params=b.unpack(genome)
        params[-1][:,3:]=0
        state=b.reset(1,2);obs=torch.zeros((2,134),device='cuda');obs[:,125]=.6
        if arm=='gru_mb_plastic':state=(state[0],torch.ones_like(state[1]),*state[2:])
        for _ in range(3):
            previous=state[1];_,state,m=b.forward(params,obs,state,torch.full((2,),.3,device='cuda'),torch.ones(2,device='cuda',dtype=torch.bool))
            if arm=='gru_mb_frozen':assert state[1].count_nonzero()==0
            else:assert torch.allclose(state[1],previous*(1-params[-1][:,1].sigmoid())[:,None,None,None])

def test_frozen_ablation_nonzero_modulation():
    b=Brain('gru_mb_frozen',Config());params=b.unpack(b.initial_mean(generator(2))[None]);params[-1][:,-1]=1
    s=b.reset(1,2);obs=torch.zeros((2,134),device='cuda')
    for _ in range(3):
        _,s,m=b.forward(params,obs,s,torch.full((2,),.3,device='cuda'),torch.ones(2,device='cuda',dtype=torch.bool))
        assert s[1].count_nonzero()==0 and (m>0).all()
