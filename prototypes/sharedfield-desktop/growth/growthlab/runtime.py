"""Trusted host boundary; never pass this module or an Env to a policy."""
import numpy as np
import crafter
from crafter import engine


class IsolatedView(engine.LocalView):
    def __init__(self, *args):
        super().__init__(*args)
        self.visual_random = np.random.RandomState(0)

    def _noise(self, canvas, amount, stddev):
        noise = self.visual_random.uniform(32, 127, canvas.shape[:2])[..., None]
        mask = amount * self._vignette(canvas.shape, stddev)[..., None]
        return (1 - mask) * canvas + mask * noise


class GrowthEnv(crafter.Env):
    """Separate visual RNG plus stable candidate order, pinned upstream only.

    Calls must be serialized by the host. view stays (9,9): view also controls
    simulation activation distance upstream and is NOT a cosmetic option.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._local_view = IsolatedView(
            self._world, self._textures, self._local_view._grid)

    def reset(self):
        self._local_view.visual_random.seed((int(self._seed) + self._episode) % 2**32)
        return super().reset()

    def _balance_object(self, chunk, objs, *args):
        # Upstream chunks contain sets of identity-hashed objects. Their order
        # varies across processes and changes RNG-selected despawn targets.
        ids = {id(obj) for obj in objs}
        ordered = [obj for obj in self._world._objects if id(obj) in ids]
        return super()._balance_object(chunk, ordered, *args)
