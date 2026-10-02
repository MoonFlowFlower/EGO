"""002A dimensional extension of repository-owned 001A brain; same arithmetic."""
"""Independent per-candidate dense/GRU genomes and lifetime-only plastic state."""
import math
import torch
from ..config import generator

class Brain:
    def __init__(self,arm,c,device='cuda'):
        self.arm,self.c,self.device=arm,c,device
        self.plastic=arm!='gru_fixed'
        h=c.hidden
        self.shapes=[(c.input_size,64),(64,),(64,3*h),(h,3*h),(3*h,),(3*h,),(h,6),(6,)]
        if self.plastic:self.shapes += [(8,)]
        self.sizes=[math.prod(s) for s in self.shapes]
        self.nparams=sum(self.sizes)
        # Six distinct incoming coordinates per KC, all weights exactly one.
        self.projection=torch.rand((256,c.input_size),device=device,generator=generator(c.projection_seed,'projection',device=device)).argsort(dim=-1,stable=True)[:,:6]
        self.action_ids=torch.arange(6,device=device)

    def initial_mean(self,g):
        blocks=[]
        for shape in self.shapes:
            if len(shape)==2:
                blocks.append(torch.randn(shape,device=self.device,generator=g)/math.sqrt(shape[0]))
            else:blocks.append(torch.zeros(shape,device=self.device))
        if self.plastic:
            blocks[-1][:3]=torch.tensor([math.log(.01),math.log(.01/.99),math.log(.9/.1)],device=self.device)
        return torch.cat([x.flatten() for x in blocks])

    def unpack(self,genomes):
        return [part.reshape((genomes.shape[0],)+shape) for part,shape in zip(genomes.split(self.sizes,-1),self.shapes)]

    def reset(self,pop,episodes):
        shape=(pop,episodes)
        return (torch.zeros((*shape,self.c.hidden),device=self.device),
                torch.zeros((*shape,256,6),device=self.device),
                torch.zeros((*shape,256,6),device=self.device),
                torch.zeros((*shape,256),device=self.device),
                torch.zeros((*shape,6),device=self.device),
                torch.full(shape,self.c.initial_energy,device=self.device))

    def forward(self,params,obs,state,uniform,alive):
        h,w,e,prev_kc,prev_action,prev_energy=state
        p,n,_=h.shape
        o=obs.reshape(p,n,self.c.input_size)
        sensory=self.c.input_size-9
        x=torch.tanh(torch.bmm(o,params[0])+params[1][:,None,:])
        xg=torch.bmm(x,params[2])+params[4][:,None,:]
        hg=torch.bmm(h,params[3])+params[5][:,None,:]
        xr,xz,xn=xg.chunk(3,-1); hr,hz,hn=hg.chunk(3,-1)
        reset=torch.sigmoid(xr+hr); update=torch.sigmoid(xz+hz)
        next_h=(1-update)*torch.tanh(xn+reset*hn)+update*h
        logits=torch.bmm(next_h,params[6])+params[7][:,None,:]
        modulation=torch.zeros((p,n),device=self.device)
        if self.plastic:
            rule=params[8]
            eta=rule[:,0].exp()[:,None,None,None]
            if self.arm=='gru_mb_frozen':eta=torch.zeros_like(eta)
            decay=rule[:,1].sigmoid()[:,None,None,None]
            gamma=rule[:,2].sigmoid()[:,None,None,None]
            inputs=torch.stack([o[:,:,sensory+2],o[:,:,sensory],o[:,:,sensory+1],o[:,:,sensory]-prev_energy],-1)
            modulation=torch.tanh((inputs*rule[:,None,3:7]).sum(-1)+rule[:,None,7])
            e=gamma*e+prev_kc[:,:,:,None]*prev_action[:,:,None,:]
            w=(1-decay)*w+eta*modulation[:,:,None,None]*e
            activation=o[:,:,self.projection].sum(-1)
            top=activation.argsort(dim=-1,descending=True,stable=True)[:,:,:26]
            kc=torch.zeros_like(activation).scatter(-1,top,1.)
            logits=logits+(kc[:,:,:,None]*w).sum(-2)
        else:kc=prev_kc
        probs=logits.softmax(-1)
        action=(uniform.reshape(p,n,1)>probs.cumsum(-1)).sum(-1).clamp_max(5)
        onehot=(action[:,:,None]==self.action_ids).float()
        proposed=(next_h,w,e,kc,onehot,o[:,:,sensory])
        alive=alive.reshape(p,n)
        next_state=tuple(torch.where(alive.reshape((p,n)+(1,)*(a.ndim-2)),b,a) for a,b in zip(state,proposed))
        return action.flatten(),next_state,modulation
