# EGO-K0-FOUNDATION-ACCEPTANCE-ROUTE-VIEW-SYNC-001A

Status: EXECUTABLE FOR LOCAL GOVERNANCE SYNC ONLY / STOP AFTER TWO LOCAL
COMMITS

Auto-Remote-Anchor: forbidden

## Problem definition

Synchronize the already-existing bounded Foundation engineering acceptance into
Ego's single canonical program-state authority, additive evidence ledger, and
generated views. Correct the existing route renderer that still classifies
`ego-k0-foundation-001a` as `supporting_active` after its authorization was
consumed and its bounded engineering evidence was accepted.

This is not a Foundation rerun, mechanism experiment, operator route decision,
or K0-R launch. It tests governance/evidence synchronization, not a mechanism
hypothesis or behavioral resemblance.

## Current layer, mainline, enablement, and trigger boundary

- Layer: Layer 2 — engineering/evidence-governance.
- Mainline target: none; `EgoOperator` remains the active default.
- K0 enabled: `false`.
- K0 mainline connected: `false`.
- Runtime authority: `none`.
- Runtime trigger evidence: absent.
- Real trigger evidence required here: callable local generators, verifiers,
  tests, Git-object readbacks, and the scoped closeout guard must recompute the
  synchronized governance state.
- Claim ceiling: local Ego authority/evidence/view synchronization for the
  existing bounded Foundation engineering acceptance only.

## Authority source and frozen provenance pins

The authorities are distinct and must not be collapsed:

1. Historical Foundation execution authority:
   - commit `07c0f1f85a3c855511ff1610ec9629f8e94e89b1`
   - route blob `5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3`
   - route SHA-256
     `ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37`
2. Foundation acceptance-transition semantic authority:
   - commit `ac85c046587675bceca86266cdf9e33183c6f3f9`
   - state blob `8e89e6c571bcacc391a19a2ab5b3ba989ac8091d`
   - state SHA-256
     `f9e413fbc91c2b6fb92aa6bc29409f8679f8e75fbe70646e45a68b720c2700df`
   - closure blob `16c608bf2b351407618cef9a16cd47f13c452690`
   - closure SHA-256
     `c4f2ca41db4d8217bf3e97d34ca8892c5c75be784bd28ce2a8504032bc955778`
3. Reviewed test-hardening descendant:
   - commit `990c667ea78a86201d9090b1d6b6cf554074d248`
   - test blob `bf8eef5d8b6c7aba447c36accca1827419a68849`
   - test SHA-256
     `508bb01918f38bcb4b1cc6370021be2444dc4c0eb7986a2141489145d386fdf4`

`990c...` is not the transition-producing commit. `ac85...` does not replace
the historical execution authority.

## One hypothesis

If the existing bounded acceptance is recorded once in Ego's canonical program
state and additive ledger, and the existing renderer/verifier sinks are updated
to encode the consumed authorization, then the canonical generators will place
Foundation only in `closed_evidence`, keep Reference Kernel parked, preserve
EgoOperator as the sole active default, and remove stale READY/authorized-only
semantics without creating a second authority or cross-repo validator.

## Strongest baseline and framing risk

The strongest baseline is hand-written acceptance prose followed by generator
self-consistency. It can make checks green without proving authority freshness,
authorization consumption, or the correct lane.

The strongest invalidity risk is producing a second truth source by copying the
ITL state, closure, or 14-file Foundation manifest into Ego, or by adding a new
cross-repo provenance validator. Another invalidity risk is hard-coding a total
task count rather than local sink invariants.

The framing is falsified if any authority/artifact pin drifts, the ITL route
suite is not exactly 205 passing tests, the official Foundation tree changes,
E3/V3 cannot remain a bounded Ego governance classification, a second schema or
validator is required, or Foundation remains in `supporting_active`.

Evidence still insufficient after success: local authority/view convergence
cannot prove runtime/mainline effect, learning, mechanism validity, initiative,
agency, autonomy, subjectivity, consciousness, readiness, or stable user
benefit.

## Bounded audit / collision record

### Candidate A — edit YAML, prose, and generated views only

Reject. `scripts/codex/route_convergence_common.py` would continue generating
Foundation as `supporting_active`; old green checks would only establish stale
self-consistency.

### Candidate B — copy ITL state, closure, or the complete manifest into Ego

Reject. This would create a second authority and a future schema-drift surface.

### Candidate C — one Ego authority, additive ledger, renderer/verifier sink

Select. Update the canonical program state and ledger, correct only the existing
route override/verifier, and regenerate existing views through existing
generators. Do not create a cross-repo validator.

## Frozen synchronized state

The K0 workstream must record:

```yaml
status: "foundation_engineering_accepted_bounded__authorization_consumed__operator_decision_required__runtime_disabled__non_mainline"
evidence_level: "E3"
verification_level: "V3"
mainline_connected: false
enabled: false
```

The authority/readback must preserve:

- current state `CLOSURE_REVIEW_REQUIRED`;
- phase `FOUNDATION_ENGINEERING_ACCEPTED_H0_NOT_TESTED_OPERATOR_DECISION_REQUIRED`;
- closure `GOVERNANCE_STOP`;
- Foundation `BANKED_ACCEPTED_BOUNDED`, authorization consumed;
- H0 `NOT_TESTED`;
- K0-R/H1/Freeze/Formal `BLOCKED_NOT_TESTED`;
- every route and child authorization `false`;
- authorized implementation targets `[]`.

E3/V3 is Ego's governance classification of repeatable local multi-module
verification. It is not a computed field from `result.json` and must not be
upgraded to runtime, mainline, learning, or mechanism evidence.

## One change surface / Expected Mutation Surface

Phase A banks only this card and its task-local mutation scope. Phase B changes
only:

- `docs/PROGRAM_STATE_UNIFIED.yaml`;
- `artifacts/evidence_ledger/index.yaml` (one additive top entry; prior entries
  remain byte-for-byte in their original order);
- `scripts/codex/route_convergence_common.py`;
- `scripts/codex/verify_route_convergence.py`;
- generated `docs/STATUS.md`;
- generated `docs/codex/tasks/TASK_LANE_INDEX.md`;
- generated `artifacts/reports/program_state_summary.md`.

The renderer must place Foundation in `closed_evidence` with bounded accepted,
authorization-consumed, disabled, non-mainline, no-runtime-authority semantics.
Reference Kernel stays in `parked` with Foundation accepted, H0 closed pre-run
and NOT_TESTED, all children false, and operator replace-versus-close decision
pending.

The verifier must enforce local sink invariants only: unique Foundation in
`closed_evidence`, absent from `supporting_active`; unique Reference Kernel in
`parked`; active default still `ego-operator-human-operator-trial-v2`; and stale
READY/authorized-only language absent. It must not read ITL or hard-code a total
task count.

At this commit boundary the expected lane counts are 1 active default, 1
supporting active, 2 parked, 20 closed evidence, and 229 reference only.

`docs/REPO_HYGIENE_POLICY.md` and `docs/REPO_SURFACE_MAP.md` must remain
byte-identical and unstaged before and after generation.

## Ablation / contrast requirement

No mechanism ablation or Foundation rerun is authorized. The governance
contrast is the callable before/after route readback: stale Foundation
`supporting_active` / authorized-only semantics before, versus unique
`closed_evidence` / authorization-consumed semantics after, while all runtime
and child authorizations remain false.

## Trace, replay, and computed-evidence provenance gate

- Do not rerun the official Foundation evidence producer.
- Run the existing focused Foundation suite and prove the official 14-file
  path/SHA/blob snapshot is unchanged before and after.
- Preserve artifact tree
  `907457e7d3028ba5437cf0e7730ec068a21cbf6b`, result blob
  `a8b3237afc40a1f56df3906870ff94c5db9c10ff`, and result SHA-256
  `834b4764514062f8937488fd4b89684b5ae684e9522d67f440ed3c077f077067`.
- ITL acceptance comes from its callable route suite,
  `build_validation_report(Path.cwd())`, status, and dashboard. Do not run
  `routectl validate`.
- Ego acceptance comes from existing generators, integrity/convergence/
  mainline/repo verifiers, bootstrap, Git-object reads, and scoped closeout.
- The ledger does not manufacture a new result; it points to the immutable
  official computed artifact.

## Three-level verification / acceptance gate

### Level 1 — authority and source integrity

- Both repo preflights and all named commit/blob/SHA pins match.
- ITL route suite: exactly `205 passed` with correct `PYTHONPATH`.
- Read-only ITL validation: pass, zero errors, zero warnings.
- ITL status and dashboard pass; `routectl validate` is not run.
- Ego focused Foundation suite: exactly `32 passed`.
- Official 14-file artifact snapshot/tree/result pins remain unchanged.

### Level 2 — generated sink and invariant verification

- Run both canonical view generators.
- Run program-state integrity, route convergence, mainline clarity, and fast
  repo verification.
- Post-sync bootstrap names the operator replace-versus-close decision and no
  longer instructs execution of Foundation.
- The ledger entry is unique and every prior entry remains in its prior order.
- Foundation is unique in `closed_evidence`, absent from `supporting_active`;
  Reference Kernel is unique in `parked`; active default is unchanged; stale
  READY/authorized-only semantics are absent.

### Level 3 — scope and committed-object proof

- Phase A stages/commits exactly two task-bank paths.
- Phase B stages/commits exactly the seven declared governance/view paths.
- Working and cached `git diff --check` pass.
- Task-scoped closeout guard passes.
- Post-commit Git-object readback proves both exact commits and path sets.
- Final Ego tracked worktree/index is clean at expected ahead/behind `13/0`.
- ITL remains at `990c...`, ahead/behind `26/0`, tracked clean, with only the
  two frozen unrelated untracked files.

## Stop condition

Stop without scope expansion on any preflight, pin, count, status, test
signature, or artifact mismatch; any unauthorized generated diff; any need to
change schema, `program_state_common.py`, Foundation source/test/runner/artifact,
EgoOperator, EgoDesktop, or ITL; any need to rerun H0 or execute K0-R/H1/Freeze/
Formal; any need to make the operator replace/close decision here; or any need
to push, tag, or remote-anchor.

If Phase A is committed and Phase B fails, preserve Phase A and stop. Do not
amend, reset, rebase, or rewrite history.

## Rollback plan

Before a phase commit, remove only uncommitted edits created by that phase if
validation fails. After a phase commit, preserve it and require a separately
authorized additive correction. Runtime rollback is not applicable because no
runtime, enablement, or mainline path changes.

## Forbidden changes

- Any ITL file or sibling-repo validator.
- Foundation package, source, test, runner, or official artifact.
- `program_state_common.py`, a new schema, or a second route logic path.
- `EgoOperator/**`, `EgoDesktop/**`, task board, project contract, runtime
  registration, memory/gate/approval/transport/proactive behavior.
- H0/K0-R/H1/Freeze/Formal execution or authorization.
- Push, tag, remote anchor, amend, reset, rebase, or history rewrite.

## Local commit authorization

Exactly two local commits are authorized after exact staging and checks:

1. `docs: bank EGO K0 Foundation acceptance route-view sync`
2. `governance: sync EGO K0 Foundation acceptance boundary`

Stage only literal phase paths. `git add -A` is forbidden. Stop after the second
local commit and return an independent-review handoff receipt.

## What this does not prove

This task does not prove a learned model, learning, causal memory/replay
contribution, mechanism validity, runtime or mainline effect, initiative,
agency, autonomy, subjectivity, consciousness, functional-subject status,
electronic life, EGO/companion/production readiness, stable user benefit, or
all-scenario stability.

## Next minimal closed-loop action

After the two local commits, stop for independent review synchronization. A
separate operator decision may later choose either to replace the closed H0
branch or close the K0 science route. Do not start K0-R in this task.
