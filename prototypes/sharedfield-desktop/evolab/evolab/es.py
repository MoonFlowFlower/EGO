"""OpenES with antithetic Gaussian sampling, tie-averaged centered ranks, Adam ascent."""
import torch

def centered_rank(fitness):
    # Pairwise comparisons give exact average ranks for ties, no arbitrary tie advantage.
    lower=(fitness[:,None]>fitness[None,:]).sum(-1)
    equal=(fitness[:,None]==fitness[None,:]).sum(-1)
    return (lower+(equal-1)/2)/(fitness.numel()-1)-.5

class OpenES:
    def __init__(self,mean,c):
        self.mean=mean.clone(); self.c=c
        self.m=torch.zeros_like(mean); self.v=torch.zeros_like(mean); self.t=0
    def ask(self,g):
        half=torch.randn((self.c.population//2,self.mean.numel()),device=self.mean.device,generator=g)
        self.noise=torch.cat([half,-half],0)
        return self.mean[None,:]+self.c.sigma*self.noise
    def tell(self,fitness):
        if not bool(torch.isfinite(fitness).all()):raise FloatingPointError('nonfinite fitness')
        grad=(centered_rank(fitness)[:,None]*self.noise).mean(0)/self.c.sigma
        self.t+=1
        self.m=.9*self.m+.1*grad; self.v=.999*self.v+.001*grad.square()
        self.mean=self.mean+self.c.learning_rate*(self.m/(1-.9**self.t))/((self.v/(1-.999**self.t)).sqrt()+1e-8)
        if not bool(torch.isfinite(self.mean).all()):raise FloatingPointError('nonfinite ES genome')
