"""Default-off offline R2 controlled-initiative harness.

The package is intentionally isolated from EgoOperator/EgoDesktop runtime paths.
It implements only the frozen offline simulator/evidence harness defined by the
landed EGO-R2-CONTROLLED-INITIATIVE-001A card.
"""

from .constants import TASK_ID

__all__ = ["TASK_ID"]
