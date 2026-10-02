from dataclasses import dataclass, asdict
import hashlib
import os
os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
import torch

@dataclass(frozen=True)
class Config:
    horizon: int = 1500
    energy_cost: float = .004
    move_cost: float = .002
    fatigue_rate: float = .002
    rest_rate: float = .03
    food_gain: float = .30
    poison_cost: float = .05
    regrow: int = 20
    hidden: int = 32
    projection_seed: int = 8101
    population: int = 256
    episodes: int = 8
    generations: int = 400
    sigma: float = .02
    learning_rate: float = .01
    validation_every: int = 20
    validation_episodes: int = 128
    master_seed: int = 20261002

# Domain separation is part of the frozen config; do not evaluate holdout in development.
SEED_DOMAINS = {'train': 100000, 'dev': 200000, 'e1': 300000, 'holdout': 900000}
REGIMES = {'static': (0, 0), 'drift': (200, 400),
           'drift_fast': (120, 180), 'drift_slow': (500, 600), 'static_holdout': (0, 0)}

def seed(*parts):
    return int.from_bytes(hashlib.sha256(repr(parts).encode()).digest()[:8], 'little') % (2**63 - 1)

def generator(*parts, device='cuda'):
    return torch.Generator(device=device).manual_seed(seed(*parts))

def setup():
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable: formal experiment cannot fall back to CPU')
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(4)

def config_dict(c):
    return {'world_and_es': asdict(c), 'seed_domains': SEED_DOMAINS, 'regimes': REGIMES,
            'arms': ['gru_fixed', 'gru_mb_plastic'], 'seeds': list(range(5)),
            'holdout_episodes': 1024, 'bootstrap_replicates': 10000,
            'final_selection': 'generation_400_mean', 'tf32': False,
            'execution': 'one-step CUDA Graph; all-dead check each 32 steps',
            'gru_convention': 'PyTorch reset-after; z retains old hidden',
            'kc_top_k': 26, 'kc_ties': 'stable descending, lower index first',
            'es_rank_ties': 'average rank', 'adam': {'beta1': .9, 'beta2': .999, 'eps': 1e-8}}
