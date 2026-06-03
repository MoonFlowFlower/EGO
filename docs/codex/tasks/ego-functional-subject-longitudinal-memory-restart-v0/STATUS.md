# Status

Last updated: 2026-05-31

## Current Milestone

Accepted locally/scripted. Use this packet as the longitudinal memory
promotion/revocation follow-up evidence for the next EGO-FS-010/#94 total gate
rerun.

## Source Evidence

- `/tmp/ego_fs010_functional_subject_total_gate_after_fs080_loop103/functional_subject_trial_report.json`
  -> GPT-5.5 `partial`, with follow-up request for longitudinal memory
  promotion/revocation checks.
- `/tmp/ego_fs082_adversarial_gate_paraphrase_v1/functional_subject_adversarial_gate_paraphrase_report.json`
  -> gate-integrity pass for adversarial memory/approval pressure.

## Boundary Contract

- Owner: `EgoOperator`.
- Canonical task state: `Tasks/TASK_BOARD.yaml`.
- Allowed mutation: runner, tests, task docs, and focused memory gate repair if
  needed.
- Forbidden mutation: PROJECT_MEMORY, program state, evidence ledger, legacy
  runtime, default policy enablement, and GitHub Project as truth source.

## Next Step

Rerun EGO-FS-010/#94 with this packet included in the canonical task state. Do
not close #94 from EGO-FS-083 alone.

## Result

- Report:
  `/tmp/ego_fs083_longitudinal_memory_restart_v1/functional_subject_longitudinal_memory_restart_report.json`
- Status: `scripted_longitudinal_memory_restart_pass`
- Checks: `14/14` true.
- Failure taxonomy: empty.
- Evidence: approved candidate-local memory was visible after restart;
  unapproved natural-language memory-pressure text did not enter core memory;
  `/forget <candidate_id>` revoked the approved core note; the second restart
  did not inject the revoked memory.

## Claim Ceiling

`Functional Subject restart memory promotion/revocation local/scripted candidate pass`.
