from dataclasses import replace
import torch
import pytest
from evolab.config import Config,generator
from evolab.brains import Brain
from evolab.rollout import rollout

@pytest.mark.parametrize('arm',['gru_fixed','gru_mb_plastic'])
def test_graph_eager_equivalence_and_reset(arm):
    c=replace(Config(),horizon=240)
    b=Brain(arm,c); genomes=torch.stack([b.initial_mean(generator(99,i)) for i in range(2)])
    for gen in (0,1):
        ref,_=rollout(c,'drift',arm,8,101,generation=gen,genomes=genomes)
        graph,_=rollout(c,'drift',arm,8,101,generation=gen,genomes=genomes,use_graph=True)
        assert torch.equal(ref,graph)

@pytest.mark.parametrize('arm',['gru_fixed','gru_mb_plastic'])
def test_graph_full_state_equivalence(arm):
    from evolab.world import World
    from evolab.graph import GraphStepper
    c=replace(Config(),horizon=220,energy_cost=0,move_cost=0,poison_cost=0)
    b=Brain(arm,c);w=World(c,'drift');genomes=b.initial_mean(generator(110))[None]
    s=w.reset(4,1,generator(111));s=s._replace(next_switch=torch.full_like(s.next_switch,10))
    bs=b.reset(1,4);u=torch.rand((c.horizon,4),device='cuda',generator=generator(112))
    noise=torch.rand((c.horizon,4,4),device='cuda',generator=generator(113))
    with torch.inference_mode():
        graph=GraphStepper(w,b,genomes,s,bs,u,noise)
        params=b.unpack(genomes)
        for t in range(c.horizon):
            action,bs,_=b.forward(params,w.observe(s),bs,u[t],s.alive)
            s=w.step(s,action,noise[t])
        gs,gbs=graph.run()
        assert all(torch.equal(x,y) for x,y in zip(s,gs))
        assert all(torch.equal(x,y) for x,y in zip(bs,gbs))
