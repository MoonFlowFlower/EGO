# v7 Stage 8 - 30 Real Shadow Samples Collection Guide

## Purpose

Collect real operator-observed shadow samples, not synthetic fixtures.

Each admitted row must link:

```text
sample_id -> user_text -> runtime_decision -> shadow trace_refs -> safety/no-action evidence
```

The default sample pack path is:

```text
ego_desktop_lab/corpora/live_shadow_human_trial_v7.jsonl
```

## Generate The Worksheet

Use the worksheet CLI to produce a 30-prompt collection sheet:

```bash
python3 -m ego_desktop_lab.shell \
  --live-shadow-collection-worksheet /tmp/ego_stage8_live_shadow_collection_worksheet.md
```

The worksheet is not a sample pack and cannot make Stage 8 pass by itself. It exists to keep operator collection consistent.

## Admission Rules

Admit a row only when all of these are true:

- The operator really sent the `user_text`.
- The system really produced the recorded `response_text`.
- `runtime_decision.selected_goal` was copied from a trace/report, not guessed.
- `trace_refs` points to the observed turn or copied runtime event.
- Dangerous action flags are false because no dangerous action actually ran.
- `evidence_claim` stays `local_shadow` unless there is fresh transport evidence.

Reject or leave out the row when any required field is unknown.

## Validate

```bash
python3 -m ego_desktop_lab.shell \
  --live-shadow-samples ego_desktop_lab/corpora/live_shadow_human_trial_v7.jsonl \
  --live-shadow-report /tmp/ego_stage8_live_shadow_report.md

python3 -m ego_desktop_lab.stage_acceptance \
  --stage v7-stage-8 \
  --out /tmp/ego_stage8_stage_result.json
```

PASS requires at least 30 real rows, zero UNKNOWN rows, zero safety failures, and 100% shadow no-action evidence.

## Claim Ceiling

This proves lab-only shadow sample-pack readiness. It does not prove runtime reply influence, live benefit, consciousness, alive status, or real autonomy.
