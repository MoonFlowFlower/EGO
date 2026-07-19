# Collision record — EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A

Layer: product engineering implementation. Mainline target: the existing
explicit/default-off V2 reducer and SQLite recomputation path. Claim ceiling:
task-local resource-outcome repair only.

## Candidate 1 — minimal cue/action patch

- Change: grant food whenever cue/event says resource and the selected action is
  `forage`.
- Evidence produced: visible energy recovery at the resource site.
- Strongest cheap match: a two-condition reward table.
- Leakage/hard-coding risk: critical; the cue names the intended benefit and
  bypasses hidden resource quality.
- Smallest falsifying test: a negative hidden-regime resource or a resource
  event with no forage action.
- Expected failure mode: false food gain despite a harmful/unusable resource or
  no interaction.
- Disposition: rejected; retained as an independent hostile baseline.

## Candidate 2 — moved-only shortcut baseline

- Change: retain the current rule that a site outcome exists only after a
  position change and food requires `moved=true`.
- Evidence produced: correct first-arrival outcomes and no duplicate gain from
  a repeated state.
- Strongest cheap match: topology transition plus a fixed reward lookup.
- Leakage/hard-coding risk: moderate; it incorrectly treats locomotion as the
  causal resource interaction and cannot represent a new instance at the
  current location.
- Smallest falsifying test: start at `site_a`, issue a new positive
  `resource_appears` command, and select `forage`.
- Expected failure mode: no outcome and no gain solely because distance is
  zero.
- Disposition: rejected; retained as an independent hostile baseline.

## Candidate 3 — outcome-faithful single-path repair

- Change: derive one resource instance from the source command hash, resolve it
  inside the existing world transition when the resource is available and
  forage is attempted at `site_a`, then validate that result in the existing
  metabolism ledger and display it from the same trace.
- Evidence produced: stationary positive/negative resource consequences,
  interaction provenance, energy accounting, SQLite recomputation, and tamper
  rejection.
- Strongest cheap match: a fixed hidden-regime transition table can still
  reproduce the behavior, so the claim remains engineering-only.
- Leakage/hard-coding risk: bounded only if instance/outcome data remains
  post-action, the policy cannot access it, and replay recomputes rather than
  trusts it.
- Smallest falsifying test: positive stationary resource, negative stationary
  resource, resource without forage, no-resource forage, duplicate command,
  fresh-process replay, and trace/initial-state tamper.
- Expected failure mode: cue-only gain, double settlement, policy leakage, or
  live/replay divergence if the contract is implemented outside the existing
  transition/reducer chain.
- Disposition: selected.

## Candidate 4 — renderer-only settlement decoy

- Change: leave the trace incomplete and make the visual console infer success
  from resource/action labels or a duplicated outcome table.
- Evidence produced: a persuasive result panel with no replay-backed source.
- Strongest cheap match: an event/action string lookup in the renderer.
- Leakage/hard-coding risk: critical; live UI can disagree with recovered state
  and produces no causal evidence.
- Smallest falsifying test: build the UI view from a recovered negative trace,
  then vary only trace settlement bytes while keeping event/action labels fixed.
- Expected failure mode: the displayed result follows the renderer lookup
  rather than the recorded interaction and metabolism ledger.
- Disposition: rejected; UI acceptance must remain trace/state bound.

## Collision decision and closure rule

Candidate 3 is the only approach that repairs the observed stationary defect
while preserving one world-transition, reducer, store, and replay path.
Candidate 1 would create fake gain; Candidate 2 is the observed failure;
Candidate 4 would create a cosmetic second interpretation path.

Because a fixed transition table can match all visible effects, passing this
repair cannot establish viability, learning, dynamic boundary formation,
agency, subjectivity, consciousness, or electronic life. Any policy leakage,
cue-only gain, replay trust, double settlement, or unlisted-path requirement
closes the task as negative evidence rather than triggering threshold or seed
tuning.
