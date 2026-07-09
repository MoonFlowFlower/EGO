# EGO-K0-REFERENCE-KERNEL-001A — Minimal Learned Reference Kernel

Status: BLOCKED UNTIL FOUNDATION ACCEPTED + ITL H0 BANKED / DEFAULT-OFF /
NOT_RUNTIME_CONNECTED / DEV-SMOKE ONLY

Auto-Remote-Anchor: forbidden

## Task identity and source pins

- Task id: `EGO-K0-REFERENCE-KERNEL-001A`
- Canonical parent: ITL `K0-DUAL-TRACK-SUPERSESSION-001A`
- Parent commit: `4e4700ca6e00b1a0e2dc3adf6a6e473b2f6ef6be`
- Parent-card blob: `11b0e09025d1064a1eb790f42d79f1db3c690f6d`
- Parent-card SHA-256:
  `f93af34291de34457c08ba6f705886185321635d7333d175d987470f66b7d238`
- Ego drafting base: `760912a415f96547fbcb50cd42e0634aa787ab62`.
- Direct prerequisite: accepted `EGO-K0-FOUNDATION-001A` result plus a
  completed `H0_ADMISSION_READBACK.json` pointing to the banked ITL H0 contract.

This card may be banked now. It is not executable until every prerequisite hash
is present and a callable prerequisite verifier derives an accepted report.
Placeholder/null H0 fields keep it blocked; manually setting
`implementation_authorized=true` has no authority.

## Problem definition

The Foundation proves only persistence/serialization/replay plumbing. K0-R must
add a real learned action-conditioned outcome predictor, online parameter
updates, structured memory-conditioned action scoring, short-horizon constrained
planning, and replay training. Otherwise the route collapses into a rule pet,
lookup table, or decorative predictor.

K0-R is a reference instrument and construction target, not a formal science
candidate. It uses dev fixtures only. H1/headroom, immutable freeze, heldout
protocols, and component verdicts remain outside this card.

## Current layer

Engineering implementation + bounded learned-kernel hypothesis construction.
Maximum evidence here is dev-only implementation/load-bearing smoke evidence.

## Mainline, enabled state, and real trigger

- `mainline_connected=false`, `enabled=false`, `runtime_authority=none`.
- Entry point: explicit local CLI only; no import-time or background side effect.
- No EgoOperator, EgoDesktop, pet/R-track, UI, LLM, network, transport,
  notification, deployment, or mainline hook.
- Real trigger: a developer explicitly runs the reference-smoke CLI on H0-public
  dev fixtures after Foundation/H0 readback.
- No sealed-heldout seed, split label, family id, sequence position, hidden rule,
  or evaluator verdict may enter the kernel.

## Hypothesis

A single task-agnostic kernel with a learned outcome model and direct structured
state/memory-to-planner channel will change typed action rankings after legal
experience; predictor bypass/checkpoint swap/no-update interventions will expose
whether the learned path is load-bearing.

Falsifier: the predictor receives oracle/task ids, a task-specific branch selects
actions, planner output is unchanged under predictor interventions, learning is
a static table mislabeled as fit, or replay only replays stored actions.

## Strongest baseline and framing risk

The strongest baseline is a transition/lookup table, recency/history rule, or
the candidate's own update rule batched offline. Matching those later may deny
transfer, online advantage, or specialness, but this card does not adjudicate
them. The strongest construction risk is a learned predictor that is logged but
not used by the action selector.

Evidence still insufficient: a falling loss, changed weight hash, one action
change, or dev smoke pass cannot establish formal model/online/replay/memory or
transfer component evidence.

## Collision record

### Candidate 1 — rule scorer plus learned-looking trace
- Evidence: visible action changes.
- Cheap match: FSM/deficit queue/lookup.
- Leak risk: high; outcome model decorative.
- Falsifier: predictor bypass does not change ranking.
- Failure: rule pet; forbidden.

### Candidate 2 — task-specific learned table
- Evidence: online fit on dev episodes.
- Cheap match: transition table/exact history lookup.
- Leak risk: family/rule keys become labels.
- Falsifier: unseen legal factor combination or family-id removal.
- Failure: memorization reference only.

### Candidate 3 — task-agnostic learned predictor + planner (selected)
- Evidence: serializable online updates and load-bearing action ranking.
- Cheap match: full H0 controls remain for later formal comparison.
- Leak risk: adapter privilege or hidden task branch.
- Falsifier: checkpoint swap, planner bypass, shuffled outcome, and no-update do
  not produce preregistered directional smoke effects.
- Expected failure: useful implementation but formal components still untested.

## Implementation target

Add to the Foundation package only:

```text
packages/ego_k0_kernel/src/ego_k0_kernel/
  outcome_model.py
  online_update.py
  replay_buffer.py
  planner.py
  reference_kernel.py
  __init__.py       # export-only change
  cli.py            # additive reference-smoke subcommand
tests/test_ego_k0_reference_kernel.py
scripts/run_ego_k0_reference_smoke.py
scripts/verify_ego_k0_reference_prerequisites.py
scripts/ego_k0_reference_dev/__init__.py
scripts/ego_k0_reference_dev/adapter.py
scripts/ego_k0_reference_dev/fixture_loader.py
scripts/ego_k0_reference_dev/public_dev_fixture_manifest.json
scripts/ego_k0_reference_dev/smoke_contract.json
artifacts/ego_k0_reference_kernel_001a/
```

No wheel/dist/freeze artifact is built here.

The dev adapter/fixture bundle stays outside the wheel. It is copied from the
banked H0 public-dev export by hash; it cannot read an ITL working tree. Task
semantics in core package modules are forbidden.

## Kernel contract

The same frozen interface is used across tasks:

```text
initialize(config, seed) -> serialized_state
propose(serialized_state, observation, legal_actions) -> proposal, next_state
observe_outcome(serialized_state, transition) -> next_state, update_record
train_replay(serialized_state, replay_batch_refs) -> next_state, update_record
```

Minimum state includes model parameters, optimizer state, structured memory-use
state, bounded replay buffer, RNG registry, step/episode ids, ABI/config hashes,
and checkpoint lineage. All are canonical and serializable.

The learned model predicts an action-conditioned outcome distribution or typed
moments, not one renderer string. A constrained horizon `H=1-2` planner ranks
only supplied legal actions using predicted outcomes, declared bounded value
terms, and structured memory features. This is the non-prompt policy-
parameterization channel. No LLM is present or permitted to own state, writes,
ranking, gates, actions, or evidence.

Replay means replay **training** on referenced serialized transitions. K0 makes
no consolidation claim. Memory is limited to structured conditioning/use; no
learned memory-write policy or `learned_memory_update` claim is allowed.

## Required interventions and dev smoke

All are callable reruns on H0-public dev fixtures:

- no-update;
- shuffled outcomes;
- predictor checkpoint swap/counterfactual prediction;
- planner bypass with a declared neutral scorer;
- replay-off and corrupted replay rejection;
- memory-read-off/source deletion on fixtures that declare memory-use;
- serialize/restart/fresh-process replay x2.

Smoke checks require actual parameter/update deltas and at least one H0-declared
fixture where predictor/planner intervention changes ranking in the expected
direction. They do not assign formal component states.

## Trace/replay and computed provenance

Use `ego_k0.trace_replay.v1`. Add model input/output, uncertainty, candidates,
value terms, memory influence refs, selected proposal, feedback, prediction
error, optimizer/update delta, replay refs, and checkpoint lineage. Replay must
recompute proposals from serialized state plus observation.

`scripts/verify_ego_k0_reference_prerequisites.py` must fail closed and produce
`artifacts/ego_k0_reference_kernel_001a/prerequisite_report.json`. It verifies:

- the canonical parent is an ancestor of the pinned ITL H0 bank;
- exact parent/card/blob/task identities;
- Foundation acceptance verdict plus result, contract-manifest, trace/replay,
  and immutable-module hashes;
- H0 `h0_acceptance.json` status, producer, code-path hash, card-bank commit,
  contract/manifest hashes, public-dev fixture/smoke hashes, and heldout denial;
- every declared artifact hash by byte readback;
- all nulls are resolved and `raw_heldout_available_to_k0r=false`.

Only the computed prerequisite report may set `implementation_authorized=true`.
Tests must prove arbitrary non-null strings, broken ancestry, wrong status/hash,
or manually edited authorization cannot unlock the card.

Every dev metric/report records producer function, input hashes, run id,
seed/context/episode ids, aggregation, code-path hash, parent/H0/Foundation
hashes, and claim ceiling. No literal pass verdicts or test-only action path.

## Acceptance gate

Accept K0-R implementation only if:

1. callable prerequisite report returns the exact accepted status with parent
   ancestry, Foundation and H0 artifacts verified; non-null fields alone fail;
2. one learned action-conditioned model performs real seeded parameter updates;
3. planner ranking consumes model predictions and structured memory through one
   typed path; no second rule path selects actions;
4. no task/family/split/order/label/oracle input or task-specific branch exists;
5. model/optimizer/memory/buffer/RNG serialize, restart, and replay exactly;
6. no-update, shuffled-outcome, checkpoint-swap, planner-bypass, replay, and
   memory interventions run through callable paths and reports preserve mixed or
   negative outcomes;
7. dev adapter/fixtures are outside the wheel, hash-pinned, and do not import an
   ITL working tree; default-off/mainline/forbidden-import scans pass;
8. tests and dev smoke pass without sealed heldout or formal verdict output;
9. `__init__.py` changes are export-only and `cli.py` changes additive; every
   other accepted Foundation module is byte-hash frozen, and the full Foundation
   validation/restart/replay regression passes unchanged;
10. exact-path scope and diff check pass.

## Claim ceiling

Reference implementation of the declared paths. A dev-only load-bearing
subclaim may be made separately for model, online update, memory-conditioned
ranking, or replay training only when that subclaim's preregistered directional
smoke passes. Failed/unrun subclaims remain implementation-path existence only;
no combined load-bearing sentence is allowed unless every named subclaim passed.
No formal component
presence, headroom, transfer, specialness, consolidation, learned memory writes,
initiative, agency, autonomy, subjectivity, consciousness, functional subject,
electronic life, EGO/companion readiness, product benefit, or mainline effect.

## Stop conditions

Stop on missing/drifted prerequisites; sealed-heldout access; family/oracle
leakage; decorative predictor; task branch; second selector; non-serializable
model/optimizer/buffer; stored-action replay; unseeded randomness; need to touch
EgoOperator/EgoDesktop/old kernel/pet/runtime; formal scoring; threshold tuning;
or any push/tag/remote requirement.

## Rollback

Disable/remove only new K0-R package additions and retain the accepted Foundation.
Preserve failed dev artifacts. After a local bank, fixes are additive commits or
a superseding card; never rewrite H0, parent, old R-track, or negative evidence.

## Expected changed files

Card bank only: this task directory. Later implementation only: the exact package,
dev-adapter, verifier, test, runner, and artifact paths above. Forbidden: Foundation contract semantics,
SQLite adapter, old scripts/artifacts, program state/generated views except under
separate route-governance authorization, UI/runtime/LLM/network, ITL files,
wheel/dist/freeze, formal artifacts, push, tag, remote anchor.

## Local commit / next action

This landing turn may exact-path bank the card package. Implementation commits
are authorized only after prerequisites pass. Next action remains blocked until
Foundation acceptance and H0 bank readback populate the admission file.

## What this does not prove

This card neither implements nor evaluates K0-R. A later dev smoke would still
not prove mechanism validity or life-like subject properties.
