"""Pure batched world transitions. RNG draws supplied explicitly by rollout."""
from typing import NamedTuple
import torch
from .config import Config, REGIMES

class State(NamedTuple):
    pos: torch.Tensor
    objects: torch.Tensor  # [batch,4,2]: foods 0..2, bed
    energy: torch.Tensor
    fatigue: torch.Tensor
    cooldown: torch.Tensor
    good: torch.Tensor
    next_switch: torch.Tensor
    age: torch.Tensor
    taste: torch.Tensor
    previous_action: torch.Tensor
    alive: torch.Tensor

class World:
    def __init__(self, config=Config(), regime='static', device='cuda'):
        self.c, self.regime, self.device = config, regime, device
        self.low, self.high = REGIMES[regime]
        self.moves = torch.tensor([[0,-1],[0,1],[-1,0],[1,0],[0,0],[0,0]], device=device)
        y,x = torch.meshgrid(torch.arange(-2,3,device=device), torch.arange(-2,3,device=device), indexing='ij')
        self.offsets = torch.stack([x.flatten(),y.flatten()], -1)
        self.actions = torch.arange(6,device=device)

    def reset(self, episodes, population, g):
        d=self.device
        order=torch.rand((episodes,100),generator=g,device=d).argsort(dim=-1,stable=True)[:,:5]
        coords=torch.stack([order%10+1,order//10+1],-1)
        repeat=lambda x:x.repeat((population,)+(1,)*(x.ndim-1))
        n=episodes*population
        good=repeat(torch.randint(0,3,(episodes,),generator=g,device=d)) if self.low else torch.zeros(n,dtype=torch.long,device=d)
        switch=repeat(torch.randint(self.low,self.high+1,(episodes,),generator=g,device=d)) if self.low else torch.full((n,),2**30,device=d,dtype=torch.long)
        return State(repeat(coords[:,4]), repeat(coords[:,:4]), torch.full((n,),.6,device=d),
                     torch.full((n,),.2,device=d),torch.zeros((n,3),device=d,dtype=torch.long),
                     good,switch,torch.zeros(n,device=d,dtype=torch.long),torch.zeros(n,device=d),
                     torch.zeros((n,6),device=d),torch.ones(n,device=d,dtype=torch.bool))

    def observe(self,s):
        cells=s.pos[:,None,:]+self.offsets[None,:,:]
        wall=((cells<1)|(cells>10)).any(-1)
        matches=(cells[:,:,None,:]==s.objects[:,None,:,:]).all(-1)
        food=matches[:,:,:3] & (s.cooldown[:,None,:]==0)
        channels=torch.cat([wall[:,:,None],matches[:,:,3:4],food],-1).float().flatten(1)
        return torch.cat([channels,s.energy[:,None],s.fatigue[:,None],s.taste[:,None],s.previous_action],-1)

    def step(self,s,action,noise):
        # noise [batch,4]: action corruption, replacement action, new colour, new period
        c=self.c
        corrupt=noise[:,0] < (s.fatigue-.5).clamp_min(0)
        executed=torch.where(corrupt,(noise[:,1]*6).long().clamp_max(5),action)
        pos=(s.pos+self.moves[executed]).clamp(1,10)
        moving=(executed<4)  # wall attempts cost energy as motor commands
        interact=executed==5
        switch=(s.age>=s.next_switch) if self.low else torch.zeros_like(s.alive)
        good=torch.where(switch,(s.good+1+(noise[:,2]*2).long().clamp_max(1))%3,s.good)
        next_switch=torch.where(switch,s.age+self.low+(noise[:,3]*(self.high-self.low+1)).long().clamp_max(self.high-self.low),s.next_switch)
        at=(pos[:,None,:]==s.objects).all(-1)
        eaten=at[:,:3] & (s.cooldown==0) & interact[:,None]
        good_hit=(eaten & (torch.arange(3,device=self.device)[None,:]==good[:,None])).any(-1)
        taste=torch.where(good_hit,c.food_gain,torch.where(eaten.any(-1),-c.poison_cost,0.))
        energy=(s.energy-c.energy_cost-moving.float()*c.move_cost+taste).clamp(0,1)
        resting=interact & at[:,3]
        fatigue=(s.fatigue+torch.where(resting,-c.rest_rate,c.fatigue_rate)).clamp(0,1)
        cooldown=torch.where(eaten,c.regrow,(s.cooldown-1).clamp_min(0))
        candidate=State(pos,s.objects,energy,fatigue,cooldown,good,next_switch,s.age+1,taste,
                        (executed[:,None]==self.actions[None,:]).float(),energy>0)
        # All fields, including taste, action, age and clocks, freeze after death.
        result=State(*(torch.where(s.alive.reshape((-1,)+(1,)*(a.ndim-1)),b,a)
                       for a,b in zip(s,candidate)))
        return result
