"""Fixed model reasoning candidate, separate claim and unchanged task criteria."""
from . import verify_capability as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_capability_v5'
if __name__=='__main__':raise SystemExit(acceptance.main())
