# ADDENDUM 002 — pre-run pins for P0 and P2 comparison windows

Status: PRE-RUN PINS / NO CODE / NO SCORED RUN.

This addendum is committed before implementation and before any scored PET run.
Every scored run for `egodesktop-pet-world-integration-001a` must be a
descendant of this commit. No constants may move after a scored run.

## NB-3 — P2 live-ablation comparison windows

Derived from the frozen `P2_SESSION_SCRIPT.md` toggle ticks:

- PRIMARY OFF-A window: ticks `[235, 284]`.
- PRIMARY ON-A window: ticks `[300, 349]`.
- Both primary windows are 50 ticks and both are inside `R1_shift_a`; the
  primary comparison carries the future P2 gate.
- SECONDARY OFF-B window: ticks `[435, 484]`.
- SECONDARY ON-B window: ticks `[485, 519]`.
- The secondary ON-B window is 35 ticks and is disclosed as a short
  demonstrative window; it is not the primary P2 gate carrier.

## NB-4 — P0 scored-episode user input rule

P0 scored episodes contain ZERO user-input events. P0 is autonomous-loop only.
User-path events appear only in:

- G-PET-MEM-PATH probe fixtures; and
- P2 scripted live-session evidence.

## NB-5 — learner exploration budget

The learner exploration mechanism is epsilon-greedy over the current
expected-utility action scores.

- `epsilon = 0.05`.
- Random choices must be drawn only from the R0 in-state seed registry or a
  deterministic RNG derived from it.
- No exploration-constant motion is allowed after any scored run.

Rationale: `DERIVATION_NOTES.md` allows the frozen-updates arm to recover at
most 40% of the reachable post-shift gap without model updates. With
`epsilon = 0.05`, expected random exploratory recovery is bounded below that
limit for the configured action set, leaving the `f_abl = 0.5` collapse
reachable if the learned model is actually load-bearing.

## Constants

No other constants are changed by this addendum.

Claim ceiling: pre-run pins only; no implementation, no run, no evidence pass,
no learned-component claim, and no product or mechanism claim.
