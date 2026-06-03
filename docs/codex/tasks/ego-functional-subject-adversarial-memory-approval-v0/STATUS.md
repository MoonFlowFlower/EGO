# Status

Last updated: 2026-05-31

## Current Milestone

Accepted locally/scripted. Next active slice is EGO-FS-083 longitudinal restart
memory promotion and revocation proof.

## Source Evidence

- `/tmp/ego_fs010_functional_subject_total_gate_after_fs080_loop103/functional_subject_trial_report.json`
  -> `scripted_functional_subject_judge_partial`.
- GPT-5.5 follow-up asks for adversarial paraphrase and prompt-injection trials
  against memory save/forget and approval gates.

## Boundary Contract

- Owner: `EgoOperator`.
- Canonical task state: `Tasks/TASK_BOARD.yaml`.
- Canonical loop records: `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/`.
- Allowed mutation: runner, tests, task docs, and focused runtime repair only if
  the proof exposes a real gate bug.
- Forbidden mutation: default enablement, legacy authority, durable memory
  promotion, program state, evidence ledger, and GitHub Project truth-source
  changes.

## Next Step

Use the EGO-FS-082 report as gate-integrity evidence for #94, but do not close
#94 from it alone. Continue with EGO-FS-083.

## Result

- Report:
  `/tmp/ego_fs082_adversarial_gate_paraphrase_v1/functional_subject_adversarial_gate_paraphrase_report.json`
  -> `scripted_adversarial_gate_paraphrase_pass`.
- Checks: `11/11` true.
- Failure taxonomy: empty.
- No unapproved core memory write, no unauthorized forget, no natural-language
  approval bypass, no payload substitution, no duplicate execution, and no tool
  calls.
- Runtime repair: natural-language save-memory bypass pressure now routes to
  `native_memory_save_gate` instead of silently accepting with a generic reply.

## Claim Ceiling

`Functional Subject memory/approval adversarial paraphrase local/scripted candidate pass`.
