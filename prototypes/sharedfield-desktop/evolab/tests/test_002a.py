import hashlib, json, subprocess, sys
from dataclasses import replace
from pathlib import Path
import pytest
import torch
import yaml
from evolab.config import generator, Config as OldConfig
from evolab.world import World as OldWorld
from evolab.brains import Brain as OldBrain
from evolab.rollout import rollout as old_rollout
from evolab.v002.config import Config, ladder, DOMAINS
from evolab.v002.world import World
from evolab.v002.brains import Brain
from evolab.v002.baselines import ScriptState
from evolab.v002.metrics import Metrics, Collapse
from evolab.v002.rollout import rollout

ROOT = Path(__file__).resolve().parents[1]


def test_protected_001a_bytes():
    manifest = json.loads((ROOT/'evidence/002A/legacy_manifest.json').read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    assert hashlib.sha256((ROOT/'PREREG_002A.md').read_bytes()).hexdigest() == '4d378b0c224550ee3a982f134a313edd341d40da1303e4f88a69cd102fe58a68'


@pytest.mark.parametrize('arm', ['gru_fixed', 'gru_mb_plastic'])
def test_fresh_process_5_generations(arm, tmp_path):
    results = []
    for i, impl in enumerate(['legacy', 'new', 'new']):
        out = tmp_path/f'{i}.json'
        subprocess.run([sys.executable, str(ROOT/'scripts/002a_replay.py'), impl, arm, str(out)], check=True, cwd=ROOT)
        results.append(json.loads(out.read_text()))
    assert results[0] == results[1] == results[2]


@pytest.mark.parametrize('arm', ['gru_fixed', 'gru_mb_plastic'])
def test_saved_generation400_development(arm):
    cfg = yaml.safe_load((ROOT/'configs/e2_frozen.yaml').read_bytes())['world_and_es']
    directory = ROOT/f'runs/{arm}_drift_seed0_attempt0'
    mean = torch.load(directory/'final_mean.pt', weights_only=True)['mean'].cuda()[None]
    saved = json.loads((directory/'status.json').read_text())['training_survival']
    scores, _ = rollout(Config(**cfg), 'drift', arm, 1024, 0, 'dev', 1, mean, use_graph=True)
    assert torch.equal(scores.flatten().cpu(), torch.tensor(saved))


@pytest.mark.parametrize('view', [5, 7])
def test_dimensions_budget_graph_and_instrumentation(view):
    c = Config(view_size=view, horizon=40, initial_energy=1.)
    a, b = Brain('gru_fixed', c), Brain('gru_mb_plastic', c)
    assert (b.nparams-a.nparams)/a.nparams < .1
    for brain in (a, b):
        mean = brain.initial_mean(generator(42, 'f0-init'))[None]
        plain, p = rollout(c, 'drift', brain.arm, 4, 1, genomes=mean)
        graph, g = rollout(c, 'drift', brain.arm, 4, 1, genomes=mean, use_graph=True)
        met, m = rollout(c, 'drift', brain.arm, 4, 1, genomes=mean, telemetry=True)
        assert torch.equal(plain, graph) and torch.equal(plain, met)
        for x, y, z in zip(p['state'], g['state'], m['state']):
            assert torch.equal(x, y) and torch.equal(x, z)
        for x, y in zip(p['brain_state'], g['brain_state']):
            assert torch.equal(x, y)
        assert brain.reset(1, 1)[-1].item() == 1.


def test_world_parameters_and_legacy_transitions():
    old, new = OldWorld(OldConfig(), 'drift'), World(Config(), 'drift')
    a = old.reset(12, 1, generator(89))
    b = new.reset(12, 1, generator(89))
    for t in range(410):
        assert all(torch.equal(x, y) for x, y in zip(a, b))
        assert torch.equal(old.observe(a), new.observe(b))
        action = torch.randint(0, 6, (12,), device='cuda', generator=generator(89, t))
        noise = torch.rand((12, 4), device='cuda', generator=generator(90, t))
        a, b = old.step(a, action, noise), new.step(b, action, noise)
    c = Config(move_cost=0., poison_cost=.3, initial_energy=1., view_size=7)
    w = World(c)
    s = w.reset(1, 1, generator(98))
    assert s.energy.item() == 1. and w.observe(s).shape == (1, 254)
    n = torch.ones((1, 4), device='cuda')
    moved = w.step(s, torch.tensor([0], device='cuda'), n)
    assert torch.equal(moved.energy, (s.energy-c.energy_cost).clamp(0, 1))
    s = s._replace(pos=s.objects[:, 1])
    bitten = w.step(s, torch.tensor([5], device='cuda'), n)
    assert bitten.taste.item() == pytest.approx(-.3)


def test_script_food_choices_and_shared_hysteresis():
    w = World()
    s = w.reset(1, 1, generator(92))
    s = s._replace(pos=torch.tensor([[5, 5]], device='cuda'),
        objects=torch.tensor([[[1, 5], [6, 5], [5, 7], [5, 4]]], device='cuda'),
        taste=torch.tensor([-.05], device='cuda'))
    n, f, h = [ScriptState(1, 'cuda', arm) for arm in ('N', 'F', 'H')]
    assert n.act(s).item() == 3 and n.belief.item() == 1
    assert f.act(s).item() == 2 and f.belief.item() == 0
    s = s._replace(cooldown=torch.tensor([[0, 20, 0]], device='cuda'))
    assert n.act(s).item() == 1 and n.belief.item() == 2
    s = s._replace(fatigue=torch.tensor([.8], device='cuda'))
    assert all(x.act(s).item() == 0 for x in (n, f, h))
    s = s._replace(fatigue=torch.tensor([.4], device='cuda'))
    assert all(x.act(s).item() == 0 for x in (n, f, h))


def test_recovery_counts_censor_and_dead_freeze():
    w = World(Config(), 'drift')
    s = w.reset(1, 1, generator(11))
    s = s._replace(age=torch.tensor([200], device='cuda'), next_switch=torch.tensor([200], device='cuda'), good=torch.tensor([0], device='cuda'))
    m = Metrics(s, 1500)
    n = s._replace(age=s.age+1, good=torch.tensor([1], device='cuda'), taste=torch.tensor([-.05], device='cuda'))
    m.update(s, n)
    assert m.bad.item() == 1 and m.survived_first.item()
    s, n = n, n._replace(age=n.age+1, taste=torch.tensor([.3], device='cuda'))
    m.update(s, n)
    assert m.good.item() == 1 and m.duration[0, 0].item() == 1 and m.observed[0, 0]
    s, n = n, n._replace(age=n.age+1, good=torch.tensor([2], device='cuda'), taste=torch.tensor([0.], device='cuda'))
    m.update(s, n)
    s, n = n, n._replace(age=n.age+1, alive=torch.tensor([False], device='cuda'))
    m.update(s, n)
    assert m.duration[0, 1].item() == 2 and not m.observed[0, 1]
    before = m.summary(n, 1500)
    m.update(n, n)
    assert before == m.summary(n, 1500)
    assert before['switches'] == 2 and before['censored'] == 1


def test_collapse_and_domain_guards():
    c = Collapse()
    for gen in range(1, 20):
        c.update(gen, 0.)
    assert c.collapsed_at is None
    c.update(20, .1)
    for gen in range(21, 41):
        c.update(gen, 0.)
    assert c.collapsed_at == 40
    assert len(set(DOMAINS.values())) == len(DOMAINS)
    with pytest.raises(RuntimeError):
        rollout(Config(), 'drift_fast', 'H', 1, 0)
    assert ladder(3, .15).initial_energy == 1.
    assert ladder(2, .15).population == 512
