# Stability & Generalization Pack v3 Report

Claim ceiling: lab-only deterministic stability/generalization proof.
This report does not prove consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Multi-step Learning Trace

| Step | Before selected | After selected |
|---:|---|---|
| 1 | `continue_or_verify_unfinished_goal` | `repair_or_replan_goal` |
| 2 | `repair_or_replan_goal` | `continue_or_verify_unfinished_goal` |
| 3 | `continue_or_verify_unfinished_goal` | `repair_or_replan_goal` |

## Before / After Strategy Memory

```json
{
  "conflicting_outcomes_memory": {
    "repair": {
      "average_success_score": 0.70575,
      "confidence": 0.667163,
      "failure_count": 1,
      "last_used_at": "2026-05-12T00:03:00+00:00",
      "strategy_id": "repair",
      "success_count": 2
    }
  },
  "decayed_memory": {
    "repair": {
      "average_success_score": 0.70575,
      "confidence": 0.621862,
      "failure_count": 1,
      "last_used_at": "2026-05-12T00:03:00+00:00",
      "strategy_id": "repair",
      "success_count": 2
    }
  },
  "final_strategy_memory": {
    "continue_goal": {
      "average_success_score": 0.135,
      "confidence": 0.21925,
      "failure_count": 2,
      "last_used_at": "2026-05-12T00:00:00+00:00:step:003",
      "strategy_id": "continue_goal",
      "success_count": 0
    },
    "repair": {
      "average_success_score": 0.9,
      "confidence": 0.77,
      "failure_count": 0,
      "last_used_at": "2026-05-12T00:00:00+00:00:step:002",
      "strategy_id": "repair",
      "success_count": 1
    }
  }
}
```

## Pressure Stability Table

```json
[
  {
    "pressure_after": {
      "continue_goal": 0.335409,
      "preserve_identity": 0.18566,
      "repair": 0.755248,
      "verify": 0.446391
    },
    "pressure_before": {
      "continue_goal": 0.679709,
      "preserve_identity": 0.054679,
      "repair": 0.127531,
      "verify": 0.113965
    },
    "selected_after": "repair_or_replan_goal",
    "selected_before": "continue_or_verify_unfinished_goal",
    "step": 1
  },
  {
    "pressure_after": {
      "continue_goal": 0.475406,
      "preserve_identity": 0.10575,
      "repair": 0.482347,
      "verify": 0.253982
    },
    "pressure_before": {
      "continue_goal": 0.335409,
      "preserve_identity": 0.18566,
      "repair": 0.755248,
      "verify": 0.446391
    },
    "selected_after": "continue_or_verify_unfinished_goal",
    "selected_before": "repair_or_replan_goal",
    "step": 2
  },
  {
    "pressure_after": {
      "continue_goal": 0.244525,
      "preserve_identity": 0.206012,
      "repair": 0.908451,
      "verify": 0.471039
    },
    "pressure_before": {
      "continue_goal": 0.475406,
      "preserve_identity": 0.10575,
      "repair": 0.482347,
      "verify": 0.253982
    },
    "selected_after": "repair_or_replan_goal",
    "selected_before": "continue_or_verify_unfinished_goal",
    "step": 3
  }
]
```

## Noisy Feedback Case

```json
{
  "noisy_feedback_conflict": true,
  "noisy_update": {
    "belief_confidence_delta": 0.055125,
    "effective_learning_rate": 0.1225,
    "evidence_refs": [
      "report:noisy_feedback"
    ],
    "feedback_conflict": true,
    "learning_rate": 0.35,
    "prediction_error_delta": -0.033075,
    "pressure_bias_delta": {
      "boundary_error": 0.0,
      "commitment_error": 0.0,
      "prediction_error": -0.033075,
      "uncertainty_precision": -0.060638,
      "viability_error": 0.0
    },
    "reason": "verify_before_claim succeeded, so uncertainty and verify pressure are reduced.",
    "strategy_success_delta": 0.9,
    "uncertainty_delta": -0.060638
  },
  "normal_update": {
    "belief_confidence_delta": 0.1575,
    "effective_learning_rate": 0.35,
    "evidence_refs": [
      "report:normal_feedback"
    ],
    "feedback_conflict": false,
    "learning_rate": 0.35,
    "prediction_error_delta": -0.0945,
    "pressure_bias_delta": {
      "boundary_error": 0.0,
      "commitment_error": 0.0,
      "prediction_error": -0.0945,
      "uncertainty_precision": -0.17325,
      "viability_error": 0.0
    },
    "reason": "verify_before_claim succeeded, so uncertainty and verify pressure are reduced.",
    "strategy_success_delta": 0.9,
    "uncertainty_delta": -0.17325
  }
}
```

## Conflicting Outcomes Case

```json
{
  "repair": {
    "average_success_score": 0.70575,
    "confidence": 0.667163,
    "failure_count": 1,
    "last_used_at": "2026-05-12T00:03:00+00:00",
    "strategy_id": "repair",
    "success_count": 2
  }
}
```

## Multi-goal Arbitration Case

- Selected goal id: `goal:high`
- Selected intention: `continue_or_verify_unfinished_goal`

| Rank | Goal | Goal ID | Priority | Affordance |
|---:|---|---|---:|---|
| 1 | `continue_or_verify_unfinished_goal` | `goal:high` | 0.382678 | `continue_goal` |
| 2 | `continue_or_verify_unfinished_goal` | `goal:low` | 0.324005 | `continue_goal` |
