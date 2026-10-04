"""Separate single claim; v2 failure and source snapshot remain preserved."""
from . import verify_capability as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_capability_v3'
if __name__=='__main__':raise SystemExit(acceptance.main())
