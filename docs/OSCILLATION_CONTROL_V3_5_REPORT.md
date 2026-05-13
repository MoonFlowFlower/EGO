# Oscillation Control & Goal Progress Stability v3.5 Report

Claim ceiling: lab-only deterministic oscillation-control proof.
This report does not prove consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Continue/Repair Loop Case

- Final selected intention: `reframe_or_split_goal`
- Oscillation detected: `True`
- Reason: `continue/repair oscillation triggered goal reframe`

```json
{
  "evidence_log_path": "temp/ego_desktop_lab/oscillation_v3_5/report.jsonl",
  "goal_progress_after": {
    "consecutive_failures": 4,
    "consecutive_repairs": 1,
    "goal_id": "goal:001",
    "last_failed_strategy": "repair",
    "last_selected_intention": "repair_or_replan_goal",
    "last_successful_strategy": null,
    "progress_score": 0.0,
    "repair_count": 2,
    "selection_history": [
      "continue_or_verify_unfinished_goal",
      "repair_or_replan_goal",
      "continue_or_verify_unfinished_goal",
      "repair_or_replan_goal"
    ],
    "should_pause": true,
    "should_reframe": true,
    "should_split": true,
    "stagnation_count": 4
  },
  "goal_progress_before": {
    "consecutive_failures": 3,
    "consecutive_repairs": 0,
    "goal_id": "goal:001",
    "last_failed_strategy": null,
    "last_selected_intention": "continue_or_verify_unfinished_goal",
    "last_successful_strategy": null,
    "progress_score": 0.0,
    "repair_count": 1,
    "selection_history": [
      "continue_or_verify_unfinished_goal",
      "repair_or_replan_goal",
      "continue_or_verify_unfinished_goal"
    ],
    "should_pause": false,
    "should_reframe": false,
    "should_split": false,
    "stagnation_count": 3
  },
  "raw_priority_ranking": [
    {
      "affordance": "repair",
      "goal": "repair_or_replan_goal",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:003:repair_or_replan_goal",
      "priority": 0.579139,
      "proposed_action": "suggestion_card",
      "rank": 1,
      "source_tension": "unfinished_goal"
    },
    {
      "affordance": "verify",
      "goal": "verify_before_claim",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:002:verify_before_claim",
      "priority": 0.402165,
      "proposed_action": "suggestion_card",
      "rank": 2,
      "source_tension": "unfinished_goal"
    },
    {
      "affordance": "continue_goal",
      "goal": "continue_or_verify_unfinished_goal",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:001:continue_or_verify_unfinished_goal",
      "priority": 0.099091,
      "proposed_action": "suggestion_card",
      "rank": 3,
      "source_tension": "unfinished_goal"
    }
  ]
}
```

## Repeated Repair Case

```json
{
  "cooldown_decision": {
    "blocked_by_cooldown": false,
    "high_risk_threshold": 0.85,
    "reason": "cooldown not applicable",
    "replacement_goal": null,
    "risk": 0.05,
    "suppressed_goal": null
  },
  "hysteresis_decision": {
    "blocked_by_hysteresis": false,
    "candidate_goal": "split_goal_or_redefine_success_criteria",
    "current_goal": null,
    "margin": 0.05,
    "priority_delta": 0.0,
    "reason": "hysteresis skipped for hard oscillation/failure routing"
  },
  "oscillation_detected": true,
  "ranked_intentions": [
    {
      "affordance": "repair",
      "cost": 0.15,
      "goal": "split_goal_or_redefine_success_criteria",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:oscillation:split_goal_or_redefine_success_criteria:goal:001",
      "priority": 0.779139,
      "proposed_action": "suggestion_card",
      "reason": "Repeated repair without progress indicates the goal should be split or success criteria redefined.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.844,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    {
      "affordance": "repair",
      "cost": 0.1,
      "goal": "repair_or_replan_goal",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:003:repair_or_replan_goal",
      "priority": 0.579139,
      "proposed_action": "suggestion_card",
      "reason": "Low viability or high prediction error creates pressure to repair or replan.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.844,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:002:verify_before_claim",
      "priority": 0.402165,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.844,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    {
      "affordance": "continue_goal",
      "cost": 0.2,
      "goal": "continue_or_verify_unfinished_goal",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:001:continue_or_verify_unfinished_goal",
      "priority": 0.099091,
      "proposed_action": "suggestion_card",
      "reason": "An unfinished goal creates pressure to continue it or verify closure.",
      "risk": 0.1,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.844,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    }
  ],
  "reason": "repeated repair without progress triggered goal split",
  "routed_goal": "split_goal_or_redefine_success_criteria",
  "selected_intention": {
    "affordance": "repair",
    "cost": 0.15,
    "goal": "split_goal_or_redefine_success_criteria",
    "goal_description": "verify whether reflection changes behavior",
    "goal_id": "goal:001",
    "id": "intention:oscillation:split_goal_or_redefine_success_criteria:goal:001",
    "priority": 0.779139,
    "proposed_action": "suggestion_card",
    "reason": "Repeated repair without progress indicates the goal should be split or success criteria redefined.",
    "risk": 0.05,
    "source_tension": {
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "severity": 0.844,
      "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
      "type": "unfinished_goal"
    }
  }
}
```

## Hysteresis Case

```json
{
  "blocked_by_hysteresis": true,
  "candidate_goal": "verify_before_claim",
  "current_goal": "continue_or_verify_unfinished_goal",
  "margin": 0.05,
  "priority_delta": 0.03,
  "reason": "candidate priority advantage is below hysteresis margin"
}
```

## Cooldown Case

```json
{
  "blocked_by_cooldown": true,
  "high_risk_threshold": 0.85,
  "reason": "repair suppressed by cooldown",
  "replacement_goal": "verify_before_claim",
  "risk": 0.1,
  "suppressed_goal": "repair_or_replan_goal"
}
```

## Failure Type Routing Case

```json
{
  "evidence_failure": "verify_before_claim",
  "execution_failure": "retry_or_change_tool",
  "goal_definition_failure": "reframe_or_split_goal",
  "permission_failure": "ask_permission_or_defer",
  "plan_failure": "repair_or_replan_goal"
}
```
