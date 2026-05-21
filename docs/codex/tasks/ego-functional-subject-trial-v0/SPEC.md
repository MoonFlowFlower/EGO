# EgoSubject: 20-Sample Functional Subject Trial + GPT-5.5 Judge

## Goal

Create the first 20-sample Chinese scripted trial for the Functional Subject roadmap, with a GPT-5.5 judge packet that evaluates operational mechanisms rather than persona style.

## Scope

- Add a 20-case Chinese sample pack covering continuity, preference change, claim pressure, bounded initiative, emotional support, tool failure, memory correction, forget/save, and repeated-failure learning.
- Extend the existing `scripts/run_ego_experience_trial.py` runner with `--functional-subject-trial`.
- Emit transcript/report files plus a GPT-5.5 judge packet.
- Represent baseline-vs-candidate expectations in each case.

## Non-Goals

- Do not run or require a real provider key in local tests.
- Do not implement SubjectState, ViabilityState, OutcomePredictor, PolicyPatchCandidate, or runtime behavior changes.
- Do not close human-required smoke tasks.
- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml` or `artifacts/evidence_ledger/**`.

## Acceptance Gate

- Trial pack has exactly 20 cases.
- Cases cover all required Functional Subject categories from `Tasks/与GPTpro的讨论结果.txt`.
- Runner produces `functional_subject_trial_report.json` and Markdown via the CLI-compatible entrypoint.
- Judge packet includes baseline failure modes, candidate success signals, dimensions, and claim ceiling.
- Local deterministic tests pass.

## Rollback

Remove the trial pack, runner branch, judge schema, tests, and local board status changes for `EGO-FS-002`.

## Claim Ceiling

`Functional Subject scripted trial local candidate pass`.
