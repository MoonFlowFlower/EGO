# ADDENDUM 001 — P2 session script freeze-boundary correction

Status: PRE-RUN ADDENDUM / NO CONSTANT CHANGE.

Claude pre-check non-blocking finding NB-1, consumed by this freeze step:

> card says the P2 operator-session script is "committed at landing", but landing
> (correctly, per landing-only scope) did not include it. Fix consumed by THIS
> step: the session script lands here, still ancestor of every scored run —
> record the wording deviation in ADDENDUM_001.md; do NOT silently edit the card
> sentence.

Resolution: `P2_SESSION_SCRIPT.md` is committed in this freeze step, before any
scored run. This commit is intended to be an ancestor of every scored PET run.
The Stage Card sentence is not edited. No gate constant, drift schedule, seed
set, CPU line, claim ceiling, or mutation path is changed by this addendum.

Claim ceiling: ordering/governance note only; no implementation, no run, no
evidence pass, and no product or mechanism claim.
