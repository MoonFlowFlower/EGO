import torch
from ..world import World as LegacyWorld
from .config import Config


class World(LegacyWorld):
    def __init__(self, config=Config(), regime='static', device='cuda'):
        super().__init__(config, regime, device)
        if config.view_size not in (5, 7):
            raise ValueError('002A permits only 5x5 and 7x7 views')
        radius = config.view_size // 2
        y, x = torch.meshgrid(torch.arange(-radius, radius+1, device=device),
                              torch.arange(-radius, radius+1, device=device), indexing='ij')
        self.offsets = torch.stack([x.flatten(), y.flatten()], -1)

    def reset(self, episodes, population, g):
        s = super().reset(episodes, population, g)
        return s._replace(energy=torch.full_like(s.energy, self.c.initial_energy))
