"""Optional one-step CUDA graph; static storage, eager-equivalent arithmetic."""
import torch

class GraphStepper:
    @torch.inference_mode()
    def __init__(self,world,brain,genomes,state,brain_state,uniform,noise):
        self.world,self.brain=world,brain
        self.genomes=genomes.clone(); self.params=brain.unpack(self.genomes)
        self.state=type(state)(*(x.clone() for x in state));self.bs=tuple(x.clone() for x in brain_state)
        self.uniform=uniform.clone();self.noise=noise.clone()
        self.index=torch.zeros(1,dtype=torch.long,device='cuda')
        stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream):
            for _ in range(3):self.step()
        torch.cuda.current_stream().wait_stream(stream)
        self.reset(genomes,state,brain_state,uniform,noise)
        torch.cuda.synchronize()
        self.graph=torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):self.step()
        self.reset(genomes,state,brain_state,uniform,noise)

    def step(self):
        p=self.genomes.shape[0]
        action,bs,_=self.brain.forward(self.params,self.world.observe(self.state),self.bs,
                                     self.uniform.index_select(0,self.index).squeeze(0).repeat(p),self.state.alive)
        ns=self.world.step(self.state,action,self.noise.index_select(0,self.index).squeeze(0).repeat(p,1))
        for a,b in zip(self.state,ns):a.copy_(b)
        for a,b in zip(self.bs,bs):a.copy_(b)
        self.index.add_(1)

    def reset(self,genomes,state,bs,uniform,noise):
        self.genomes.copy_(genomes)
        for a,b in zip(self.state,state):a.copy_(b)
        for a,b in zip(self.bs,bs):a.copy_(b)
        self.uniform.copy_(uniform);self.noise.copy_(noise);self.index.zero_()

    def run(self):
        for t in range(self.world.c.horizon):
            self.graph.replay()
            # Dead state is absorbing; a synchronized all-dead check changes no outcome.
            if (t+1)%32==0 and not bool(self.state.alive.any()):break
        return self.state,self.bs
