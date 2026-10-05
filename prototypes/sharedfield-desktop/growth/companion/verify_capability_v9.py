"""Diagnostic feedback and bounded repair, separate frozen claim."""
from . import verify_capability as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_capability_v9'
if __name__=='__main__':raise SystemExit(acceptance.main())
