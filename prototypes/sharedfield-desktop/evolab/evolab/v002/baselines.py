import torch
from ..baselines import HandState


class ScriptState(HandState):
    """H's exact hunger/rest/path logic; only food choice differs for N/F."""
    def __init__(self, n, device, arm):
        super().__init__(n, device)
        assert arm in ('H', 'N', 'F')
        self.arm = arm

    def act(self, s):
        if self.arm == 'H':
            return super().act(s)
        self.resting = (self.resting | (s.fatigue > .7)) & (s.fatigue >= .2)
        if self.arm == 'N':
            # Manhattan distance matches the x-then-y shortest path. Stable colour tie.
            distance = (s.objects[:, :3] - s.pos[:, None, :]).abs().sum(-1)
            self.belief = distance.masked_fill(s.cooldown != 0, 1000).argmin(-1)
        else:
            self.belief = torch.zeros_like(self.belief)
        food = s.objects[:, :3].gather(1, self.belief[:, None, None].expand(-1, 1, 2)).squeeze(1)
        available = s.cooldown.gather(1, self.belief[:, None]).squeeze(1) == 0
        target = torch.where(self.resting[:, None], s.objects[:, 3], food)
        delta = target - s.pos
        action = torch.where(delta[:, 0] > 0, 3, torch.where(delta[:, 0] < 0, 2,
                 torch.where(delta[:, 1] > 0, 1, torch.where(delta[:, 1] < 0, 0, 5))))
        self.last_colour = self.belief
        return torch.where(self.resting | ((s.energy < .7) & available), action, 4)
