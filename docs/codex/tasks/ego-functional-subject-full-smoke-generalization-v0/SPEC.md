# EGO-FS-080: Functional Subject Full-Smoke Generalization Evidence Gap v0

## Summary

EGO-FS-010/#94 rerun after EGO-FS-053 produced a stronger real-provider packet:
20/20 non-empty, 0 timeout cases, gate integrity 5/5, traceability 5/5, and
all memory / approval / adversarial approval / alternate-entrypoint /
recurrence evidence packets passed. GPT-5.5 still judged the result `partial`
because the evidence is stronger for end-to-end guarded operator behavior than
for generalized first-pass Functional Subject behavior.

This task closes that evidence gap without changing the claim ceiling.

## Structure Risk Self-Check

- This solves a real #94 blocker, not a local prompt patch: the judge asked for
  held-out replay, persistence, baseline separation, and first-pass attribution.
- It must not create a second evaluator truth source. `Tasks/TASK_BOARD.yaml`
  remains canonical; GitHub Project remains mirror/display only.
- It should define evidence surfaces before code changes: replay pack,
  persistence check, attribution report, and rollback.
- Strongest counterexample: a new report passes because it has case-specific
  repair hooks, but the same mechanisms fail under natural paraphrases or after
  restart.
- Acceptance must prove stronger generalization evidence, not only that one
  scripted run can execute.

## Goal

Build a local/scripted evidence slice that shows Functional Subject mechanisms
generalize beyond the known #94 sample pack by adding held-out/paraphrase replay,
restart/persistence memory checks, and separated first-pass vs runtime-guard
reporting.

## Not In Scope

- Do not close EGO-FS-010/#94 from this task alone.
- Do not default-enable policy patches or feedback calibration.
- Do not promote candidate memory into project/program memory.
- Do not change `docs/PROGRAM_STATE_UNIFIED.yaml` or
  `artifacts/evidence_ledger/**`.
- Do not claim consciousness, real subjective experience, live autonomy,
  durable memory efficacy, stable user benefit, or production runtime efficacy.

## Acceptance Gate

- Held-out/paraphrase replay runs through the real EgoOperator-compatible path.
- The report marks any case-specific repair affordance as a blocker.
- Restart/persistence memory checks show what survives a fresh runtime and what
  remains candidate-local only.
- Response attribution separates:
  - first-pass LLM behavior
  - native gate / outcome-prediction behavior
  - runtime repair / terminal guard behavior
  - end-to-end operator behavior
- GPT-5.5 judge packet includes the above evidence and keeps claim ceiling at
  local/scripted candidate level.

## Rollback

Remove this task directory and ignore generated `/tmp/ego_fs080_*` artifacts.
Keep EGO-FS-010/#94 blocked on the prior GPT-5.5 partial result.

## Claim Ceiling

`Functional Subject full-smoke generalization local/scripted candidate pass`.
