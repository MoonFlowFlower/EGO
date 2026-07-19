# EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A

Status: `READY_FOR_TEST_FIRST_EXECUTION`

Auto-Remote-Anchor: `forbidden`

## Problem definition and real objective

Repair the existing explicit, default-off V2 product path so every executed
simulation tick pays an energy cost, only an environment-produced food outcome
can replenish energy, and critical energy changes the real action surface. The
repair must stay inside the existing controller -> reducer -> SQLite
recomputation chain.

This task does not test whether a functional electronic-life mechanism exists.
It removes a product defect that would otherwise make a later viability test
invalid.

## Live pins and authority readback

- Ego worktree at task start: branch `main`, HEAD
  `2b85c36925685a545c01811014aab78bb07d3efe`, clean, ahead 24 / behind 0.
- ITL worktree at task start: branch `codex/meta-theory-scaffold`, HEAD
  `0bdc05ff5d2e6001beb35d66ccc1485de300ac90`, clean, ahead 21 / behind 0.
- Product route readback:
  `artifacts/ROUTE-STATE-MACHINE-001A/routes/EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A/state.json`
  permits `develop_v2_in_ego_with_local_bounded_task_card`.
- Ego product-axis mirror has an exact matching pinned payload; the explicit
  entrypoint is `scripts/run_ego_life_playground_v0.py` and remains default-off.
- This task changes no route, status, program-state, validator, or product-axis
  authority field.

Any pin drift, dirty-path collision, or cross-repo authority conflict before
the first source edit is a stop.

## Current layer, mainline, enabled state, and trigger

- Current layer: Layer 2, product engineering implementation and replay hygiene.
- Mainline target: the existing V2 product chain only:
  `PlaygroundController.dispatch -> engine.compute_step ->
  SQLiteEventStore.append_step -> SQLiteEventStore.recover_run`.
- Mainline integration: already connected to the explicit local V2 product
  entrypoint; no new entrypoint is allowed.
- Enabled-state requirement: explicit Step/Run only; `default_enabled=false`,
  no autostart or background tick.
- Real-trigger requirement: focused acceptance must execute a real controller
  dispatch and persist/recover at least one tick through SQLite.
- Claim ceiling: product engineering repair under the named distributions only.

## Bounded audit

### Hypothesis

Replacing heuristic energy gains with one post-outcome metabolism ledger, and
using its resulting energy in the existing selector gate, is sufficient to
make energy conservation and the critical-energy consequence replayable without
adding another controller, reducer, store, or replay path.

### Strongest baseline explanation

A fixed deficit scorer plus a fixed action-cost table and a hard-coded
critical-energy gate can reproduce the visible behavior. That explanation is
accepted for this phase. Passing this card cannot count as learning, viability
mechanism, autonomy, or electronic-life evidence.

### Strongest reason the framing may be invalid

If food gain can be inferred from a cue or chosen action without a realized
world transition, or if the critical consequence exists only in a UI/test
helper, the repair is cosmetic and the framing fails.

### Falsifier and still-insufficient evidence

- Falsifier: any tick gains energy without the environment transition reporting
  a moved positive forage outcome, or recovered replay differs from fresh
  recomputation.
- Still insufficient: monotonic decay, survival-looking behavior, clean replay,
  or a changed action at low energy. These establish only the bounded repair.
- This task tests engineering coupling, not a mechanism hypothesis.

### Anti-hardcoding and leakage checks

- No event, seed, sequence, fixture, filename, or expected-action exception.
- No use of hidden regime, oracle read, future observation, or stored trace as
  a policy/replay input.
- No parallel metabolism selector or UI-only viability state.
- No schema split: live and replay call the same `compute_step` bytes.
- No old artifact is rewritten and no result threshold may be changed after RED.

## Task-local constants and equations fixed before RED

The following values are fixed for this task before executing the failing tests:

```text
passive_decay_per_tick = 0.020
food_energy_gain = 0.280
critical_energy_threshold = 0.150
critical_allowed_actions = [forage, rest, withdraw]

action_cost = existing ACTION_COSTS[selected_action]
energy_after = clamp01(
    energy_before - passive_decay_per_tick - action_cost + food_gain
)
actual_delta.energy = energy_after - energy_before
```

`food_gain = 0.280` if and only if the environment-produced transition reports
all of the following:

```text
selected_action == forage
moved == true
visited_site == site_a
outcome == 1.0
food_obtained == true
```

Otherwise `food_gain = 0.0`. A cue, an intended forage action, a zero-distance
repeat, or a positive non-forage site outcome is insufficient.

At decision time, if `energy_before <= 0.150`, the selector's real legal action
set is the intersection of topology-legal actions and
`[forage, rest, withdraw]`. This is the required downstream capability
restriction. Episode termination is intentionally out of scope for this
minimal repair.

## Collision result

The paired collision record is:

`docs/codex/tasks/ego-v2-p0-metabolism-viability-coupling-001a/COLLISION_RECORD.md`

Selected approach: add environment-owned `food_obtained` to the existing world
transition record, compute one metabolism ledger inside `compute_step`, and
apply one low-energy intersection gate before the existing argmax. Rejected
approaches include cue/action reward and a separate viability controller.

## Baseline and ablation requirements

- Independent callable baseline: the pre-repair heuristic energy equation,
  used only by the verifier to demonstrate that a quiet/rest or resource/forage
  choice could replenish energy without realized food.
- Real ablation: rerun the same ordered scenario through `compute_step` in an
  isolated fresh process with the task-local food gain set to zero. This may
  only be an evidence-time in-memory intervention; it must not add a command,
  controller, reducer, or persistent product switch.
- Baseline and ablation do not participate in acceptance as mechanism evidence;
  they document the repair boundary.

## Trace and replay requirement

Every new trace must include values recomputed by `compute_step`:

```text
energy_before
passive_decay
action_cost
food_gain
energy_after
downstream_effect
viability_gate
metabolism.producer_function
metabolism.input_artifacts
metabolism.run_id
metabolism.seed
metabolism.episode_id
metabolism.aggregation_rule
metabolism.code_path_hash
```

`downstream_effect` must distinguish threshold entry from an action restriction
that is active on the current tick. SQLite recovery must begin from serialized
initial state and ordered stored commands, call `compute_step`, and compare the
stored trace only after recomputation. Tampering with the stored trace or
initial state must fail closed.

## Computed-evidence provenance gate

All emitted result, baseline, ablation, replay, and progress fields must come
from callable producer functions. Each evidence record must identify input
artifacts, run ID, seed/episode/context IDs where applicable, aggregation rule,
and code-path hash. No literal pass verdict or test that only asserts `pass` is
admissible.

## Test-first sequence

1. Add focused tests without changing product code.
2. Run them and preserve the expected RED readback and source code-path hash.
3. Make the smallest source change that satisfies the fixed equations.
4. Run focused tests, existing V0/V2 suites, verifier tests, the callable
   verifier, fresh-process x2, and route/convergence guards that cover the
   touched chain.

## Acceptance gate

All of the following are required:

1. Continuous no-food Step ticks have strictly monotonically decreasing energy.
2. Forage without an environment `food_obtained=true` transition has zero food
   gain and cannot increase energy.
3. A moved positive forage outcome produces exactly `0.280` food gain and the
   ledger reconciles to `energy_after`.
4. Repeated no-food ticks cross `0.150`; a subsequent real selector call removes
   `approach` and `explore` from eligibility while preserving the predeclared
   critical subset.
5. Trace contains the exact ledger and downstream-effect fields above.
6. SQLite recovery and two fresh processes reproduce final state, selected
   actions, ledger fields, and trace hashes from serialized state plus ordered
   commands.
7. Stored-trace and initial-state tamper cases fail closed.
8. A real explicit controller dispatch commits and recovers the same ledger.
9. No second controller/reducer/store/replay path, timer, autostart, network,
   LLM, or route change is present.

## Stop condition

Stop and preserve the negative readback if any of these occurs:

- positive food gain without the full environment outcome predicate;
- critical restriction exists outside `compute_step` or differs in replay;
- stored action/reward/viability fields become replay inputs;
- focused implementation needs controller, terminal, UI, store, SQLite schema,
  route, status, program-state, or validator changes;
- an unlisted write appears or user work collides with the task;
- a metric, threshold, event distribution, or constant needs post-result tuning;
- destructive Git, push, tag, network, LLM, background scheduling, or credentials
  are required.

## Rollback plan

Before commit, rollback is a scoped reverse patch limited to task-owned files;
failed tests/readbacks may be retained as named negative evidence only when they
do not overwrite historical artifacts. After commit, reversal requires a new
additive commit. Never reset, clean, stash, amend, rebase, or rewrite history.

## Expected changed files

Only these paths may change:

- `docs/codex/tasks/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A.md`
- `docs/codex/tasks/ego-v2-p0-metabolism-viability-coupling-001a/COLLISION_RECORD.md`
- `labs/ego_life_playground_v0/engine.py`
- `labs/ego_life_playground_v0/microworld.py`
- `tests/test_ego_v2_p0_metabolism_viability_coupling_001a.py`
- `tests/test_ego_life_playground_v0.py`
- `tests/test_ego_life_playground_v2_microworld.py`
- `scripts/codex/verify_ego_v2_p0_metabolism_viability_coupling_001a.py`
- `scripts/tests/test_verify_ego_v2_p0_metabolism_viability_coupling_001a.py`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/result.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/trace.jsonl`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/baseline_comparison.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/ablation_report.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/replay_report.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/failure_manifest.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/progress_checkpoint.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/experiment_ledger.jsonl`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/stage_scorecard.json`
- `artifacts/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A/claim_ceiling.txt`

## Forbidden changes

All unlisted paths are forbidden, especially controller/store/terminal/UI,
SQLite schema, launcher, old artifacts, route-state artifacts, `STATUS.md`,
`PROGRAM_STATE*`, `state.json`, validators, network/LLM/autostart/background
behavior, and any second logic path.

### Scope amendment 1 — regression-contract readback

The first complete V0/V2 regression run after the focused GREEN result produced
three failures in the two pre-existing test files now listed above. No source,
constant, threshold, metric, distribution, or acceptance rule is changed by
this amendment:

- the old goal-completion fixture depended on heuristic resource/forage energy
  gain under a negative realized site outcome;
- the paired-history fixture expected the negative-outcome run to make the same
  second choice as the positive-outcome run despite the newly real energy loss;
- the visual lockstep fixture reused the same event and therefore produced a
  legitimate zero-distance second action with no animation.

The two test files may change only to bind those assertions to the predeclared
real-outcome energy rule and a moving visual event. Weakening replay, tamper,
lockstep, memory-isolation, or no-fake-gain assertions remains forbidden.

## Commit and publication

One scoped local commit is permitted only after all acceptance checks succeed
and the changed-path set is exact. Push, tag, and remote anchor are forbidden.

## What this does not prove

This repair does not prove viability as a mechanism, learning, memory
causality, dynamic causal boundary, initiative, agency, autonomy, emotion,
subjectivity, consciousness, electronic life, Joi-like existence, product
readiness, or stable user benefit.
