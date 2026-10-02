import torch
from ..config import generator
from ..graph import GraphStepper
from .config import DOMAINS
from .world import World
from .brains import Brain
from .baselines import ScriptState
from .metrics import Metrics

_CACHE = {}


@torch.inference_mode()
def rollout(c, regime, arm, episodes, run_seed, domain='f0', generation=0,
            genomes=None, use_graph=False, telemetry=False, trace=False):
    if 'holdout' in domain or 'holdout' in regime or regime in ('drift_fast', 'drift_slow'):
        raise RuntimeError('002A holdout sealed until a verified gate V entrypoint exists')
    p = 1 if genomes is None else genomes.shape[0]
    world = World(c, regime)
    tokens = (c.master_seed, DOMAINS[domain], run_seed, generation)
    s = world.reset(episodes, p, generator(*tokens, 'layout'))
    u = torch.rand((c.horizon, episodes), generator=generator(*tokens, 'policy'), device='cuda')
    noise = torch.rand((c.horizon, episodes, 4), generator=generator(*tokens, 'environment'), device='cuda')
    brain = Brain(arm, c) if genomes is not None else None
    params = brain.unpack(genomes) if brain else None
    bs = brain.reset(p, episodes) if brain else None
    hand = ScriptState(episodes, 'cuda', arm) if arm in ('H', 'N', 'F') else None
    metrics = Metrics(s, c.horizon) if telemetry else None
    frames = []
    graph = use_graph and brain is not None and not telemetry and not trace
    if graph:
        key = (c, regime, arm, episodes, p)
        if key not in _CACHE:
            _CACHE[key] = GraphStepper(world, brain, genomes, s, bs, u, noise)
        else:
            _CACHE[key].reset(genomes, s, bs, u, noise)
        s, bs = _CACHE[key].run()
    else:
        for t in range(c.horizon):
            modulation = None
            if brain:
                action, bs, modulation = brain.forward(params, world.observe(s), bs, u[t].repeat(p), s.alive)
            elif hand:
                action = hand.act(s)
            else:
                action = (u[t]*6).long().clamp_max(5)
            if trace and t % 5 == 0:
                frames.append({name: val[0].cpu().tolist() for name, val in zip(s._fields, s)})
                if modulation is not None:
                    frames[-1]['modulation'] = float(modulation.flatten()[0])
            new = world.step(s, action, noise[t].repeat(p, 1))
            if metrics:
                metrics.update(s, new)
            s = new
    if brain and not all(bool(torch.isfinite(x).all()) for x in bs):
        raise FloatingPointError('nonfinite brain state')
    return s.age.float().reshape(p, episodes)/c.horizon, dict(
        state=s, brain_state=bs, metrics=metrics, frames=frames,
        summary=metrics.summary(s, c.horizon) if metrics else None)
