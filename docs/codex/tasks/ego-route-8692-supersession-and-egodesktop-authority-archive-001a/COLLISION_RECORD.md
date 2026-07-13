# Collision Record — EGO Route 8692 Supersession

## Real objective

Correct the current product/capability authority additively so 8692 M1-M3 and
EgoDesktop cannot be resumed as current successor work, while preserving all
historical source and evidence and binding only Card 2 banking.

## Candidate A — edit STATUS prose only (rejected)

- Evidence produced: a human-readable correction.
- Strongest cheap baseline: any stale task card, memory summary, or generated
  view can still point to M1 and win in a fresh session.
- Leakage/hard-coding risk: high; the prose becomes another manually maintained
  route list.
- Smallest falsifier: mutate a sink back to `M1 ready`; no machine gate rejects.
- Expected failure: route drift recurs because no structured enforcement exists.

## Candidate B — preserve 8692 and add a second canonical route (rejected)

- Evidence produced: two internally consistent route documents.
- Strongest cheap baseline: sessions select whichever authority permits the
  desired work.
- Leakage/hard-coding risk: maximum; schema/authority split is the design.
- Smallest falsifier: make both routes claim `canonical` and observe that no
  unique next action is machine-decidable.
- Expected failure: conflicting successors and a permanent second logic path.

## Candidate C — additive supersession in the existing authority (selected)

- Product/capability authority remains
  `Ego/docs/PROGRAM_STATE_UNIFIED.yaml`.
- Science/attribution authority remains ITL
  `ROUTE-STATE-MACHINE-001A` at pinned HEAD
  `b67c94fe1244ef6006ed3af8e924d4c670fe64bb`.
- 8692 is superseded before M1; EgoDesktop future-route authority is archived;
  history and bounded Foundation evidence remain preserved.
- Renderers read structured Program State; validators validate it and fail
  closed; cross-repo references use committed-object pins.
- Smallest falsifiers: remove supersession, enable M1, restore EgoDesktop
  successor dependency, enable a science successor, create an undisposed
  lineage, enable pilot reuse with `audit_ref=null`, add an unbound action, or
  alter an ITL pin. Each must fail callable validation.
- Expected failure mode: if a second authority, runtime change, or non-computable
  lineage disposition is required, stop as `ANTI_ZENO_SCOPE_FAILURE`.

## Strongest baseline explanation

This is governance-only. A passing result means the route correction is
machine-readable and fail-closed; it does not create learning, a world model,
headroom, mechanism evidence, or life-like behavior.

## Strongest invalidation

The framing is invalid if current route facts cannot be computed from the one
Ego authority plus pinned ITL science readback, if runtime/source changes are
needed, or if a second authority must be created.

## Evidence still insufficient

Green tests, generated Markdown consistency, and reviewer approval remain
insufficient for any runtime, mechanism, learning, readiness, agency,
subjectivity, or consciousness claim.

## Risk audit

- Hard-coding: route values belong in structured Program State, not verifier
  literals or renderer constants.
- Local optimum / Zeno: no follow-on governance-only successor is allowed.
- Evidence leakage: capability verdicts remain capability-only; pilot #1 cannot
  be reused as a positive control or regression baseline without retro-Yellow.
- Weak baseline: explicitly bounded to governance-only effect.
- Schema split / second logic path: rejected by design and mutation tests.
- Replay weakness: existing generators must reproduce sinks byte-for-byte.
- Claim inflation: bounded by the Stage Card ceiling.

## Acceptance, stop, and rollback

Acceptance is the Stage Card's callable validation gate. Stop on any Stage Card
stop condition. Roll back only through a later authorized additive correction or
revert of the scoped local commits; never rewrite historical evidence.
