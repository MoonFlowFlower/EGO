"""Separate single claim; earlier evidence is immutable."""
from . import verify_capability as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_capability_v4'
if __name__=='__main__':raise SystemExit(acceptance.main())
