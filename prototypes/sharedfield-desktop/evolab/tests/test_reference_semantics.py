import torch
from evolab.config import Config,generator
from evolab.brains import Brain
from evolab.baselines import HandState
from evolab.world import World

def test_gru_matches_torch_reference():
    b=Brain('gru_fixed',Config()); params=b.unpack(b.initial_mean(generator(77))[None])
    obs=torch.rand((3,134),device='cuda',generator=generator(78));state=b.reset(1,3)
    state=(torch.rand((1,3,32),device='cuda',generator=generator(79)),*state[1:])
    _,out,_=b.forward(params,obs,state,torch.full((3,),.2,device='cuda'),torch.ones(3,device='cuda',dtype=torch.bool))
    # GRUCell initialization uses a local fork so the test does not affect simulation RNG.
    with torch.random.fork_rng(devices=[0]):
        cell=torch.nn.GRUCell(64,32,device='cuda')
    with torch.no_grad():
        cell.weight_ih.copy_(params[2][0].T);cell.weight_hh.copy_(params[3][0].T)
        cell.bias_ih.copy_(params[4][0]);cell.bias_hh.copy_(params[5][0])
        x=torch.tanh(obs@params[0][0]+params[1][0])
        expected=cell(x,state[0][0])
    assert torch.allclose(expected,out[0][0],rtol=1e-5,atol=1e-6)

def test_hand_uses_actual_tasted_colour_after_noise():
    w=World();s=w.reset(1,1,generator(80));h=HandState(1,'cuda')
    s=s._replace(pos=s.objects[:,2],taste=torch.tensor([.3],device='cuda'))
    h.act(s);assert h.belief.item()==2
