# EGO-CANONICAL-MECHANISM-INTEGRATION-001A

Status: `M0_ROUTE_FREEZE_AUTHORIZED__M1_NOT_STARTED`

Auto-Remote-Anchor: forbidden

## Task identity and operator decision

- Task id: `EGO-CANONICAL-MECHANISM-INTEGRATION-001A`
- Operator decision date: `2026-07-13`
- Operator decision: freeze competing routes, select one integration route, and
  make the route unambiguous for every fresh session.
- Ego base branch: `main`
- Ego base HEAD: `92d13c116133b56a8c0eb61d8abb411b6b7daf3d`
- Ego base tree: `51f749eab22508dd6cdc4d4dc1637db596c10247`
- Base worktree: clean; upstream behind/ahead `0/0`.

Pinned component trees at the route decision:

| component | role | git object |
|---|---|---|
| `packages/ego_k0_kernel/` | sole event/state/persistence/trace/replay substrate | `43380f76c37b05f36a4a4ef45354048787cafe68` |
| `labs/virtual_cat_pspc_v0/` | source-only world/self-model candidate | `654359fc1ab4e0137e2fa929e6cb57a240381cdf` |
| `EgoDesktop/` | sole future user-visible observer/test host | `2c29bc0c81ba06fff3ed98dbce2235ce10e0817a` |

Pinned evidence inputs are listed in
`docs/EGO_CANONICAL_MECHANISM_INTEGRATION_ROUTE_001A.md`. They remain evidence
inputs, not runtime authority.

## Problem definition

The repository contains many individually bounded K0, PSPC, PET, shadow,
adapter, and outcome-utility tasks, but no new enabled product path combines the
strongest surviving pieces. Fifty workstreams exist while only the old
`EgoOperator` workstream is both enabled and mainline-connected. Historical
`go_for_*` strings and many default-off shadow tasks can therefore mislead a
fresh session into continuing an obsolete local optimum.

The real objective is one testable successor path, not another isolated gate:

```text
K0 Foundation canonical substrate
  -> VirtualCatPSPC-derived world/self model adapter
  -> EgoDesktop observer and bounded input surface
```

This task first freezes route authority, then permits one default-off integration
lineage. It does not switch the current runtime mainline in M0.

## Current layer

- M0: engineering/governance integration hygiene.
- M1-M3: engineering implementation plus bounded mechanism-hypothesis testing.
- No philosophical-consciousness or subjectivity-validation claim is in scope.

## Mainline target, enabled state, and real trigger

- Current runtime owner remains `EgoOperator` until a separately reviewed
  transition gate is satisfied.
- Selected successor target is `EgoDesktop`, not `EgoOperator`.
- M0 state: `mainline_connected=false`, `enabled=false`,
  `runtime_authority=none` for the successor.
- M1 and M2 must remain default-off behind one explicit developer flag.
- A real trigger is absent at M0.
- The first acceptable real trigger must traverse one callable path:

```text
EgoDesktop input/observation
  -> K0 canonical event/state transition
  -> world/self-model prediction
  -> actual environment feedback
  -> computed prediction error
  -> serialized model update
  -> later prediction or proposal change
  -> K0 trace and fresh-process replay
```

No renderer event, stored action, scripted verdict, or old PET reflex counts as
this trigger.

## Hypothesis

If the accepted K0 Foundation owns canonical state/event/trace/replay, a
VirtualCatPSPC-derived adapter owns auditable learned prediction state, and
EgoDesktop remains a pure observer/input host, then one default-off executable
can test whether prediction-error-driven updates change later proposals without
creating a second kernel or mistaking UI behavior for mechanism evidence.

## Strongest baseline and invalidity risk

Strongest equal-access baselines:

1. schedule-aware static policy;
2. `count_table` / transition lookup;
3. fixed prediction-error threshold plus direct overwrite;
4. observation-only decoder;
5. stored-action replay.

The framing is invalid if any equal-access baseline matches the candidate on the
predeclared post-shift metric, or if frozen updates/no-prediction-error-learning
does not remove the claimed effect. Passing serialization, UI smoke, or replay
alone is insufficient.

## Collision requirement

`COLLISION_RECORD.md` is binding. It rejects:

- running old PET P2 as a substitute for the selected mechanism;
- connecting VirtualCat directly to Electron and bypassing K0;
- continuing the old PSPC shadow/governance ladder.

The selected candidate is K0-owned state plus an external, auditable
VirtualCat-derived mechanism adapter plus an observer-only EgoDesktop surface.

## Milestones

### M0 — route authority freeze and session safety

Change only the task package, canonical route document, program state,
onboarding/agent instructions, route-view generator rules, and mechanically
generated views. No runtime or mechanism code.

Acceptance:

1. `docs/PROGRAM_STATE_UNIFIED.yaml` names this as the sole selected successor.
2. `AGENTS.md`, `docs/ACTIVE_CONTEXT_PACK.md`, and `README.md` point new sessions
   to the canonical route document.
3. Historical PET/PSPC/outcome routes are explicitly frozen as non-authoritative
   predecessors; their stored artifacts are not edited.
4. The task lane index marks this task `supporting_active` while `EgoOperator`
   remains the one `active_default` runtime.
5. Bootstrap, program-state integrity, route convergence, mainline clarity,
   scoped closeout, and diff checks pass or report exact blockers.

### M1 — headless canonical mechanism bridge

Implementation authorization: granted by the 2026-07-13 operator decision only
after M0 is committed and a fresh session confirms the M0 pins and clean tree.

Before editing K0 core, run a feasibility test proving that model parameters,
optimizer/update context, prediction, feedback, prediction error, and update
lineage can be represented inside canonical serialized state and recomputed by
the same source/replay path. If this requires adapter-owned hidden state or a
second state transition authority, STOP.

M1 expected surfaces, subject to the feasibility stop:

```text
packages/ego_k0_kernel/src/ego_k0_kernel/       # minimal canonical extension only
scripts/ego_canonical_mechanism/                # adapter + headless harness
tests/test_ego_canonical_mechanism_*.py
artifacts/ego_canonical_mechanism_integration_001a/m1/
```

M1 must not touch `EgoDesktop`, `EgoOperator`, old PET sources, VirtualCat lab
sources, or historical artifacts.

### M2 — default-off EgoDesktop observer integration

Permitted only after M1 passes its engineering gates and a post-result routing
check says `advance`. Add one developer-flag entrypoint. EgoDesktop may relay
inputs and render K0 frames; it may not own policy, model updates, state, scoring,
or verdicts.

### M3 — visible intervention and replay evidence

Run a preregistered visible session with at least one environment shift and real
learner ON/OFF interventions. Bank raw trace, independent baselines, ablations,
positive-control leakage scan, and fresh-process recomputing replay. M3 may
produce proxy evidence only.

## Ablation requirement

M1/M3 must rerun episodes under real interventions:

- frozen world-model updates;
- no prediction-error learning;
- self-model frozen or removed where the selected proposal depends on it;
- candidate mechanism removed while K0/event/UI access remains unchanged.

An ablation label without a rerun is invalid.

## Trace/replay requirement

- K0 is the single canonical event/state/trace/replay authority.
- Model state and update lineage must be serialized in canonical K0 state or in
  canonical source events sufficient to reconstruct it.
- Replay must recompute predictions, prediction errors, updates, proposals, and
  next state from checkpoint plus observations/feedback.
- Stored actions/hashes may be comparison inputs only, never replay authority.
- Fresh-process replay x2 and mid-episode resume are required before M1 closes.

## Computed-evidence provenance gate

Every evidence-bearing score or verdict must record:

- `producer_function`;
- input artifact hashes;
- task/run/episode/context identifiers;
- seed and update context;
- aggregation rule;
- code-path hash;
- baseline/ablation callable identifiers.

Leakage scans require a real scanner and firing positive control. Unused frozen
seeds, contexts, or interventions block the claim.

## Acceptance gate

M0 acceptance is route clarity only. Full integration acceptance requires:

1. one real default-off entrypoint;
2. one enabled developer session;
3. a real observation/feedback trigger;
4. prediction, error, update, and later behavioral change in the same trace;
5. independent callable baselines under access parity;
6. real ablation reruns that remove the claimed update effect;
7. recomputing replay with zero mismatches;
8. no second policy/state/evidence path;
9. honest UI label and bounded claim ceiling;
10. an independent post-result review before any mainline transition.

## Claim ceiling

M0: route selection, freeze, and evidence-hygiene documentation only.

M1-M3 maximum: default-off engineering integration and measured adaptation
within the preregistered environment distribution. No stable user benefit,
agency, autonomy, functional subject, subjectivity, consciousness, emotion,
companion readiness, EGO readiness, or production/mainline claim.

## Stop conditions

Stop without broadening authority if:

- source pins or route authority conflict;
- a cheap equal-access baseline can match the candidate;
- K0 cannot own serialized model/update state without a second transition path;
- VirtualCat historical sources/artifacts would need rewriting;
- old PET reflex/direct-write code becomes the candidate mechanism;
- Electron owns model/state/scoring/verdict logic;
- replay trusts stored actions or misses update reconstruction;
- P0/P1-style governance repair repeats without increased discriminative
  mechanism evidence;
- mainline, external side effects, push, or tag would be required.

## Rollback plan

- M0: revert only this additive route-freeze commit with a later authorized
  correction; do not rewrite historical artifacts.
- M1/M2: remove or disable only newly added default-off integration modules and
  keep M0 route/negative evidence.
- No current runtime rollback is required because M0 does not change runtime and
  M1/M2 must remain default-off.

## M0 expected changed files

- `AGENTS.md`
- `README.md`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/ACTIVE_CONTEXT_PACK.md`
- `docs/MAINLINE_QUICKSTART.md`
- `docs/EGO_CANONICAL_MECHANISM_INTEGRATION_ROUTE_001A.md`
- `docs/codex/tasks/ego-canonical-mechanism-integration-001a/**`
- `scripts/codex/route_convergence_common.py`
- `scripts/codex/verify_route_convergence.py`
- mechanically generated route/program-state views only

## Forbidden changes in M0

- `packages/ego_k0_kernel/**`
- `labs/virtual_cat_pspc_v0/**`
- `EgoDesktop/**`
- `EgoOperator/**`
- `scripts/ego_pet/**`, `scripts/ego_pet_capability/**`
- all historical evidence artifacts and prior task cards
- evidence ledger, task board, ITL repo, push, tag, or remote anchor

## Local commit authorization

One scoped local M0 commit is authorized after all M0 gates pass. Push, tag, and
remote anchor are forbidden.

## What this does not prove

This card and M0 route freeze do not implement the bridge, enable a new program,
observe a real trigger, validate the mechanism, or prove any subjectivity-related
claim.
