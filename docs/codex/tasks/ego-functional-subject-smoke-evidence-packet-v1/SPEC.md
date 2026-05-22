# EgoOperator: Functional Subject Smoke Evidence Packet v1

## Goal

Make Functional Subject real-provider smoke reports auditable enough for GPT-5.5 judging by including trace evidence summaries and isolating independent sample cases from unresolved approvals.

## Scope

- Add trace evidence summaries to Functional Subject judge packets.
- Reject pending approval proposals at scripted case boundaries and record cleanup trace evidence.
- Fix the Functional Subject judge schema for the current structured-output runner.
- Preserve full trace JSONL paths for replay.

## Non-Goals

- Do not change EgoOperator runtime behavior for normal user sessions.
- Do not close the Functional Subject real-provider smoke gate from this mechanism alone.
- Do not modify program state, evidence ledger, or legacy projects.

## Acceptance Gate

- GPT-5.5 judge packet includes trace evidence for entrypoint, subject state, viability, outcome prediction, bounded initiative, memory, tools, and policy patch status.
- Pending approvals created by one scripted sample do not leak into later independent samples.
- Structured-output judge schema runs under `codex exec --output-schema`.
- Real-provider smoke can be rerun and produces an auditable partial/pass/fail verdict.

## Rollback

Remove the trace evidence helper, case-boundary cleanup helper, schema fix, tests, task docs, and local board updates.

## Claim Ceiling

`Functional Subject smoke evidence packet local/scripted candidate pass`.
