# EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A

Status: `READY_FOR_TEST_FIRST_EXECUTION`

Auto-Remote-Anchor: `forbidden`

Task ID: `EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A`

Current stage: `Phase A.1 product repair; Phase B not entered`

## Problem definition and real objective

Repair the existing explicit, default-off V2 product path so a
`resource_appears` command creates one environment-owned resource interaction
opportunity. A `forage` action at `site_a` must resolve that opportunity even
when the agent is already at the site, and energy gain must depend on the
resolved hidden-regime outcome rather than movement, cue, or action alone.

This is a product defect repair. It does not test whether viability, learning,
a dynamic causal boundary, or electronic life exists.

## Live preflight and source pins

- Ego at task start: branch `main`, HEAD
  `0b72f9d12e9e90e0f91e39bef98bb8dc2c2d7551`, clean, ahead 27 / behind 0.
- ITL at task start: branch `codex/meta-theory-scaffold`, HEAD
  `0bdc05ff5d2e6001beb35d66ccc1485de300ac90`, clean, ahead 21 / behind 0.
- The two product-axis payloads at
  `artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json` have the same
  SHA-256:
  `1d3ea7dc5725b3046f4be043451def2d3abc8ce4201635c45ed2c5091b8d8fa6`.
- The effective product action is
  `develop_v2_in_ego_with_local_bounded_task_card`; the explicit entrypoint is
  `scripts/run_ego_life_playground_v0.py`, enabled only after explicit launch.
- Science experiment execution remains false. This task does not enter Phase B
  and changes no ITL file or route-control file.

Any worktree collision, authority-payload mismatch, source-pin mismatch, or
unlisted write before the first product-code edit is a stop.

## Current layer, mainline target, enabled state, and real trigger

- Current layer: Layer 2, product engineering implementation and evidence
  hygiene.
- Mainline target: the existing single path
  `PlaygroundController.dispatch -> engine.compute_step ->
  microworld.transition_world -> engine.compute_metabolism_ledger ->
  SQLiteEventStore.append_step/recover_run`.
- Mainline integration: already connected to the explicit local V2 product
  entrypoint; no new entrypoint or side path is permitted.
- Enabled-state requirement: explicit Step/Run only; default enablement,
  autostart, background dispatch, network, and LLM remain off.
- Real-trigger requirement: acceptance must execute a real controller dispatch,
  persist it, and recover it through SQLite. The observed pre-repair trigger is
  a stationary `forage` at `site_a` under `resource_appears` with
  `moved=false`, no outcome, and no energy gain.
- Claim ceiling: bounded product engineering repair only.

## Bounded audit

### Hypothesis

Deriving one resource instance from the command hash, resolving it inside the
existing world transition, and requiring that interaction result in the
existing metabolism ledger is sufficient to close the stationary-resource
defect without changing the world-state schema or adding a controller, store,
reducer, or replay path.

### Strongest baseline explanations

1. The current moved-only rule explains the defect but rejects a legitimate
   stationary interaction.
2. A cue-only rule (`resource` or `resource_appears` means food) can imitate
   visible energy recovery while ignoring action and hidden outcome.
3. A fixed action/cue table can reproduce every visible behavior in this task.
   Therefore even a successful repair remains engineering evidence only.

### Strongest reason the framing may be invalid

If the command hash, resource instance, hidden regime, stored trace, or future
state leaks into policy observation; if the same command can settle twice; or
if SQLite recovery trusts stored interaction fields instead of recomputing
them, the apparent closure is not causal and the task fails.

### Falsifier and still-insufficient evidence

- Falsifier: energy gain on no resource event, non-forage action, negative
  resource outcome, or replay without a recomputed positive interaction.
- Falsifier: identical source command hashes produce different instance IDs,
  or different resource commands produce the same instance ID.
- Still insufficient: correct energy arithmetic, a truthful UI, replay
  equality, or tamper rejection. None establishes viability, learning, a
  self/world boundary, agency, or electronic life.
- This task tests an engineering causal contract, not a mechanism hypothesis.

### Anti-hardcoding, leakage, and second-path audit

- No seed-, sequence-, run-, fixture-, filename-, or expected-action exception.
- Resource instance ID is post-outcome evidence only and never enters the
  policy observation or candidate scorer.
- Hidden regime remains environment-owned and is read only by the world
  transition that produces the outcome.
- No cue-only food predicate, no stored-trace input, and no future observation.
- Live execution and recovery call the same `compute_step` code bytes.
- No second controller, reducer, state store, replay path, UI-only settlement,
  timer, network, or LLM path.

## Task-local causal contract fixed before RED

For every `resource_appears` command:

```text
resource_instance_id = sha256(
    utf8("resource_instance|" + source_command_hash)
)
```

The instance ID appears only in post-outcome trace data. A resource interaction
has this exact record:

```text
instance_id
available
attempted
resolved
outcome
food_obtained
failure_reason
```

Settlement rules:

```text
available = current event is resource_appears and the visible resource is at site_a
attempted = selected action is forage and action target/post-action position is site_a
resolved = available and attempted
outcome = environment hidden-regime result (+1 or -1) iff resolved
food_obtained = resolved and outcome == +1
```

Failure reasons are task-local, deterministic trace labels:

```text
no_resource_event
resource_not_attempted
harmful_or_unusable_resource
null on successful food acquisition
```

An unresolved resource interaction has no outcome and no food. A negative
resolved interaction has an outcome but no food. Existing moved-site outcomes
remain intact; only the resource/forage food predicate is changed. Safety,
connection, and stimulation settlement rules remain unchanged.

Energy remains:

```text
passive_decay = 0.020
action_cost = ACTION_COSTS[selected_action]
food_gain = 0.280 if food_obtained else 0.0
energy_after = clamp01(
    energy_before - passive_decay - action_cost + food_gain
)
```

## Collision result

The paired collision record is:

`docs/codex/tasks/ego-v2-p0-resource-interaction-outcome-repair-001a/COLLISION_RECORD.md`

Selected approach: add one interaction result to the existing world transition,
validate it in the existing metabolism ledger, and display the resulting trace
in the existing visual console. The moved-only and cue-only approaches remain
independent hostile baselines.

## Baseline and ablation requirements

- Independent moved-only baseline: food requires `moved=true`; it must fail the
  stationary positive case.
- Independent cue-only baseline: resource cue/event grants food; it must be
  rejected by non-forage and negative-outcome controls.
- Real ablation: rerun the same serialized state and command through
  `compute_step` with task-local food gain set to zero in memory. The selected
  action and interaction outcome must stay the same while `energy_after`
  decreases.
- Baselines and ablation are evidence-boundary checks, not mechanism evidence.

## Trace, replay, and provenance requirement

- New traces use `ego.life_playground.trace.v6`.
- Preserve top-level `moved`, `visited_site`, `outcome`, and `food_obtained`
  inside `world_transition` for existing consumers.
- Add the exact `resource_interaction` record above to post-outcome trace data.
- Preserve the existing metabolism fields: `energy_before`, `passive_decay`,
  `action_cost`, `food_gain`, `energy_after`, and `downstream_effect`.
- SQLite recovery must start from serialized initial state plus ordered stored
  commands, rerun `compute_step`, and compare stored traces only afterward.
- Two independent fresh processes must produce the same state, action,
  interaction, energy ledger, and trace hashes.
- Tampering with `resource_interaction`, the stored trace, or initial state must
  fail closed.
- A callable recursive leakage scanner must inspect both policy projections for
  resource-instance and post-outcome interaction data. The real projection must
  be clean, and an injected positive-control instance ID/key must be detected.

All result, baseline, ablation, replay, and tamper findings must be produced by
callable functions. Each evidence record must identify `producer_function`,
input artifacts, `run_id`, seed/context/episode IDs, aggregation rule, and code
path hash. Static pass dictionaries and pass-only assertions are inadmissible.

## Test-first sequence and two-iteration budget

### Focus iteration 1 — causal path

1. Add focused tests without changing product code.
2. Run them and preserve the expected RED readback.
3. Modify only the existing world-transition/metabolism/trace path.
4. Run focused tests, independent baselines, ablation, SQLite replay,
   fresh-process x2, and tamper controls.

### Focus iteration 2 — UI expression

1. Add UI truthfulness tests and observe RED.
2. Require the view to render only the recovered frame's trace/state bytes; a
   renderer-side inference or event/action lookup is not admissible.
3. Change labels and the existing result view only.
4. Run the UI and related V2 suites.

If either iteration fails to increase discriminative evidence, stop and perform
one redesign rather than layering patches. Two consecutive no-gain iterations
close the task as `needs_reframing`.

## Acceptance gate

All of the following are required:

1. From energy `0.0`, already at `site_a`, a new positive resource instance and
   stationary `forage` produce outcome `+1`, food gain `0.280`, and energy
   after `0.240`.
2. The corresponding negative resource outcome yields no food gain and records
   `harmful_or_unusable_resource`.
3. No-resource forage and non-forage resource events yield no food gain.
4. Identical commands derive identical instance IDs; different resource
   commands derive different IDs; one stored command settles only once.
5. The moved-only baseline fails the stationary positive case. The cue-only
   baseline fails the non-forage and negative-outcome controls.
6. The food-gain ablation reruns the same state and command and lowers energy
   after without changing the interaction outcome.
7. SQLite and two fresh processes recompute identical results from serialized
   state plus ordered commands.
8. Interaction, stored-trace, and initial-state tampering each fail closed.
9. The callable leakage scanner reports no resource-instance/post-outcome data
   in either policy projection and triggers on its injected positive control.
10. The UI distinguishes the selected attempt from the realized result and
   displays the resource instance, success/failure reason, food gain, passive
   decay, action cost, and net energy change. Every displayed settlement value
   must be read from a recovered frame's trace/state bytes; a renderer-only
   lookup keyed by event, action, seed, or label must fail the UI test.
11. A real explicit controller dispatch produces, stores, and recovers the same
    interaction ledger; no side path or forbidden capability is added.

## Stop condition

Stop and preserve the negative readback if any of these occurs:

- gain is possible from cue, action, movement, hidden label, or stored trace
  without a resolved positive resource interaction;
- the instance ID enters policy observation or scorer inputs;
- one command can settle more than once in the ordered log;
- replay does not recompute from serialized state plus commands;
- implementation requires controller, store, SQLite schema, world-state schema,
  route-control, status, program-state, validator, ITL, network, LLM, autostart,
  background behavior, or a second logic path change;
- an unlisted write or user-work collision appears;
- a threshold, seed rule, distribution, metric, or constant needs tuning after
  RED;
- destructive Git, push, tag, remote publication, credentials, or Phase B is
  required.

## Rollback plan

Before commit, rollback is a scoped reverse patch limited to task-owned files.
After commit, reversal requires a new additive commit. Never reset, clean,
stash, amend, rebase, delete historical artifacts, or rewrite existing SQLite
runs.

## Expected changed files

Only these paths may change:

- `docs/codex/tasks/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A.md`
- `docs/codex/tasks/ego-v2-p0-resource-interaction-outcome-repair-001a/COLLISION_RECORD.md`
- `labs/ego_life_playground_v0/microworld.py`
- `labs/ego_life_playground_v0/engine.py`
- `labs/ego_life_playground_v0/visual_console.py`
- `tests/test_ego_v2_p0_resource_interaction_outcome_repair_001a.py`
- `tests/test_ego_v2_p0_metabolism_viability_coupling_001a.py`
- `tests/test_ego_life_playground_v0.py`
- `tests/test_ego_life_playground_v2_microworld.py`
- `scripts/codex/verify_ego_v2_p0_resource_interaction_outcome_repair_001a.py`
- `scripts/tests/test_verify_ego_v2_p0_resource_interaction_outcome_repair_001a.py`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/result.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/trace.jsonl`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/baseline_comparison.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/ablation_report.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/leakage_report.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/replay_report.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/failure_manifest.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/progress_checkpoint.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/experiment_ledger.jsonl`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/stage_scorecard.json`
- `artifacts/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A/claim_ceiling.txt`

## Forbidden changes

All unlisted paths are forbidden. In particular: controller, store, terminal,
launcher, SQLite schema, world-state schema, prior artifacts/runs, ITL files,
route-control artifacts, `STATUS.md`, `PROGRAM_STATE*`, `state.json`, validators,
network, LLM, autostart, background dispatch, and any second behavior or replay
path.

## Commit and publication

One scoped local commit is permitted only after all acceptance checks succeed
and an independent review finds no blocking issue. Push, tag, and remote anchor
are forbidden.

## What this does not prove

This repair does not prove viability as a mechanism, learning, memory
causality, a dynamic causal boundary, initiative, agency, autonomy, emotion,
subjectivity, consciousness, electronic life, Joi-like existence, product
readiness, or stable user benefit.
