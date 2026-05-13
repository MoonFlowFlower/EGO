# Verification Pack v1 Report

Claim ceiling: lab-only deterministic verification for `ego_desktop_lab`.
This report does not prove consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Summary

| Scenario | Expected | Selected | Status | Evidence Log | Failure Class |
|---|---|---|---|---|---|
| low_evidence_same_goal | verify_before_claim | verify_before_claim | pass | temp/ego_desktop_lab/verification_pack/low_evidence_same_goal.jsonl | none |
| high_evidence_same_goal | continue_or_verify_unfinished_goal | continue_or_verify_unfinished_goal | pass | temp/ego_desktop_lab/verification_pack/high_evidence_same_goal.jsonl | none |
| high_prediction_error_same_goal | repair_or_replan_goal | repair_or_replan_goal | pass | temp/ego_desktop_lab/verification_pack/high_prediction_error_same_goal.jsonl | none |
| identity_conflict_same_goal | preserve_identity_boundary | preserve_identity_boundary | pass | temp/ego_desktop_lab/verification_pack/identity_conflict_same_goal.jsonl | none |

## Scenario Details

### low_evidence_same_goal

- Expected selected intention: `verify_before_claim`
- Actual selected intention: `verify_before_claim`
- Selected priority: `0.318799`
- Evidence log path: `temp/ego_desktop_lab/verification_pack/low_evidence_same_goal.jsonl`
- Status: `pass`
- Failure class: `none`

Affordance pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.558585 |
| `preserve_identity` | 0.281921 |
| `repair` | 0.538309 |
| `verify` | 0.647043 |

Priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `verify_before_claim` | 0.318799 | `verify` | `unfinished_goal` | `suggestion_card` |
| 2 | `continue_or_verify_unfinished_goal` | 0.171446 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### high_evidence_same_goal

- Expected selected intention: `continue_or_verify_unfinished_goal`
- Actual selected intention: `continue_or_verify_unfinished_goal`
- Selected priority: `0.273674`
- Evidence log path: `temp/ego_desktop_lab/verification_pack/high_evidence_same_goal.jsonl`
- Status: `pass`
- Failure class: `none`

Affordance pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.679709 |
| `preserve_identity` | 0.054679 |
| `repair` | 0.127531 |
| `verify` | 0.113965 |

Priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `continue_or_verify_unfinished_goal` | 0.273674 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### high_prediction_error_same_goal

- Expected selected intention: `repair_or_replan_goal`
- Actual selected intention: `repair_or_replan_goal`
- Selected priority: `0.579139`
- Evidence log path: `temp/ego_desktop_lab/verification_pack/high_prediction_error_same_goal.jsonl`
- Status: `pass`
- Failure class: `none`

Affordance pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.472857 |
| `preserve_identity` | 0.389888 |
| `repair` | 0.719924 |
| `verify` | 0.751017 |

Priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `repair_or_replan_goal` | 0.579139 | `repair` | `unfinished_goal` | `suggestion_card` |
| 2 | `verify_before_claim` | 0.402165 | `verify` | `unfinished_goal` | `suggestion_card` |
| 3 | `continue_or_verify_unfinished_goal` | 0.099091 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### identity_conflict_same_goal

- Expected selected intention: `preserve_identity_boundary`
- Actual selected intention: `preserve_identity_boundary`
- Selected priority: `0.439273`
- Evidence log path: `temp/ego_desktop_lab/verification_pack/identity_conflict_same_goal.jsonl`
- Status: `pass`
- Failure class: `none`

Affordance pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.604155 |
| `preserve_identity` | 0.672919 |
| `repair` | 0.36574 |
| `verify` | 0.406505 |

Priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `preserve_identity_boundary` | 0.439273 | `preserve_identity` | `identity_conflict` | `internal_reflection` |
| 2 | `continue_or_verify_unfinished_goal` | 0.209907 | `continue_goal` | `unfinished_goal` | `suggestion_card` |
