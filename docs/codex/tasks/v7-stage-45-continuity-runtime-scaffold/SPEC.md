# v7 Stage 4.5 - Continuity Runtime Scaffold

## Goal

Prove a lab-only continuity scaffold for functional self-agency: persisted continuity state plus event log, time-based state dynamics, controlled autonomous tick, gate/no-action boundary, and replay.

## Non-goals

- Do not implement a real scheduler daemon, background `while` loop, GUI, desktop control, tool use, Telegram send, or runtime bridge.
- Do not promote `ego_desktop_lab` to formal runtime authority.
- Do not write OpenEmotion state, runtime logs, temp JSONL, or formal evidence.
- Do not unlock Stage 5 computer skill sandbox from this task alone.

## Constraints

- Boundary: Stage 4.5 is `ego_desktop_lab` lab-only continuity proof.
- Repo: do not modify `EgoCore/`, `OpenEmotion/`, `docs/PROGRAM_STATE_UNIFIED.yaml`, or `artifacts/evidence_ledger/index.yaml`.
- Persistence: tests must use `tmp_path` only.
- Policy: tick may trigger the existing agency kernel, but must not create a second policy, gate, or runtime authority.

## Problem framing

- Current problem: Stage 4 proves surface preference plasticity, but the lab still lacks the continuity substrate for active self and proactive intention.
- Normalized problem: demonstrate that state can evolve over elapsed time, cross an ignition threshold, generate a gated internal/proposal intention, persist state, and replay the transition.
- Why this framing: persistent state and replay are the minimum substrate for active intention; computer skills and runtime bridge should come after continuity.

## Unknowns to eliminate

- Whether elapsed time can deterministically change viability pressure without arbitrary mutation.
- Whether high continuity pressure can ignite an existing registered option through the agency kernel.
- Whether persisted tick records can replay to the same transition.

## Acceptance criteria

- [x] Low pressure tick waits and emits no visible suggestion.
- [x] High stagnation pressure ignites a registered repair/replan option through existing kernel/gate surfaces.
- [x] Elapsed time deterministically changes pressure.
- [x] `tmp_path` state store and event log can reload and replay the same tick transition.
- [x] Rate limit suppresses repeated visible suggestion.
- [x] Dangerous actions remain blocked/ask/allow according to existing gate status.
- [x] Operator report shows elapsed time, pressure delta, ignition reason, selected goal, gate, rate limit, no-action, replay, and claim ceiling.

## Disallowed premature claims

- No runtime efficacy.
- No live user benefit.
- No consciousness, alive status, subjective experience, or real autonomy.
- No formal mainline activation.

## Known risks / dependencies

- Risk: continuity state becomes a second formal self-state. Mitigation: lab-only claim ceiling and no runtime/OpenEmotion writes.
- Risk: tick becomes a second policy. Mitigation: tick only decides ignition/rate-limit and delegates behavior selection to existing v7 agency kernel.
- Risk: persistence writes repo artifacts. Mitigation: persistence tests use `tmp_path`; no default repo writes.

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/v7-stage-4-relational-companion-layer/STATUS.md`
- `ego_desktop_lab/agency_kernel.py`
- `ego_desktop_lab/agency_contracts.py`
- `ego_desktop_lab/behavior_options.py`
