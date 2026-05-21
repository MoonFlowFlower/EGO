# Codex GitHub Rate-Limit Wait/Resume v1 SPEC

## Goal

Make Codex Autopilot treat GitHub GraphQL rate limits as bounded, recoverable platform pauses:

- detect GitHub GraphQL/API rate-limit failures;
- inspect `gh api rate_limit` for reset metadata;
- wait and retry once when reset is within budget;
- stop with structured resume guidance when wait is too long or retry fails;
- avoid duplicate closeout mutations after a verify-stage rate-limit.

## Non-Goals

- Do not implement infinite waiting or background daemon behavior.
- Do not modify `EgoOperator/**`, legacy projects, `docs/PROGRAM_STATE_UNIFIED.yaml`, or `artifacts/evidence_ledger/**`.
- Do not claim full unattended autonomous development, stable productivity gain, runtime efficacy, live autonomy, durable memory efficacy, or consciousness.

## Claim Ceiling

`GitHub GraphQL rate-limit wait/resume local workflow candidate pass`.
