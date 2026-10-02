"""Paired hierarchical bootstrap: sample seeds, then episodes within each condition."""
import torch
from .config import generator

def paired_difference(x,y,replicates=10000,label='difference'):
    # [5 seeds, K conditions, 1024 episodes]; K=2 drift, K=1 static.
    # Resample matched seed/episode pairs to respect shared environmental draws.
    x,y=x.cpu().double(),y.cpu().double()
    assert x.shape==y.shape and x.ndim==3 and x.shape[0]==5
    g=generator('hierarchical-bootstrap',label,device='cpu'); n,k,e=x.shape
    diff=x-y; draws=[]
    for start in range(0,replicates,100):
        count=min(100,replicates-start)
        seeds=torch.randint(n,(count,n),generator=g)
        episodes=torch.randint(e,(count,n,k,e),generator=g)
        data=diff[seeds].gather(-1,episodes)
        draws.append(data.mean(dim=(1,2,3)))
    boot=torch.cat(draws)
    return {'difference':diff.mean().item(), 'ci95':torch.quantile(boot,torch.tensor([.025,.975],dtype=torch.double)).tolist(),
            'bootstrap_replicates':replicates,'seed_pairs_positive':int((diff.mean(dim=(1,2))>0).sum())}

def decide(a_drift,b_drift,b0_drift,a_static,b_static):
    main=paired_difference(b_drift,a_drift,label='B-A drift')
    ablation=paired_difference(b_drift,b0_drift,label='B-B0 drift')
    static=paired_difference(b_static,a_static,label='B-A static')
    delta=.1*a_drift.double().mean().item();delta_static=.1*a_static.double().mean().item()
    h1=main['difference']>=delta and main['ci95'][0]>0 and main['seed_pairs_positive']>=4
    h2=ablation['difference']>=.5*main['difference'] if h1 else None
    h3=static['difference']<delta_static
    outcome='negative' if not h1 else ('partial_ablation' if not h2 else ('positive' if h3 else 'partial_static'))
    return {'H1':h1,'H2':h2,'H3':h3,'outcome':outcome,'delta':delta,'delta_static':delta_static,
            'drift_B_minus_A':main,'drift_B_minus_B0':ablation,'static_B_minus_A':static}
