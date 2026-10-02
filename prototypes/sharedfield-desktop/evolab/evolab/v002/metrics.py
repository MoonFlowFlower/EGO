"""Observational counters: never feed back into fitness or policy inputs."""
import torch


class Collapse:
    def __init__(self):
        self.consecutive = 0
        self.collapsed_at = None

    def update(self, generation, std):
        self.consecutive = self.consecutive + 1 if std == 0 else 0
        if self.consecutive == 20 and self.collapsed_at is None:
            self.collapsed_at = generation  # detection generation, not inferred start


class Metrics:
    def __init__(self, s, horizon):
        self.good = torch.zeros_like(s.age)
        self.bad = torch.zeros_like(s.age)
        self.first_switch = s.next_switch.clone()
        self.survived_first = torch.zeros_like(s.alive)
        self.count = torch.zeros_like(s.age)
        # At most floor(T/120)+1 switches in registered conditions.
        shape = (s.age.numel(), horizon // 120 + 2)
        self.start = torch.full(shape, -1, dtype=torch.long, device=s.age.device)
        self.duration = torch.full_like(self.start, -1)
        self.observed = torch.zeros(shape, dtype=torch.bool, device=s.age.device)

    def update(self, old, new):
        eating_good = old.alive & (new.taste > 0)
        self.good.add_(eating_good.long())
        self.bad.add_((old.alive & (new.taste < 0)).long())
        switch = old.alive & (new.good != old.good)
        self.survived_first |= switch & (old.age == self.first_switch) & new.alive
        # Recovery belongs to the current colour epoch. If superseded by another
        # switch, an unfinished epoch is right-censored at that switch.
        previous = (self.count - 1).clamp_min(0)[:, None]
        starts = self.start.gather(1, previous).squeeze(1)
        pending = (self.count > 0) & ~self.observed.gather(1, previous).squeeze(1)
        old_duration = self.duration.gather(1, previous).squeeze(1)
        d = torch.where(pending & old.alive, old.age-starts, old_duration)
        self.duration.scatter_(1, previous, d[:, None])
        idx = self.count.clamp_max(self.start.shape[1]-1)[:, None]
        self.start.scatter_(1, idx, torch.where(switch, old.age, self.start.gather(1, idx).squeeze(1))[:, None])
        self.count.add_(switch.long())
        current = (self.count - 1).clamp_min(0)[:, None]
        starts = self.start.gather(1, current).squeeze(1)
        observed = self.observed.gather(1, current).squeeze(1)
        active = (self.count > 0) & old.alive & ~observed
        # Switch and good interaction in the same transition => recovery delay 0.
        delay = torch.where(eating_good, old.age-starts, new.age-starts)
        self.duration.scatter_(1, current, torch.where(active, delay, self.duration.gather(1, current).squeeze(1))[:, None])
        self.observed.scatter_(1, current, (observed | (active & eating_good))[:, None])

    def summary(self, s, horizon):
        valid = self.start >= 0
        recovered = self.duration[valid & self.observed].float()
        return dict(survival=s.age.float().mean().item()/horizon,
                    good_food_mean=self.good.float().mean().item(),
                    bad_food_mean=self.bad.float().mean().item(),
                    ate_good_fraction=(self.good > 0).float().mean().item(),
                    survived_first_fraction=self.survived_first.float().mean().item(),
                    switches=int(valid.sum()), censored=int((valid & ~self.observed).sum()),
                    recovered_only_median=float(recovered.median()) if recovered.numel() else None)
