import torch

class HandState:
    def __init__(self,n,device):
        self.belief=torch.zeros(n,device=device,dtype=torch.long)
        self.resting=torch.zeros(n,device=device,dtype=torch.bool)
        self.last_colour=torch.zeros(n,device=device,dtype=torch.long)

    def act(self,s):
        actual_colour=(s.pos[:,None,:]==s.objects[:,:3]).all(-1).long().argmax(-1)
        self.belief=torch.where(s.taste>0,actual_colour,
                     torch.where(s.taste<0,(actual_colour+1)%3,self.belief))
        self.resting=(self.resting | (s.fatigue>.7)) & (s.fatigue>=.2)
        food=s.objects[:,:3].gather(1,self.belief[:,None,None].expand(-1,1,2)).squeeze(1)
        available=s.cooldown.gather(1,self.belief[:,None]).squeeze(1)==0
        hungry=s.energy<.7
        target=torch.where(self.resting[:,None],s.objects[:,3],food)
        delta=target-s.pos
        # Resolve x first, then y. Waiting on an exhausted food is allowed.
        action=torch.where(delta[:,0]>0,3,torch.where(delta[:,0]<0,2,
               torch.where(delta[:,1]>0,1,torch.where(delta[:,1]<0,0,5))))
        active=self.resting | (hungry & available)
        action=torch.where(active,action,4)
        self.last_colour=self.belief
        return action
