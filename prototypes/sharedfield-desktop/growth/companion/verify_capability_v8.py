"""Grounded boundary explanation, separate frozen claim."""
from . import verify_capability as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_capability_v8'
if __name__=='__main__':raise SystemExit(acceptance.main())
