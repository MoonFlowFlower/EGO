"""Statistics use an explicit CPU torch.Generator; no global RNG."""
import torch
from .config import generator

def mean_ci(values,replicates=10000):
    x=values.detach().cpu().double().flatten()
    g=generator('e1_bootstrap',device='cpu')
    idx=torch.randint(x.numel(),(replicates,x.numel()),generator=g)
    boot=x[idx].mean(-1)
    return {'mean':x.mean().item(),'ci95':torch.quantile(boot,torch.tensor([.025,.975],dtype=torch.double)).tolist(),'episodes':x.numel()}
