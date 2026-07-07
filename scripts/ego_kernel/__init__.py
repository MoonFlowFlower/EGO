"""Default-off EGO R0 kernel substrate helpers.

This package has no runtime registration and does not import EgoOperator.
"""

from scripts.ego_kernel.state import KERNEL_STATE_SCHEMA_VERSION, KernelState

__all__ = ["KERNEL_STATE_SCHEMA_VERSION", "KernelState"]
