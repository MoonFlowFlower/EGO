from dataclasses import replace
import torch
from evolab.world import World
from evolab.config import Config,generator,SEED_DOMAINS

def test_world_invariants_and_observation():
    w=World(); s=w.reset(64,1,generator(1)); assert w.observe(s).shape==(64,134)
    coords=s.objects
    assert ((coords>=1)&(coords<=10)).all()
    assert not ((s.pos[:,None,:]==coords).all(-1)).any()
    assert not ((coords[:,:,None,:]==coords[:,None,:,:]).all(-1) & ~torch.eye(4,device='cuda',dtype=torch.bool)[None]).any()
    actions=torch.randint(0,6,(240,64),device='cuda',generator=generator(2))
    noises=torch.rand((240,64,4),device='cuda',generator=generator(3))
    for t in range(240):
        s=w.step(s,actions[t],noises[t])
        assert ((s.energy>=0)&(s.energy<=1)&(s.fatigue>=0)&(s.fatigue<=1)).all()
        assert (s.good==0).all()
    assert not s.alive.any()
    later=w.step(s,actions[0],noises[0]); assert all(torch.equal(a,b) for a,b in zip(s,later))

def test_death_transition_and_wall_cost():
    w=World(); s=w.reset(1,1,generator(4)); s=s._replace(pos=torch.ones_like(s.pos),energy=torch.full_like(s.energy,.005))
    z=torch.ones((1,4),device='cuda')*.9
    s=w.step(s,torch.tensor([0],device='cuda'),z)
    assert not s.alive.item() and s.age.item()==1 and s.energy.item()==0
    assert s.pos.tolist()==[[1,1]]

def test_food_cooldown_and_taste():
    w=World(replace(Config(),energy_cost=0,move_cost=0,fatigue_rate=0))
    s=w.reset(1,1,generator(4)); s=s._replace(pos=s.objects[:,0])
    action=torch.tensor([5],device='cuda'); z=torch.zeros((1,4),device='cuda')+.9
    s=w.step(s,action,z); assert abs(s.taste.item()-.3)<1e-6 and s.cooldown[0,0]==20
    for _ in range(20):
        s=w.step(s,action,z); assert s.taste.item()==0
    s=w.step(s,action,z); assert abs(s.taste.item()-.3)<1e-6

def test_drift_switch_and_static():
    for regime in ('static','drift'):
        w=World(regime=regime);s=w.reset(32,1,generator(5));s=s._replace(next_switch=torch.zeros_like(s.next_switch))
        later=w.step(s,torch.full((32,),4,device='cuda'),torch.full((32,4),.9,device='cuda'))
        if regime=='drift':assert (later.good!=s.good).all()
        else:assert (later.good==0).all()

def test_seed_domains_and_holdout_seal():
    assert len(set(SEED_DOMAINS.values()))==len(SEED_DOMAINS)
    import pytest
    from evolab.rollout import rollout
    with pytest.raises(RuntimeError,match='Holdout'):
        rollout(Config(),'drift_fast','R',1,0,domain='holdout')

def test_common_world_across_candidates():
    w=World(regime='drift');s=w.reset(8,3,generator(6))
    for value in s:
        assert torch.equal(value[:8],value[8:16]) and torch.equal(value[:8],value[16:])
