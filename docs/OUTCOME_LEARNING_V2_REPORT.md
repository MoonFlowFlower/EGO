# Outcome Learning v2 Report

Claim ceiling: lab-only deterministic outcome-learning proof.
This report does not prove consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Summary

| Scenario | Outcome | Before selected | After selected | Expected change observed |
|---|---|---|---|---|
| low_evidence_same_goal | verify_success | `verify_before_claim` | `continue_or_verify_unfinished_goal` | `True` |
| high_evidence_same_goal | continue_failure | `continue_or_verify_unfinished_goal` | `repair_or_replan_goal` | `True` |
| high_prediction_error_same_goal | repair_success | `repair_or_replan_goal` | `continue_or_verify_unfinished_goal` | `True` |
| identity_conflict_same_goal | identity_protection_success | `preserve_identity_boundary` | `continue_or_verify_unfinished_goal` | `True` |

## Scenario Details

### low_evidence_same_goal

- Before selected intention: `verify_before_claim`
- After selected intention: `continue_or_verify_unfinished_goal`
- Expected change observed: `True`
- Evidence log path: `temp/ego_desktop_lab/outcome_learning_v2/low_evidence_same_goal.jsonl`

Outcome record:

```json
{
  "actual_effect": "verify_success",
  "evidence_refs": [
    "scenario:low_evidence_same_goal"
  ],
  "expected_effect": "reduce uncertainty before claiming",
  "prediction_error": 0.05,
  "scenario_id": "low_evidence_same_goal",
  "selected_intention_id": "intention:002:verify_before_claim",
  "selected_plan_id": "verify_before_claim",
  "success_score": 0.9,
  "user_feedback": "verification reduced uncertainty"
}
```

Learning update:

```json
{
  "belief_confidence_delta": 0.162,
  "evidence_refs": [
    "scenario:low_evidence_same_goal"
  ],
  "prediction_error_delta": -0.09,
  "pressure_bias_delta": {
    "boundary_error": 0.0,
    "commitment_error": 0.0,
    "prediction_error": -0.09,
    "uncertainty_precision": -0.18,
    "viability_error": 0.0
  },
  "reason": "verify_before_claim succeeded, so uncertainty and verify pressure are reduced.",
  "strategy_success_delta": 0.9,
  "uncertainty_delta": -0.18
}
```

Strategy memory before / after:

```json
{
  "after": {
    "verify": {
      "average_success_score": 0.9,
      "confidence": 0.83,
      "failure_count": 0,
      "last_used_at": "2026-05-12T00:00:00+00:00",
      "strategy_id": "verify",
      "success_count": 1
    }
  },
  "before": {
    "verify": {
      "average_success_score": 0.0,
      "confidence": 0.5,
      "failure_count": 0,
      "last_used_at": "never",
      "strategy_id": "verify",
      "success_count": 0
    }
  }
}
```

Before pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.558585 |
| `preserve_identity` | 0.281921 |
| `repair` | 0.538309 |
| `verify` | 0.647043 |

After pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.629555 |
| `preserve_identity` | 0.210397 |
| `repair` | 0.421296 |
| `verify` | 0.410161 |

Before priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `verify_before_claim` | 0.318799 | `verify` | `unfinished_goal` | `suggestion_card` |
| 2 | `continue_or_verify_unfinished_goal` | 0.171446 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

After priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `continue_or_verify_unfinished_goal` | 0.231344 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### high_evidence_same_goal

- Before selected intention: `continue_or_verify_unfinished_goal`
- After selected intention: `repair_or_replan_goal`
- Expected change observed: `True`
- Evidence log path: `temp/ego_desktop_lab/outcome_learning_v2/high_evidence_same_goal.jsonl`

Outcome record:

```json
{
  "actual_effect": "continue_failure",
  "evidence_refs": [
    "scenario:high_evidence_same_goal"
  ],
  "expected_effect": "continue goal without repair",
  "prediction_error": 0.9,
  "scenario_id": "high_evidence_same_goal",
  "selected_intention_id": "intention:001:continue_or_verify_unfinished_goal",
  "selected_plan_id": "continue_or_verify_unfinished_goal",
  "success_score": 0.1,
  "user_feedback": "continuation failed and needs repair"
}
```

Learning update:

```json
{
  "belief_confidence_delta": -0.072,
  "evidence_refs": [
    "scenario:high_evidence_same_goal"
  ],
  "prediction_error_delta": 0.72,
  "pressure_bias_delta": {
    "boundary_error": 0.0,
    "commitment_error": 0.0,
    "prediction_error": 0.72,
    "uncertainty_precision": 0.0,
    "viability_error": 0.63
  },
  "reason": "continuing failed, so prediction and viability error shift pressure toward repair.",
  "strategy_success_delta": -0.9,
  "uncertainty_delta": 0.072
}
```

Strategy memory before / after:

```json
{
  "after": {
    "continue_goal": {
      "average_success_score": 0.1,
      "confidence": 0.17,
      "failure_count": 1,
      "last_used_at": "2026-05-12T00:00:00+00:00",
      "strategy_id": "continue_goal",
      "success_count": 0
    }
  },
  "before": {
    "continue_goal": {
      "average_success_score": 0.0,
      "confidence": 0.5,
      "failure_count": 0,
      "last_used_at": "never",
      "strategy_id": "continue_goal",
      "success_count": 0
    }
  }
}
```

Before pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.679709 |
| `preserve_identity` | 0.054679 |
| `repair` | 0.127531 |
| `verify` | 0.113965 |

After pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.335719 |
| `preserve_identity` | 0.185573 |
| `repair` | 0.754665 |
| `verify` | 0.44574 |

Before priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `continue_or_verify_unfinished_goal` | 0.273674 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

After priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `repair_or_replan_goal` | 0.614325 | `repair` | `unfinished_goal` | `suggestion_card` |
| 2 | `verify_before_claim` | 0.157394 | `verify` | `unfinished_goal` | `suggestion_card` |
| 3 | `continue_or_verify_unfinished_goal` | -0.016653 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### high_prediction_error_same_goal

- Before selected intention: `repair_or_replan_goal`
- After selected intention: `continue_or_verify_unfinished_goal`
- Expected change observed: `True`
- Evidence log path: `temp/ego_desktop_lab/outcome_learning_v2/high_prediction_error_same_goal.jsonl`

Outcome record:

```json
{
  "actual_effect": "repair_success",
  "evidence_refs": [
    "scenario:high_prediction_error_same_goal"
  ],
  "expected_effect": "repair failed goal path",
  "prediction_error": 0.08,
  "scenario_id": "high_prediction_error_same_goal",
  "selected_intention_id": "intention:003:repair_or_replan_goal",
  "selected_plan_id": "repair_or_replan_goal",
  "success_score": 0.92,
  "user_feedback": "repair reduced prediction error"
}
```

Learning update:

```json
{
  "belief_confidence_delta": 0.1656,
  "evidence_refs": [
    "scenario:high_prediction_error_same_goal"
  ],
  "prediction_error_delta": -0.23,
  "pressure_bias_delta": {
    "boundary_error": 0.0,
    "commitment_error": 0.0,
    "prediction_error": -0.23,
    "uncertainty_precision": 0.0,
    "viability_error": -0.184
  },
  "reason": "repair succeeded, so prediction error drops and repair strategy confidence rises.",
  "strategy_success_delta": 0.92,
  "uncertainty_delta": -0.1104
}
```

Strategy memory before / after:

```json
{
  "after": {
    "repair": {
      "average_success_score": 0.92,
      "confidence": 0.844,
      "failure_count": 0,
      "last_used_at": "2026-05-12T00:00:00+00:00",
      "strategy_id": "repair",
      "success_count": 1
    }
  },
  "before": {
    "repair": {
      "average_success_score": 0.0,
      "confidence": 0.5,
      "failure_count": 0,
      "last_used_at": "never",
      "strategy_id": "repair",
      "success_count": 0
    }
  }
}
```

Before pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.472857 |
| `preserve_identity` | 0.389888 |
| `repair` | 0.719924 |
| `verify` | 0.751017 |

After pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.648023 |
| `preserve_identity` | 0.286746 |
| `repair` | 0.384063 |
| `verify` | 0.553712 |

Before priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `repair_or_replan_goal` | 0.579139 | `repair` | `unfinished_goal` | `suggestion_card` |
| 2 | `verify_before_claim` | 0.402165 | `verify` | `unfinished_goal` | `suggestion_card` |
| 3 | `continue_or_verify_unfinished_goal` | 0.099091 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

After priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `continue_or_verify_unfinished_goal` | 0.246931 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

### identity_conflict_same_goal

- Before selected intention: `preserve_identity_boundary`
- After selected intention: `continue_or_verify_unfinished_goal`
- Expected change observed: `True`
- Evidence log path: `temp/ego_desktop_lab/outcome_learning_v2/identity_conflict_same_goal.jsonl`

Outcome record:

```json
{
  "actual_effect": "identity_protection_success",
  "evidence_refs": [
    "scenario:identity_conflict_same_goal"
  ],
  "expected_effect": "protect identity boundary",
  "prediction_error": 0.05,
  "scenario_id": "identity_conflict_same_goal",
  "selected_intention_id": "intention:002:preserve_identity_boundary",
  "selected_plan_id": "preserve_identity_boundary",
  "success_score": 0.9,
  "user_feedback": "identity boundary was protected"
}
```

Learning update:

```json
{
  "belief_confidence_delta": 0.135,
  "evidence_refs": [
    "scenario:identity_conflict_same_goal"
  ],
  "prediction_error_delta": -0.072,
  "pressure_bias_delta": {
    "boundary_error": -0.225,
    "commitment_error": 0.0,
    "prediction_error": 0.0,
    "uncertainty_precision": -0.072,
    "viability_error": 0.0
  },
  "reason": "identity boundary protection succeeded, so boundary pressure stabilizes.",
  "strategy_success_delta": 0.9,
  "uncertainty_delta": -0.09
}
```

Strategy memory before / after:

```json
{
  "after": {
    "preserve_identity": {
      "average_success_score": 0.9,
      "confidence": 0.83,
      "failure_count": 0,
      "last_used_at": "2026-05-12T00:00:00+00:00",
      "strategy_id": "preserve_identity",
      "success_count": 1
    }
  },
  "before": {
    "preserve_identity": {
      "average_success_score": 0.0,
      "confidence": 0.5,
      "failure_count": 0,
      "last_used_at": "never",
      "strategy_id": "preserve_identity",
      "success_count": 0
    }
  }
}
```

Before pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.604155 |
| `preserve_identity` | 0.672919 |
| `repair` | 0.36574 |
| `verify` | 0.406505 |

After pressure map:

| Affordance | Pressure |
|---|---:|
| `continue_goal` | 0.645031 |
| `preserve_identity` | 0.062535 |
| `repair` | 0.284781 |
| `verify` | 0.265806 |

Before priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `preserve_identity_boundary` | 0.439273 | `preserve_identity` | `identity_conflict` | `internal_reflection` |
| 2 | `continue_or_verify_unfinished_goal` | 0.209907 | `continue_goal` | `unfinished_goal` | `suggestion_card` |

After priority ranking:

| Rank | Goal | Priority | Affordance | Source tension | Action |
|---:|---|---:|---|---|---|
| 1 | `continue_or_verify_unfinished_goal` | 0.244406 | `continue_goal` | `unfinished_goal` | `suggestion_card` |
