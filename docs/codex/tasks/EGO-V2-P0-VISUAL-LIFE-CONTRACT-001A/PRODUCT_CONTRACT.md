# EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A — product contract

This is a pre-code product contract for one local, explicit, default-off path.
It fixes implementation inputs; it is not science evidence or a claim that the
mechanism works.

## 1. Product boundary

- Layer: Layer 2 engineering plus a bounded Layer 3 mechanism hypothesis.
- Lane: product/capability.
- Mainline target: the existing `scripts/run_ego_life_playground_v0.py` path.
- Enabled state: product axis `enabled=true`, `default_enabled=false`; no
  autostart, background dispatch, network, or LLM.
- Real-trigger requirement: Step/Run must traverse
  `PlaygroundController.dispatch -> compute_step -> SQLite commit/recovery`.
- Claim ceiling: local product integration and replay hygiene only.
- Auto-Remote-Anchor: `forbidden`.

## 2. Observation and action boundary

The policy's only exteroception is a `5 x 5` egocentric array. The body occupies
array cell `[2,2]`; its facing direction maps toward row `1`. Tokens are exactly:

```text
self empty wall occluded v0 v1 v2 v3 v4
```

For every target cell, an integer-grid ray is traced from `[2,2]`. The first
opaque wall or object is visible; cells beyond the first opaque cell on that ray
are `occluded`. Out-of-map and blocked topology cells are `wall`. The result is a
pure function of serialized world state and pose.

The policy receives no semantic event, absolute coordinate, place name, object
ID, map dimensions/topology, path, legal-action mask, trial seed, life ID,
command sequence, or token-to-cause mapping. It may receive serialized
interoception (`energy/safety/connection/stimulation`), current internal goal,
model, and memory. Policy memory projections contain content/aggregate values
only; source episode/life IDs, command hashes, and other lineage identifiers
remain trace-only.

Actions are exactly:

```text
turn_left turn_right move_forward interact rest
```

All five are always selectable. Turns rotate by 90 degrees. `move_forward`
moves at most one cell and returns a typed blocked outcome for a wall or object.
`interact` affects only the immediately forward object and otherwise returns a
typed no-object outcome. `rest` changes no world position. No action teleports,
calls a path planner, or directly selects a semantic stimulus.

## 3. World and deterministic sampling

One trial contains one instance of each hidden stimulus cause:

```text
resource social novelty threat shelter
```

A SHA-256 ordering derived from the trial world seed produces a bijection from
`v0..v4` to those causes. The mapping and topology stay unchanged for all four
lives and are absent from policy inputs.

Birth and object placement use a counter-hash sampler, not a mutable PRNG:

```text
sha256({trial_seed, namespace, life_index, entity_id, spawn_count, candidate})
```

Candidate cells are sorted walkable cells not already occupied; the smallest
digest selects the cell. Initial placement uses `spawn_count=0`. Interacting
with an object increments only that object's current-life spawn count and
resamples it from currently free cells. A new life resets all object spawn
counts to zero and resamples body/object positions using the new life index.
Policy calls and UI timing therefore cannot advance placement state.

An optional operator event may identify one cause and relocate its object before
observation using an independent injection counter and the same counter-hash
rule. The command and observer trace may name that event; the policy sees only
the resulting visual token.

## 4. Fixed body dynamics

Initial body state for every life:

```json
{"energy":0.45,"safety":0.62,"connection":0.50,"stimulation":0.43}
```

Every action tick applies passive energy decay `0.010` plus an action cost:

```json
{"turn_left":0.004,"turn_right":0.004,"move_forward":0.012,"interact":0.008,"rest":0.002}
```

Only a successful forward interaction adds the following cause delta; all
values are clamped to `[0,1]` after combining the tick effects:

```json
{
  "resource":{"energy":0.280,"safety":0.000,"connection":0.000,"stimulation":0.000},
  "social":{"energy":0.000,"safety":0.000,"connection":0.160,"stimulation":0.020},
  "novelty":{"energy":0.000,"safety":-0.020,"connection":0.000,"stimulation":0.160},
  "threat":{"energy":0.000,"safety":-0.180,"connection":0.000,"stimulation":0.040},
  "shelter":{"energy":0.000,"safety":0.120,"connection":0.000,"stimulation":0.000}
}
```

`rest` additionally adds `safety +0.020`. These values are fixed before the
implementation run and must not be tuned from observed survival outcomes.

## 5. Goal contract

- A bodily target remains active until its value reaches `0.72`.
- Completion latches that variable out of ordinary candidacy.
- A latched variable becomes an ordinary candidate again only after its value
  falls below `0.60`.
- A value at or below `0.15` is a severe deficit and may override the current
  target. Energy at or below `0.15` wins ties and takes priority.
- If no bodily variable is eligible, the goal status is `explore`.
- Explore scores use only serialized counts of visual observation/action/next-
  observation transitions. No fixed target rotation or semantic event name may
  contribute.
- Trace records goal before/after, per-variable deficit/latch state,
  completion, transition kind, and override reason.

## 6. Four-life lifecycle

A trial has exactly four lives. One `episode` equals one life. Each life has at
most `256` policy-action ticks.

- If post-metabolism `energy_after == 0`, the current action tick is terminal.
  Its model/memory update is still applied; no next policy action is selected.
- The next command calls the same `compute_step` and produces a pure respawn
  transition. It does not invoke policy scoring or apply action metabolism.
- If a living life reaches action tick `256`, it is right-censored and the next
  command is likewise a pure respawn transition.
- Death in life 4 or censoring at life-4 tick 256 ends the trial. Further
  dispatch is rejected.
- Fourth-life output is `min(survival_ticks,256)` plus `censored`.

Across respawn, byte equality is required for:

```text
model
memory.episodic
memory.consolidated
memory.claim_events
memory.competing_claims
```

The trial token-to-cause mapping, command chain, and trace chain also persist.
The following reset: organism, pose, object positions, current-life object spawn
counts, current goal and goal latches, last action, life tick, and working
spatial state. Each carry/reset component has before/after hashes in the respawn
trace.

## 7. Observer/UI split

The observer frame may render the complete semantic world recovered from
serialized state and may show lifecycle receipts. A separate panel renders the
exact 5x5 policy visual array. Observer data is renderer-only: it is not a
policy input, replay authority, baseline shortcut, or fresh side lookup.

## 8. Versions and compatibility

Implementation version strings are:

```text
state                    ego.life_playground.state.v3
run                      ego.life_playground.run.v3
command                  ego.life_playground.command.v5
trace                    ego.life_playground.trace.v7
world                    ego.life_playground.microworld.state.v4
policy observation       ego.life_playground.microworld.observation.v4
observer frame           ego.life_playground.microworld.public_frame.v5
claim memory             ego.life_playground.claim_memory.v2
code-path manifest       ego.life_playground.code_path.v4
```

The SQLite table shape does not change. Old stored runs fail closed through
schema/code-path mismatch. No old database or artifact is deleted or rewritten.

## 9. Evidence and stop rules

Callable product checks must record producer function, input artifacts, run ID,
seed/context/life IDs, aggregation rule, and code-path hash. Leakage scanning
requires a real scanner plus a positive control. Replay recomputes actions from
serialized initial state and commands; stored actions/traces are comparison-only.

Stop or downgrade on policy leakage, a second reducer/policy/store/replay path,
non-recomputed respawn, carry/reset mismatch, unused test schedules, baseline
access advantage, or equal-access lookup/count-Q/graph/planner equivalence.

This contract does not prove electronic life, subjectivity, consciousness,
emotion, agency, autonomy, general learning, mechanism validity, or stable user
benefit.
