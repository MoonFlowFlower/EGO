"""Non-executing input has no task category prerequisite, separate frozen claim."""
from . import verify_interaction_v11 as acceptance
acceptance.EVIDENCE=acceptance.ROOT/'evidence/kernel_interaction_v13'
if __name__=='__main__':raise SystemExit(acceptance.main())
