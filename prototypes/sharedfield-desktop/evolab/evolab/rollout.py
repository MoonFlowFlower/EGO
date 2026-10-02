"""Rollout entrypoint: complete fixed-horizon batches, with common random numbers."""
import torch
from .config import generator, SEED_DOMAINS
from .world import World
from .brains import Brain
from .baselines import HandState
from .graph import GraphStepper
_GRAPH_CACHE = {}

@torch.inference_mode()
def rollout(c,regime,arm,episodes,run_seed,domain='e1',generation=0,genomes=None,trace=False,use_graph=False,final_evaluation=False):
    if domain=='holdout' and not final_evaluation:
        raise RuntimeError('Holdout requires explicit final-evaluation entrypoint; development is sealed')
    p=1 if genomes is None else genomes.shape[0]
    world=World(c,regime)
    tokens=(c.master_seed,SEED_DOMAINS[domain],run_seed,generation)
    s=world.reset(episodes,p,generator(*tokens,'layout'))
    # Independent generators by purpose; base episode streams repeated identically for each candidate.
    u=torch.rand((c.horizon,episodes),generator=generator(*tokens,'policy'),device='cuda')
    noise=torch.rand((c.horizon,episodes,4),generator=generator(*tokens,'environment'),device='cuda')
    brain=Brain(arm,c) if genomes is not None else None
    params=brain.unpack(genomes) if brain else None
    bs=brain.reset(p,episodes) if brain else None
    hand=HandState(episodes,'cuda') if arm=='H' else None
    frames=[]
    modulation=None
    if use_graph and brain and not trace:
        key=(c,regime,arm,episodes,p)
        if key not in _GRAPH_CACHE:
            _GRAPH_CACHE[key]=GraphStepper(world,brain,genomes,s,bs,u,noise)
        else:
            _GRAPH_CACHE[key].reset(genomes,s,bs,u,noise)
        s,bs=_GRAPH_CACHE[key].run()
    for t in range(0 if use_graph and brain and not trace else c.horizon):
        if brain:
            action,bs,modulation=brain.forward(params,world.observe(s),bs,u[t].repeat(p),s.alive)
        elif hand:
            action=hand.act(s)
        else:
            action=(u[t]*6).long().clamp_max(5)
        if trace and (t%5==0):
            frames.append({name:val[0].detach().cpu().tolist() for name,val in zip(s._fields,s)})
            if modulation is not None:frames[-1]['modulation']=float(modulation.flatten()[0])
        s=world.step(s,action,noise[t].repeat(p,1))
    if brain and not all(bool(torch.isfinite(x).all()) for x in bs):
        raise FloatingPointError('nonfinite brain state')
    return s.age.float().reshape(p,episodes)/c.horizon,frames
