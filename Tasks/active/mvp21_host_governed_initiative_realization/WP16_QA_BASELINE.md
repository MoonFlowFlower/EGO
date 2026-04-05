# WP16 / MVP21 QA Baseline

## 1. Document Purpose

This file is the formal QA baseline for `WP16/MVP21` in `maintenance_mode`.

It answers only three questions:

- what `WP16` has formally proven
- how future maintenance verification must be run
- which failures stay bugfix-only versus require reopen

This is not a design document. It does not expand authority, define `WP17+`, or rewrite the `WP16` closeout claim.

## 2. Current Official Claim

The only allowed official claim is:

> `WP16/MVP21` has implemented a governed mainline version of `proposal-only initiative realization writeback`, has reached `V5/E5` on the controlled axis, and is now in `maintenance_mode`.
> This does not prove `live autonomy / direct reply authority / tool authority / broader transport claims`.

Any wording broader than that is treated as a reporting or documentation error.

## 3. Proven Functional Boundary

The formally proven boundary must stay narrowed to these five points:

- `realization readiness pressure -> bounded review-first downstream weighting`
- `commitment fulfillment preparation -> structured realization proposal candidates`
- `delivery failure and low reserve -> guarded hold / repair-review bias`
- `host-lane mediation hints stay bounded and gated under host governance`
- `text-only wording changes do not create false downstream behavioral proof`

Together these prove:

- `initiative_realization` is the single formal owner for realization / fulfillment / readiness semantics
- it enters the formal mainline through the bounded `initiative_realization` contract
- it changes later bounded tendency / weighting in a measurable way under `proposal_only`
- it does not gain direct reply / tool / transport authority

This file does not prove:

- live autonomy
- OpenEmotion direct reply authority
- tool authority
- broader transport maturity
- direct outbox enqueue authority
- direct transport enable-policy takeover

## 4. Five-Layer Test Matrix

### Layer A: Unit / Contract

Goal:

- formal owner state, store, governance, and replay primitives are real and stable

Fixed entry:

- `OpenEmotion/tests/mvp21/test_realization_owner_infra.py`

Pass signals:

- initiative realization owner state can be created, updated, persisted, and restored
- replay / governance / proposal discipline constraints hold

### Layer B: Causal

Goal:

- realization / fulfillment proposals change later bounded strategy rather than only changing wording

Fixed entry:

- `OpenEmotion/tests/mvp21/test_realization_causal_formal_proof.py`
- `OpenEmotion/artifacts/mvp21/mvp21_causal_validation_current.md`

Pass signals:

- readiness, fulfillment, hold, and failure-recovery conditions cause structured downstream shifts
- wording-only cases with no downstream shift are rejected as proof

### Layer C: Boundary / No-Bypass

Goal:

- OpenEmotion owns initiative realization semantics without bypassing host governance

Fixed entry:

- `OpenEmotion/tests/mvp21/test_mvp21_mainline_reference_demotion.py`
- `OpenEmotion/tools/verify_mvp21_mainline_wiring.py --json`

Pass signals:

- `WP7` host proactive substrate remains `host_substrate_only / reference-only`
- historical proactive / roadmap material remains `technical reference` or `reference-only`
- realization outputs do not become direct reply / tool / transport authority

### Layer D: Replay / Wiring

Goal:

- the formal mainline is real, and replay / trace remain sufficient for audit

Fixed entry:

- `OpenEmotion/tests/mvp21/test_realization_proto_self_integration.py`
- `EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k realization`
- `OpenEmotion/tools/verify_mvp21_mainline_wiring.py --json`

Pass signals:

- `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` remains the only formal mainline
- initiative realization context is injected and consumed in bounded form
- trace / replay remain sufficient for gated realization writeback

### Layer E: Controlled Observation

Goal:

- maintenance conclusions remain backed by real mainline observation, not only unit tests

Fixed entry:

- `OpenEmotion/tests/mvp21/test_controlled_observation.py`
- `OpenEmotion/tests/mvp21/test_controlled_observation_batch.py`
- `OpenEmotion/tools/run_mvp21_controlled_observation.py`
- `OpenEmotion/tools/run_mvp21_controlled_observation_batch.py`
- `OpenEmotion/artifacts/mvp21/mvp21_controlled_observation_current.md`
- `OpenEmotion/artifacts/mvp21/mvp21_controlled_observation_batch_current.md`

Pass signals:

- single-sample `V4/E4` remains reproducible
- batch `V5/E5` remains true
- `proposal_only_discipline_count`, `behavioral_authority_none_count`, and `bounded_influence_present_count` continue to hold

## 5. Ten-Point Checklist

Each `WP16` maintenance verification must evaluate at least these ten checks:

1. `initiative_realization/*` remains the only formal owner target.
2. `WP7` proactive runtime / delivery / outbox / transport surfaces remain `host_substrate_only` and are not reattached as `WP16` fallback truth.
3. `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` remains the only formal consumer path.
4. initiative realization owner state / store / governance / replay primitives still work.
5. realization proposals still change later bounded tendency / weighting.
6. wording-only changes without structural downstream shift still fail as proof.
7. realization outputs still have no direct reply / tool / transport authority.
8. trace payload and replay remain sufficient to explain proposal generation and gated writeback.
9. single controlled observation still reproduces `V4/E4`.
10. repeated aggregate still preserves `V5/E5`, or the report explicitly says the run only refreshed maintenance verification and did not alter closeout status.

## 6. Failure Grading and Reopen Rules

### A. Documentation Correction

Use when:

- `proposal-only initiative realization writeback` is misreported as proactive send autonomy
- axis-local `E5` is misreported as global maturity
- non-proven claims are written as proven

Action:

- correct docs / reporting
- do not reopen `WP16`

### B. Bugfix Only

Use when:

- references drift
- runner / report / scenario-bank defects occur
- the issue does not affect owner uniqueness, proposal discipline, behavioral authority, or replay consistency

Action:

- scoped bugfix
- rerun the impacted layer
- record it in the maintenance ledger
- do not automatically reopen `WP16`

### C. Hotfix / Regression

Use when:

- any of the five layers regresses
- but the authority source and formal owner remain intact

Examples:

- causal test regression
- single-sample observation regression
- wiring / replay regression

Action:

- ship a scoped hotfix
- rerun the impacted layer and adjacent layer
- record it in the maintenance ledger
- escalate only if a reopen condition is hit

### D. Reopen Required

Any of the following requires `WP16 reopen discussion`:

- formal owner uniqueness fails
- `WP7` host substrate or historical proactive surfaces become formal owner or fallback truth again
- direct reply / tool / transport authority leaks
- proposal discipline fails
- `behavioral_authority` is no longer `none`
- replay consistency structurally fails
- evidence classification is wrongly elevated and corrupts the closeout basis

After reopen, these must be re-decided:

- current layer
- authority source
- current blocker
- whether `maintenance_mode` can be retained

## 7. Allowed and Forbidden in Maintenance

### Allowed

- bugfix
- regression repair
- artifact refresh
- observation rerun
- aggregate refresh
- maintenance ledger intake
- wording correction

### Forbidden

- authority expansion
- direct reply authority release
- tool authority release
- broader transport claims
- direct outbox enqueue authority
- direct transport enable-policy takeover
- rewriting the `WP16` maintenance claim into a new phase scope

## 8. Standard Maintenance Report Template

Every `WP16` maintenance verification should report:

- verification scope:
  - which layers were run
- pass items:
  - only results aligned to this baseline
- fail items:
  - explicitly grade as documentation correction / bugfix / hotfix / reopen
- what this run still does not prove:
  - retain `live autonomy / direct reply authority / tool authority / broader transport claims`
- reopen decision:
  - `yes / no`
