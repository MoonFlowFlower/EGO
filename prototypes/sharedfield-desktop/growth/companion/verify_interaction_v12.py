"""Explicit source facts and current applicability, separate frozen claim."""
from . import verify_interaction_v11 as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_interaction_v12'
if __name__=='__main__':raise SystemExit(acceptance.main())
