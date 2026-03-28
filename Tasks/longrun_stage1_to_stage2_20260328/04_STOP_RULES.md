# Stop Rules

Stop immediately if any of these become true:

1. A required authority source conflicts with the batch assumption and changes the current formal position.
2. A repair proposal would cross from `MVP11.5 / Stage 1` into `Stage 3+` capability work.
3. Verification for a `ready / promote` claim does not reach the required threshold.
4. The same blocker class fails to converge after 2 repair loops.
5. The current environment cannot safely continue because exec/session hygiene is degraded enough to threaten reproducibility.
6. `Stage 2` is formally promoted.
7. A blocker dossier is complete and the formal outcome is `stage1_blocker_complete_stop`.
