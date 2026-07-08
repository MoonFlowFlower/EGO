# P2 SESSION SCRIPT — egodesktop-pet-world-integration-001a freeze-B

Status: FROZEN_PRE_RUN / SCRIPT_ONLY.

Purpose: freeze the visible operator-session script before any P0 scored run so
the live-session evidence cannot be tuned after offline results. This is not a
runtime trace and not a pass result.

## Session constants

- Uses `world_config_v0.json`.
- Episode length for this scripted session: ticks `0..520`.
- Drift boundaries crossed by the session: tick `200` and tick `400`.
- Initial ablation state: `ablation_enabled=false`,
  `learner_updates_enabled=true`.
- `ablation_toggle` semantics:
  - `ablation_enabled=true` freezes learner model updates while policy
    execution continues.
  - `ablation_enabled=false` resumes learner model updates.
- All events below are admitted through the tick-quantized product input path
  and must appear in kernel trace.

## Ordered input events

| tick | event | payload | purpose |
|---:|---|---|---|
| 5 | `pet` | `{"intensity":"gentle"}` | early comfort interaction before any drift |
| 25 | `feed` | `{"portion":"small"}` | early energy interaction before any drift |
| 170 | `pet` | `{"intensity":"gentle"}` | pre-boundary interaction, still regime R0 |
| 190 | `feed` | `{"portion":"small"}` | pre-boundary energy support |
| 215 | `ablation_toggle` | `{"ablation_enabled":true,"learner_updates_enabled":false}` | OFF→ON after crossing drift boundary tick 200 |
| 245 | `pet` | `{"intensity":"gentle"}` | input while updates are frozen |
| 285 | `ablation_toggle` | `{"ablation_enabled":false,"learner_updates_enabled":true}` | ON→OFF within post-shift A window family |
| 330 | `feed` | `{"portion":"small"}` | non-ablation care event after updates resume |
| 390 | `pet` | `{"intensity":"gentle"}` | pre-boundary interaction before drift boundary tick 400 |
| 415 | `ablation_toggle` | `{"ablation_enabled":true,"learner_updates_enabled":false}` | OFF→ON after crossing drift boundary tick 400 |
| 455 | `feed` | `{"portion":"small"}` | input while updates are frozen in post-shift B |
| 485 | `ablation_toggle` | `{"ablation_enabled":false,"learner_updates_enabled":true}` | ON→OFF within post-shift B window family |
| 510 | `pet` | `{"intensity":"gentle"}` | final visible interaction after updates resume |

## Expected non-input schedule crossings

- Tick `200`: world switches from `R0_pre_shift` to `R1_shift_a`.
- Tick `400`: world switches from `R1_shift_a` to `R2_shift_b`.

These crossings are world schedule events, not user inputs. They still must be
reflected in trace state frames so replay can recover the same regime sequence
without the viewer.

## Acceptance reminder

The future P2 run must preserve the raw live-session trace verbatim. If the
future implementation cannot replay this script bit-exactly from serialized
state plus observation, the live-session evidence is invalid.
