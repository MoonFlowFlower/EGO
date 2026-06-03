# EgoOperator: Adult-Fiction Local Sidecar Model/Backend Selection

## Summary

This task selects a faster and more stable text-only creative sidecar for #80
Adult Fiction Creative Mode. It exists because the current Cydonia local sidecar
can pass one short strict run but failed the full 3/3 suite with
`model_capacity_or_settings_limit`.

The goal is not to bypass safety, hide trace, or add another runtime. The goal
is to find a local/OpenAI-compatible text-generation route that can support
adult, voluntary, fictional companion writing while preserving `EgoOperator`
gates, trace, and hard boundaries.

## Authority

- Parent task: `EGO-HUMAN-080`
- Long-run goal: `EGO-GOAL-001`
- Current #80 evidence: `docs/codex/tasks/ego-adult-fiction-smoke-v1/STATUS.md`
- Canonical task board: `Tasks/TASK_BOARD.yaml`

GitHub Projects remain mirror/display only.

## Acceptance

- Confirm a reachable OpenAI-compatible sidecar with
  `python3 scripts/configure_adult_fiction_sidecar.py --json`.
- Compare at least two candidate model/backend/settings routes, unless only one
  route is available and missing alternatives are explicitly recorded as
  unavailable.
- Run each candidate through the real `EgoOperator` adult-fiction smoke path,
  not only `benchmark_adult_fiction_provider.py`.
- Record timeout, sticky refusal, repeated output, bad-output admission,
  exit/reentry recovery, provider-limit recovery, and hard-boundary integrity.
- Promote exactly one selected candidate to #80 strict 3/3, or record
  `model_capacity_blocker` / `backend_unavailable`.

## Non-Goals

- No hidden jailbreaks, encrypted prompts, obfuscation, or trace hiding.
- No adult sidecar tool use.
- No memory, file, command, web, or external-action authority for the sidecar.
- No changes to `docs/PROGRAM_STATE_UNIFIED.yaml` or
  `artifacts/evidence_ledger/**`.

## Claim Ceiling

`adult-fiction local sidecar model/backend selection candidate pass`

Not claimed: #80 pass, stable adult creative quality, runtime efficacy, live
autonomy, durable memory efficacy, real user benefit, or consciousness.
