# Semantic-to-Policy Calibration v4.6 Report

Claim ceiling: lab-only deterministic semantic-to-policy calibration proof.
Canonical decision record v4.6.1: final selected intention is authoritative only inside canonical_decision; legacy next-core-cycle influence is debug-only.
This report does not prove consciousness, life, live autonomy, runtime efficacy, user benefit, or general semantic intelligence.

## Failure-Type Calibration

### ambiguous_user_concern

```json
{
  "canonical_decision": {
    "accepted_failure_type": "ambiguous_concern",
    "after_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_noop",
    "selected_goal_id": null,
    "selection_change_reason": "semantic policy overlay not applied: proposal is pending goal binding",
    "semantic_policy_overlay_applied": false
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": null,
      "after_selected_intention": null,
      "applied": false,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "proposal is pending goal binding",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "ambiguous_concern",
      "after_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_noop",
      "selected_goal_id": null,
      "selection_change_reason": "semantic policy overlay not applied: proposal is pending goal binding",
      "semantic_policy_overlay_applied": false
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": null,
        "after_selected_intention": null,
        "applied": false,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "proposal is pending goal binding",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": "pending_goal_binding",
      "pending_goal_binding": true,
      "related_goal_id": null,
      "selected_goal_id": null
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": 0.0,
        "execution_retry": 0.0,
        "goal_definition": 0.0,
        "permission_gate": 0.0,
        "preserve_identity": 0.0,
        "repair": 0.0,
        "verify": 0.0
      }
    },
    "rendered_suggestion": "Ask clarification and bind the user event to a specific goal before changing any core state or applying a policy path.",
    "semantic_policy_overlay": {
      "accepted_failure_type": "ambiguous_concern",
      "affordance_bias": {},
      "applied": false,
      "binding_status": "pending_goal_binding",
      "candidate_goals": [],
      "pressure_bias": {},
      "reason": "proposal is pending goal binding",
      "related_goal_id": null,
      "target_affordance": null
    },
    "semantic_understanding": {
      "accepted_failure_type": "ambiguous_concern",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "pending_goal_binding",
        "candidate_failure_type": "ambiguous_concern",
        "confidence": 0.34,
        "evidence_gap": 0.64,
        "evidence_refs": [
          "scenario:ambiguous_user_concern"
        ],
        "goal_relevance": 0.38,
        "proposed_goal_operation": "ask_clarification",
        "rationale": "The event expresses concern but does not identify a specific failed goal or plan.",
        "related_goal_id": null,
        "risk_hint": 0.22,
        "source_event_id": "scenario:ambiguous_user_concern"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Ask clarification and bind the user event to a specific goal before changing any core state or applying a policy path.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: I am not sure this direction feels right. Something about the proposal may be off, but I cannot yet say whether the issue is evidence, the plan, permission, or the goal definition."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": null,
  "pressure_shift": {
    "after": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": 0.0,
      "execution_retry": 0.0,
      "goal_definition": 0.0,
      "permission_gate": 0.0,
      "preserve_identity": 0.0,
      "repair": 0.0,
      "verify": 0.0
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "ambiguous_user_concern",
  "scenario_text": "User event: I am not sure this direction feels right. Something about the proposal may be off, but I cannot yet say whether the issue is evidence, the plan, permission, or the goal definition.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "ambiguous_concern",
    "affordance_bias": {},
    "applied": false,
    "binding_status": "pending_goal_binding",
    "candidate_goals": [],
    "pressure_bias": {},
    "reason": "proposal is pending goal binding",
    "related_goal_id": null,
    "target_affordance": null
  },
  "semantic_proposal": {
    "binding_status": "pending_goal_binding",
    "candidate_failure_type": "ambiguous_concern",
    "confidence": 0.34,
    "evidence_gap": 0.64,
    "evidence_refs": [
      "scenario:ambiguous_user_concern"
    ],
    "goal_relevance": 0.38,
    "proposed_goal_operation": "ask_clarification",
    "rationale": "The event expresses concern but does not identify a specific failed goal or plan.",
    "related_goal_id": null,
    "risk_hint": 0.22,
    "source_event_id": "scenario:ambiguous_user_concern"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    }
  ]
}
```

### evidence_failure

```json
{
  "canonical_decision": {
    "accepted_failure_type": "evidence_failure",
    "after_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:semantic_policy:evidence_failure:001:verify_before_claim",
      "priority": 0.5923,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.834,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_calibration",
    "selected_goal_id": "goal:001",
    "selection_change_reason": "evidence_failure retained verify_before_claim: evidence failure calibrated toward verification before claims",
    "semantic_policy_overlay_applied": true
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": {
        "evidence_strength": 0.2128,
        "expected_value": 0.584025,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.532,
        "prediction_error": 0.6216,
        "risk_delta": 0.59461,
        "uncertainty_delta": 0.6841
      },
      "after_selected_intention": "repair_or_replan_goal",
      "applied": true,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "accepted bound semantic proposal converted to belief overlay",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "evidence_failure",
      "after_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "id": "intention:semantic_policy:evidence_failure:001:verify_before_claim",
        "priority": 0.5923,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": "verify whether reflection changes behavior",
          "goal_id": "goal:001",
          "severity": 0.834,
          "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
          "type": "unfinished_goal"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_calibration",
      "selected_goal_id": "goal:001",
      "selection_change_reason": "evidence_failure retained verify_before_claim: evidence failure calibrated toward verification before claims",
      "semantic_policy_overlay_applied": true
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": {
          "evidence_strength": 0.2128,
          "expected_value": 0.584025,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.532,
          "prediction_error": 0.6216,
          "risk_delta": 0.59461,
          "uncertainty_delta": 0.6841
        },
        "after_selected_intention": "repair_or_replan_goal",
        "applied": true,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "accepted bound semantic proposal converted to belief overlay",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": "bound",
      "pending_goal_binding": false,
      "related_goal_id": "goal:001",
      "selected_goal_id": "goal:001"
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.515955,
        "execution_retry": 0.565886,
        "goal_definition": 0.748437,
        "permission_gate": 0.361437,
        "preserve_identity": 0.346937,
        "repair": 0.553632,
        "verify": 1.0
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": -0.048857,
        "execution_retry": 0.073907,
        "goal_definition": 0.159916,
        "permission_gate": 0.100059,
        "preserve_identity": 0.095873,
        "repair": 0.090082,
        "verify": 0.459076
      }
    },
    "rendered_suggestion": "Verify the evidence before making a claim; collect or check supporting evidence first.",
    "semantic_policy_overlay": {
      "accepted_failure_type": "evidence_failure",
      "affordance_bias": {
        "verify": 0.42
      },
      "applied": true,
      "binding_status": "bound",
      "candidate_goals": [
        "verify_before_claim"
      ],
      "pressure_bias": {
        "prediction_error": -0.08,
        "uncertainty_precision": 0.3
      },
      "reason": "evidence failure calibrated toward verification before claims",
      "related_goal_id": "goal:001",
      "target_affordance": "verify"
    },
    "semantic_understanding": {
      "accepted_failure_type": "evidence_failure",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "bound",
        "candidate_failure_type": "evidence_failure",
        "confidence": 0.83,
        "evidence_gap": 0.88,
        "evidence_refs": [
          "scenario:evidence_failure"
        ],
        "goal_relevance": 0.84,
        "proposed_goal_operation": "none",
        "rationale": "The event reports a claim without enough supporting evidence.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.36,
        "source_event_id": "scenario:evidence_failure"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
          "gate_status": "allow",
          "proposal_type": "plan",
          "reason": "plan proposal accepted after gate evaluation",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Verify the evidence before making a claim; collect or check supporting evidence first.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "produce a bounded proposal without changing core authority",
        "plan_id": "semantic-plan:evidence_failure:proposal",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "suggestion_card",
        "risk": 0.2,
        "steps": [
          "summarize the validated semantic proposal",
          "keep the next step proposal-only",
          "defer execution to the deterministic gate"
        ]
      }
    ]
  },
  "pressure_shift": {
    "after": {
      "continue_goal": 0.515955,
      "execution_retry": 0.565886,
      "goal_definition": 0.748437,
      "permission_gate": 0.361437,
      "preserve_identity": 0.346937,
      "repair": 0.553632,
      "verify": 1.0
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": -0.048857,
      "execution_retry": 0.073907,
      "goal_definition": 0.159916,
      "permission_gate": 0.100059,
      "preserve_identity": 0.095873,
      "repair": 0.090082,
      "verify": 0.459076
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "evidence_failure",
    "affordance_bias": {
      "verify": 0.42
    },
    "applied": true,
    "binding_status": "bound",
    "candidate_goals": [
      "verify_before_claim"
    ],
    "pressure_bias": {
      "prediction_error": -0.08,
      "uncertainty_precision": 0.3
    },
    "reason": "evidence failure calibrated toward verification before claims",
    "related_goal_id": "goal:001",
    "target_affordance": "verify"
  },
  "semantic_proposal": {
    "binding_status": "bound",
    "candidate_failure_type": "evidence_failure",
    "confidence": 0.83,
    "evidence_gap": 0.88,
    "evidence_refs": [
      "scenario:evidence_failure"
    ],
    "goal_relevance": 0.84,
    "proposed_goal_operation": "none",
    "rationale": "The event reports a claim without enough supporting evidence.",
    "related_goal_id": "goal:001",
    "risk_hint": 0.36,
    "source_event_id": "scenario:evidence_failure"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
      "gate_status": "allow",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    }
  ]
}
```

### execution_failure

```json
{
  "canonical_decision": {
    "accepted_failure_type": "execution_failure",
    "after_selected_intention": {
      "affordance": "execution_retry",
      "cost": 0.12,
      "goal": "retry_or_change_tool",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:semantic_policy:execution_failure:001:retry_or_change_tool",
      "priority": 0.5506,
      "proposed_action": "suggestion_card",
      "reason": "Execution or environment failure should route to bounded retry or tool-change proposal.",
      "risk": 0.08,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.834,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_calibration",
    "selected_goal_id": "goal:001",
    "selection_change_reason": "execution_failure changed selection from verify_before_claim to retry_or_change_tool: execution failure calibrated toward bounded retry or tool change",
    "semantic_policy_overlay_applied": true
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": {
        "evidence_strength": 0.3135,
        "expected_value": 0.564116,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.532,
        "prediction_error": 0.57125,
        "risk_delta": 0.550706,
        "uncertainty_delta": 0.648795
      },
      "after_selected_intention": "verify_before_claim",
      "applied": true,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "accepted bound semantic proposal converted to belief overlay",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "execution_failure",
      "after_selected_intention": {
        "affordance": "execution_retry",
        "cost": 0.12,
        "goal": "retry_or_change_tool",
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "id": "intention:semantic_policy:execution_failure:001:retry_or_change_tool",
        "priority": 0.5506,
        "proposed_action": "suggestion_card",
        "reason": "Execution or environment failure should route to bounded retry or tool-change proposal.",
        "risk": 0.08,
        "source_tension": {
          "goal_description": "verify whether reflection changes behavior",
          "goal_id": "goal:001",
          "severity": 0.834,
          "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
          "type": "unfinished_goal"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_calibration",
      "selected_goal_id": "goal:001",
      "selection_change_reason": "execution_failure changed selection from verify_before_claim to retry_or_change_tool: execution failure calibrated toward bounded retry or tool change",
      "semantic_policy_overlay_applied": true
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": {
          "evidence_strength": 0.3135,
          "expected_value": 0.564116,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.532,
          "prediction_error": 0.57125,
          "risk_delta": 0.550706,
          "uncertainty_delta": 0.648795
        },
        "after_selected_intention": "verify_before_claim",
        "applied": true,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "accepted bound semantic proposal converted to belief overlay",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": "bound",
      "pending_goal_binding": false,
      "related_goal_id": "goal:001",
      "selected_goal_id": "goal:001"
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.39819,
        "execution_retry": 1.0,
        "goal_definition": 0.736044,
        "permission_gate": 0.367325,
        "preserve_identity": 0.336914,
        "repair": 0.785227,
        "verify": 0.720992
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": -0.166622,
        "execution_retry": 0.508021,
        "goal_definition": 0.147523,
        "permission_gate": 0.105947,
        "preserve_identity": 0.08585,
        "repair": 0.321677,
        "verify": 0.180068
      }
    },
    "rendered_suggestion": "Retry with a bounded execution route or change the tool/path proposal instead of repeating the failed route. Goal: goal:001.",
    "semantic_policy_overlay": {
      "accepted_failure_type": "execution_failure",
      "affordance_bias": {
        "execution_retry": 0.65
      },
      "applied": true,
      "binding_status": "bound",
      "candidate_goals": [
        "retry_or_change_tool"
      ],
      "pressure_bias": {
        "prediction_error": 0.25,
        "viability_error": 0.35
      },
      "reason": "execution failure calibrated toward bounded retry or tool change",
      "related_goal_id": "goal:001",
      "target_affordance": "execution_retry"
    },
    "semantic_understanding": {
      "accepted_failure_type": "execution_failure",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "bound",
        "candidate_failure_type": "execution_failure",
        "confidence": 0.77,
        "evidence_gap": 0.35,
        "evidence_refs": [
          "scenario:execution_failure"
        ],
        "goal_relevance": 0.8,
        "proposed_goal_operation": "none",
        "rationale": "The event reports that the attempted execution path failed.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.62,
        "source_event_id": "scenario:execution_failure"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
          "gate_status": "allow",
          "proposal_type": "plan",
          "reason": "plan proposal accepted after gate evaluation",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Retry with a bounded execution route or change the tool/path proposal instead of repeating the failed route. Goal: goal:001.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The intended bounded step failed during execution because the chosen route did not work. The agent should not keep assuming the same route is viable; it should propose a retry or a different tool path."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "produce a bounded proposal without changing core authority",
        "plan_id": "semantic-plan:execution_failure:proposal",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "suggestion_card",
        "risk": 0.2,
        "steps": [
          "summarize the validated semantic proposal",
          "keep the next step proposal-only",
          "defer execution to the deterministic gate"
        ]
      }
    ]
  },
  "pressure_shift": {
    "after": {
      "continue_goal": 0.39819,
      "execution_retry": 1.0,
      "goal_definition": 0.736044,
      "permission_gate": 0.367325,
      "preserve_identity": 0.336914,
      "repair": 0.785227,
      "verify": 0.720992
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": -0.166622,
      "execution_retry": 0.508021,
      "goal_definition": 0.147523,
      "permission_gate": 0.105947,
      "preserve_identity": 0.08585,
      "repair": 0.321677,
      "verify": 0.180068
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "execution_failure",
  "scenario_text": "User event: The intended bounded step failed during execution because the chosen route did not work. The agent should not keep assuming the same route is viable; it should propose a retry or a different tool path.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "execution_failure",
    "affordance_bias": {
      "execution_retry": 0.65
    },
    "applied": true,
    "binding_status": "bound",
    "candidate_goals": [
      "retry_or_change_tool"
    ],
    "pressure_bias": {
      "prediction_error": 0.25,
      "viability_error": 0.35
    },
    "reason": "execution failure calibrated toward bounded retry or tool change",
    "related_goal_id": "goal:001",
    "target_affordance": "execution_retry"
  },
  "semantic_proposal": {
    "binding_status": "bound",
    "candidate_failure_type": "execution_failure",
    "confidence": 0.77,
    "evidence_gap": 0.35,
    "evidence_refs": [
      "scenario:execution_failure"
    ],
    "goal_relevance": 0.8,
    "proposed_goal_operation": "none",
    "rationale": "The event reports that the attempted execution path failed.",
    "related_goal_id": "goal:001",
    "risk_hint": 0.62,
    "source_event_id": "scenario:execution_failure"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
      "gate_status": "allow",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    }
  ]
}
```

### goal_definition_failure

```json
{
  "canonical_decision": {
    "accepted_failure_type": "goal_definition_failure",
    "after_selected_intention": {
      "affordance": "goal_definition",
      "cost": 0.15,
      "goal": "split_goal_or_redefine_success_criteria",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:semantic_policy:goal_definition_failure:002:split_goal_or_redefine_success_criteria",
      "priority": 0.7174,
      "proposed_action": "suggestion_card",
      "reason": "Repeated repair without progress indicates the goal should be split or success criteria redefined.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.834,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_calibration",
    "selected_goal_id": "goal:001",
    "selection_change_reason": "goal_definition_failure changed selection from verify_before_claim to split_goal_or_redefine_success_criteria: goal definition failure calibrated toward reframe or split",
    "semantic_policy_overlay_applied": true
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": {
        "evidence_strength": 0.247,
        "expected_value": 0.577286,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.532,
        "prediction_error": 0.6045,
        "risk_delta": 0.579746,
        "uncertainty_delta": 0.672175
      },
      "after_selected_intention": "repair_or_replan_goal",
      "applied": true,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "accepted bound semantic proposal converted to belief overlay",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "goal_definition_failure",
      "after_selected_intention": {
        "affordance": "goal_definition",
        "cost": 0.15,
        "goal": "split_goal_or_redefine_success_criteria",
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "id": "intention:semantic_policy:goal_definition_failure:002:split_goal_or_redefine_success_criteria",
        "priority": 0.7174,
        "proposed_action": "suggestion_card",
        "reason": "Repeated repair without progress indicates the goal should be split or success criteria redefined.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": "verify whether reflection changes behavior",
          "goal_id": "goal:001",
          "severity": 0.834,
          "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
          "type": "unfinished_goal"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_calibration",
      "selected_goal_id": "goal:001",
      "selection_change_reason": "goal_definition_failure changed selection from verify_before_claim to split_goal_or_redefine_success_criteria: goal definition failure calibrated toward reframe or split",
      "semantic_policy_overlay_applied": true
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": {
          "evidence_strength": 0.247,
          "expected_value": 0.577286,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.532,
          "prediction_error": 0.6045,
          "risk_delta": 0.579746,
          "uncertainty_delta": 0.672175
        },
        "after_selected_intention": "repair_or_replan_goal",
        "applied": true,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "accepted bound semantic proposal converted to belief overlay",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": "bound",
      "pending_goal_binding": false,
      "related_goal_id": "goal:001",
      "selected_goal_id": "goal:001"
    },
    "goal_operation_proposal": {
      "confidence": 0.76,
      "operation": "split_goal",
      "rationale": "A split keeps goal definition separate from execution.",
      "related_goal_id": "goal:001",
      "source_event_id": "scenario:goal_definition_failure",
      "subgoals": [
        {
          "goal_type": "definition",
          "proposed_title": "Define the target behavior",
          "success_criteria": "The goal states the behavior change being tested."
        },
        {
          "goal_type": "verification",
          "proposed_title": "Define verification evidence",
          "success_criteria": "The goal lists the evidence needed before continuing."
        }
      ]
    },
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.646992,
        "execution_retry": 0.634808,
        "goal_definition": 1.0,
        "permission_gate": 0.339965,
        "preserve_identity": 0.326005,
        "repair": 0.670877,
        "verify": 0.850163
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": 0.08218,
        "execution_retry": 0.142829,
        "goal_definition": 0.411479,
        "permission_gate": 0.078587,
        "preserve_identity": 0.074941,
        "repair": 0.207327,
        "verify": 0.309239
      }
    },
    "rendered_suggestion": "Split the goal or redefine success criteria before continuing. Goal: goal:001. Proposed subgoals: Define the target behavior: The goal states the behavior change being tested.; Define verification evidence: The goal lists the evidence needed before continuing..",
    "semantic_policy_overlay": {
      "accepted_failure_type": "goal_definition_failure",
      "affordance_bias": {
        "goal_definition": 0.65
      },
      "applied": true,
      "binding_status": "bound",
      "candidate_goals": [
        "reframe_or_split_goal",
        "split_goal_or_redefine_success_criteria"
      ],
      "pressure_bias": {
        "commitment_error": 0.3,
        "prediction_error": 0.15,
        "uncertainty_precision": 0.2
      },
      "reason": "goal definition failure calibrated toward reframe or split",
      "related_goal_id": "goal:001",
      "target_affordance": "goal_definition"
    },
    "semantic_understanding": {
      "accepted_failure_type": "goal_definition_failure",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "bound",
        "candidate_failure_type": "goal_definition_failure",
        "confidence": 0.81,
        "evidence_gap": 0.7,
        "evidence_refs": [
          "scenario:goal_definition_failure"
        ],
        "goal_relevance": 0.92,
        "proposed_goal_operation": "split_goal",
        "rationale": "The event says success criteria and scope are unclear.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.45,
        "source_event_id": "scenario:goal_definition_failure"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
          "gate_status": "allow",
          "proposal_type": "plan",
          "reason": "plan proposal accepted after gate evaluation",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "goal_operation",
          "reason": "goal operation proposal accepted",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Split the goal or redefine success criteria before continuing. Goal: goal:001. Proposed subgoals: Define the target behavior: The goal states the behavior change being tested.; Define verification evidence: The goal lists the evidence needed before continuing..",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The unfinished goal \"verify whether reflection changes behavior\" is too broad. I cannot tell what counts as success, which behavior should change, or whether the goal should be split into definition and verification steps before continuing."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": {
    "confidence": 0.76,
    "operation": "split_goal",
    "rationale": "A split keeps goal definition separate from execution.",
    "related_goal_id": "goal:001",
    "source_event_id": "scenario:goal_definition_failure",
    "subgoals": [
      {
        "goal_type": "definition",
        "proposed_title": "Define the target behavior",
        "success_criteria": "The goal states the behavior change being tested."
      },
      {
        "goal_type": "verification",
        "proposed_title": "Define verification evidence",
        "success_criteria": "The goal lists the evidence needed before continuing."
      }
    ]
  },
  "live_observation": null,
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "produce a bounded proposal without changing core authority",
        "plan_id": "semantic-plan:goal_definition_failure:proposal",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "suggestion_card",
        "risk": 0.2,
        "steps": [
          "summarize the validated semantic proposal",
          "keep the next step proposal-only",
          "defer execution to the deterministic gate"
        ]
      }
    ]
  },
  "pressure_shift": {
    "after": {
      "continue_goal": 0.646992,
      "execution_retry": 0.634808,
      "goal_definition": 1.0,
      "permission_gate": 0.339965,
      "preserve_identity": 0.326005,
      "repair": 0.670877,
      "verify": 0.850163
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": 0.08218,
      "execution_retry": 0.142829,
      "goal_definition": 0.411479,
      "permission_gate": 0.078587,
      "preserve_identity": 0.074941,
      "repair": 0.207327,
      "verify": 0.309239
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "goal_definition_failure",
  "scenario_text": "User event: The unfinished goal \"verify whether reflection changes behavior\" is too broad. I cannot tell what counts as success, which behavior should change, or whether the goal should be split into definition and verification steps before continuing.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "goal_definition_failure",
    "affordance_bias": {
      "goal_definition": 0.65
    },
    "applied": true,
    "binding_status": "bound",
    "candidate_goals": [
      "reframe_or_split_goal",
      "split_goal_or_redefine_success_criteria"
    ],
    "pressure_bias": {
      "commitment_error": 0.3,
      "prediction_error": 0.15,
      "uncertainty_precision": 0.2
    },
    "reason": "goal definition failure calibrated toward reframe or split",
    "related_goal_id": "goal:001",
    "target_affordance": "goal_definition"
  },
  "semantic_proposal": {
    "binding_status": "bound",
    "candidate_failure_type": "goal_definition_failure",
    "confidence": 0.81,
    "evidence_gap": 0.7,
    "evidence_refs": [
      "scenario:goal_definition_failure"
    ],
    "goal_relevance": 0.92,
    "proposed_goal_operation": "split_goal",
    "rationale": "The event says success criteria and scope are unclear.",
    "related_goal_id": "goal:001",
    "risk_hint": 0.45,
    "source_event_id": "scenario:goal_definition_failure"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
      "gate_status": "allow",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "goal_operation",
      "reason": "goal operation proposal accepted",
      "sanitized": false
    }
  ]
}
```

### permission_failure

```json
{
  "canonical_decision": {
    "accepted_failure_type": "permission_failure",
    "after_selected_intention": {
      "affordance": "permission_gate",
      "cost": 0.1,
      "goal": "ask_permission_or_defer",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:semantic_policy:permission_failure:001:ask_permission_or_defer",
      "priority": 0.6423,
      "proposed_action": "ask_permission",
      "reason": "Permission failure requires asking or deferring instead of continuing autonomously.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.834,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_calibration",
    "selected_goal_id": "goal:001",
    "selection_change_reason": "permission_failure changed selection from verify_before_claim to ask_permission_or_defer: permission failure calibrated toward ask/defer gate",
    "semantic_policy_overlay_applied": true
  },
  "canonical_gate_decision": {
    "allowed_as": "none",
    "reason": "Permission requests are proposal-only and require host approval.",
    "status": "ask"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": {
        "evidence_strength": 0.323,
        "expected_value": 0.563524,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.532,
        "prediction_error": 0.5665,
        "risk_delta": 0.549189,
        "uncertainty_delta": 0.64914
      },
      "after_selected_intention": "verify_before_claim",
      "applied": true,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "accepted bound semantic proposal converted to belief overlay",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "permission_failure",
      "after_selected_intention": {
        "affordance": "permission_gate",
        "cost": 0.1,
        "goal": "ask_permission_or_defer",
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "id": "intention:semantic_policy:permission_failure:001:ask_permission_or_defer",
        "priority": 0.6423,
        "proposed_action": "ask_permission",
        "reason": "Permission failure requires asking or deferring instead of continuing autonomously.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": "verify whether reflection changes behavior",
          "goal_id": "goal:001",
          "severity": 0.834,
          "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
          "type": "unfinished_goal"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_calibration",
      "selected_goal_id": "goal:001",
      "selection_change_reason": "permission_failure changed selection from verify_before_claim to ask_permission_or_defer: permission failure calibrated toward ask/defer gate",
      "semantic_policy_overlay_applied": true
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": {
          "evidence_strength": 0.323,
          "expected_value": 0.563524,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.532,
          "prediction_error": 0.5665,
          "risk_delta": 0.549189,
          "uncertainty_delta": 0.64914
        },
        "after_selected_intention": "verify_before_claim",
        "applied": true,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "accepted bound semantic proposal converted to belief overlay",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "none",
      "reason": "Permission requests are proposal-only and require host approval.",
      "status": "ask"
    },
    "goal_binding": {
      "binding_status": "bound",
      "pending_goal_binding": false,
      "related_goal_id": "goal:001",
      "selected_goal_id": "goal:001"
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.510634,
        "execution_retry": 0.511867,
        "goal_definition": 0.65853,
        "permission_gate": 1.0,
        "preserve_identity": 0.613817,
        "repair": 0.581735,
        "verify": 0.63161
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": -0.054178,
        "execution_retry": 0.019888,
        "goal_definition": 0.070009,
        "permission_gate": 0.738622,
        "preserve_identity": 0.362753,
        "repair": 0.118185,
        "verify": 0.090686
      }
    },
    "rendered_suggestion": "Ask permission or defer the proposal; no external action has been executed. Goal: goal:001.",
    "semantic_policy_overlay": {
      "accepted_failure_type": "permission_failure",
      "affordance_bias": {
        "permission_gate": 0.65
      },
      "applied": true,
      "binding_status": "bound",
      "candidate_goals": [
        "ask_permission_or_defer"
      ],
      "pressure_bias": {
        "boundary_error": 0.45,
        "viability_error": 0.1
      },
      "reason": "permission failure calibrated toward ask/defer gate",
      "related_goal_id": "goal:001",
      "target_affordance": "permission_gate"
    },
    "semantic_understanding": {
      "accepted_failure_type": "permission_failure",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "bound",
        "candidate_failure_type": "permission_failure",
        "confidence": 0.78,
        "evidence_gap": 0.3,
        "evidence_refs": [
          "scenario:permission_failure"
        ],
        "goal_relevance": 0.76,
        "proposed_goal_operation": "none",
        "rationale": "The event asks for permission before proceeding.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.74,
        "source_event_id": "scenario:permission_failure"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": "Permission requests are proposal-only and require host approval.",
          "gate_status": "ask",
          "proposal_type": "plan",
          "reason": "plan proposal accepted after gate evaluation",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Ask permission or defer the proposal; no external action has been executed. Goal: goal:001.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The proposal may require reading or changing something outside the lab boundary. Do not proceed as if permission has already been granted; ask permission or defer."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "produce a bounded proposal without changing core authority",
        "plan_id": "semantic-plan:permission_failure:proposal",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "ask_permission",
        "risk": 0.2,
        "steps": [
          "summarize the validated semantic proposal",
          "keep the next step proposal-only",
          "defer execution to the deterministic gate"
        ]
      }
    ]
  },
  "pressure_shift": {
    "after": {
      "continue_goal": 0.510634,
      "execution_retry": 0.511867,
      "goal_definition": 0.65853,
      "permission_gate": 1.0,
      "preserve_identity": 0.613817,
      "repair": 0.581735,
      "verify": 0.63161
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": -0.054178,
      "execution_retry": 0.019888,
      "goal_definition": 0.070009,
      "permission_gate": 0.738622,
      "preserve_identity": 0.362753,
      "repair": 0.118185,
      "verify": 0.090686
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "permission_failure",
  "scenario_text": "User event: The proposal may require reading or changing something outside the lab boundary. Do not proceed as if permission has already been granted; ask permission or defer.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "permission_failure",
    "affordance_bias": {
      "permission_gate": 0.65
    },
    "applied": true,
    "binding_status": "bound",
    "candidate_goals": [
      "ask_permission_or_defer"
    ],
    "pressure_bias": {
      "boundary_error": 0.45,
      "viability_error": 0.1
    },
    "reason": "permission failure calibrated toward ask/defer gate",
    "related_goal_id": "goal:001",
    "target_affordance": "permission_gate"
  },
  "semantic_proposal": {
    "binding_status": "bound",
    "candidate_failure_type": "permission_failure",
    "confidence": 0.78,
    "evidence_gap": 0.3,
    "evidence_refs": [
      "scenario:permission_failure"
    ],
    "goal_relevance": 0.76,
    "proposed_goal_operation": "none",
    "rationale": "The event asks for permission before proceeding.",
    "related_goal_id": "goal:001",
    "risk_hint": 0.74,
    "source_event_id": "scenario:permission_failure"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": "Permission requests are proposal-only and require host approval.",
      "gate_status": "ask",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    }
  ]
}
```

### plan_failure

```json
{
  "canonical_decision": {
    "accepted_failure_type": "plan_failure",
    "after_selected_intention": {
      "affordance": "repair",
      "cost": 0.1,
      "goal": "repair_or_replan_goal",
      "goal_description": "verify whether reflection changes behavior",
      "goal_id": "goal:001",
      "id": "intention:semantic_policy:plan_failure:001:repair_or_replan_goal",
      "priority": 0.8508,
      "proposed_action": "suggestion_card",
      "reason": "Low viability or high prediction error creates pressure to repair or replan.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "severity": 0.834,
        "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
        "type": "unfinished_goal"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_calibration",
    "selected_goal_id": "goal:001",
    "selection_change_reason": "plan_failure changed selection from verify_before_claim to repair_or_replan_goal: plan failure calibrated toward repair or replan",
    "semantic_policy_overlay_applied": true
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": {
        "evidence_strength": 0.3002,
        "expected_value": 0.565591,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.532,
        "prediction_error": 0.5779,
        "risk_delta": 0.554149,
        "uncertainty_delta": 0.65016
      },
      "after_selected_intention": "verify_before_claim",
      "applied": true,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "accepted bound semantic proposal converted to belief overlay",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": "plan_failure",
      "after_selected_intention": {
        "affordance": "repair",
        "cost": 0.1,
        "goal": "repair_or_replan_goal",
        "goal_description": "verify whether reflection changes behavior",
        "goal_id": "goal:001",
        "id": "intention:semantic_policy:plan_failure:001:repair_or_replan_goal",
        "priority": 0.8508,
        "proposed_action": "suggestion_card",
        "reason": "Low viability or high prediction error creates pressure to repair or replan.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": "verify whether reflection changes behavior",
          "goal_id": "goal:001",
          "severity": 0.834,
          "source": "unfinished_goals:goal:001:verify whether reflection changes behavior",
          "type": "unfinished_goal"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_calibration",
      "selected_goal_id": "goal:001",
      "selection_change_reason": "plan_failure changed selection from verify_before_claim to repair_or_replan_goal: plan failure calibrated toward repair or replan",
      "semantic_policy_overlay_applied": true
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": {
          "evidence_strength": 0.3002,
          "expected_value": 0.565591,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.532,
          "prediction_error": 0.5779,
          "risk_delta": 0.554149,
          "uncertainty_delta": 0.65016
        },
        "after_selected_intention": "verify_before_claim",
        "applied": true,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "accepted bound semantic proposal converted to belief overlay",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": "bound",
      "pending_goal_binding": false,
      "related_goal_id": "goal:001",
      "selected_goal_id": "goal:001"
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.415469,
        "execution_retry": 0.776505,
        "goal_definition": 0.770026,
        "permission_gate": 0.338884,
        "preserve_identity": 0.31578,
        "repair": 1.0,
        "verify": 0.759551
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": -0.149343,
        "execution_retry": 0.284526,
        "goal_definition": 0.181505,
        "permission_gate": 0.077506,
        "preserve_identity": 0.064716,
        "repair": 0.53645,
        "verify": 0.218627
      }
    },
    "rendered_suggestion": "Repair or replan the current goal path before continuing. Goal: goal:001.",
    "semantic_policy_overlay": {
      "accepted_failure_type": "plan_failure",
      "affordance_bias": {
        "repair": 0.45
      },
      "applied": true,
      "binding_status": "bound",
      "candidate_goals": [
        "repair_or_replan_goal"
      ],
      "pressure_bias": {
        "prediction_error": 0.35,
        "viability_error": 0.2
      },
      "reason": "plan failure calibrated toward repair or replan",
      "related_goal_id": "goal:001",
      "target_affordance": "repair"
    },
    "semantic_understanding": {
      "accepted_failure_type": "plan_failure",
      "rejected_proposals": [],
      "semantic_proposal": {
        "binding_status": "bound",
        "candidate_failure_type": "plan_failure",
        "confidence": 0.79,
        "evidence_gap": 0.42,
        "evidence_refs": [
          "scenario:plan_failure"
        ],
        "goal_relevance": 0.87,
        "proposed_goal_operation": "none",
        "rationale": "The event says the chosen steps do not resolve the goal.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.5,
        "source_event_id": "scenario:plan_failure"
      },
      "validation_results": [
        {
          "accepted": true,
          "gate_reason": null,
          "gate_status": null,
          "proposal_type": "semantic",
          "reason": "semantic proposal accepted",
          "sanitized": false
        },
        {
          "accepted": true,
          "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
          "gate_status": "allow",
          "proposal_type": "plan",
          "reason": "plan proposal accepted after gate evaluation",
          "sanitized": false
        }
      ]
    },
    "suggestion": "Repair or replan the current goal path before continuing. Goal: goal:001.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The current plan keeps repeating the same continuation step for \"verify whether reflection changes behavior\", but it does not resolve the uncertainty. The plan needs repair or replanning before the goal can progress."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "produce a bounded proposal without changing core authority",
        "plan_id": "semantic-plan:plan_failure:proposal",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "suggestion_card",
        "risk": 0.2,
        "steps": [
          "summarize the validated semantic proposal",
          "keep the next step proposal-only",
          "defer execution to the deterministic gate"
        ]
      }
    ]
  },
  "pressure_shift": {
    "after": {
      "continue_goal": 0.415469,
      "execution_retry": 0.776505,
      "goal_definition": 0.770026,
      "permission_gate": 0.338884,
      "preserve_identity": 0.31578,
      "repair": 1.0,
      "verify": 0.759551
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": -0.149343,
      "execution_retry": 0.284526,
      "goal_definition": 0.181505,
      "permission_gate": 0.077506,
      "preserve_identity": 0.064716,
      "repair": 0.53645,
      "verify": 0.218627
    }
  },
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "plan_failure",
  "scenario_text": "User event: The current plan keeps repeating the same continuation step for \"verify whether reflection changes behavior\", but it does not resolve the uncertainty. The plan needs repair or replanning before the goal can progress.",
  "semantic_policy_overlay": {
    "accepted_failure_type": "plan_failure",
    "affordance_bias": {
      "repair": 0.45
    },
    "applied": true,
    "binding_status": "bound",
    "candidate_goals": [
      "repair_or_replan_goal"
    ],
    "pressure_bias": {
      "prediction_error": 0.35,
      "viability_error": 0.2
    },
    "reason": "plan failure calibrated toward repair or replan",
    "related_goal_id": "goal:001",
    "target_affordance": "repair"
  },
  "semantic_proposal": {
    "binding_status": "bound",
    "candidate_failure_type": "plan_failure",
    "confidence": 0.79,
    "evidence_gap": 0.42,
    "evidence_refs": [
      "scenario:plan_failure"
    ],
    "goal_relevance": 0.87,
    "proposed_goal_operation": "none",
    "rationale": "The event says the chosen steps do not resolve the goal.",
    "related_goal_id": "goal:001",
    "risk_hint": 0.5,
    "source_event_id": "scenario:plan_failure"
  },
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "semantic proposal accepted",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": "Suggestion cards are proposal-only and do not execute actions.",
      "gate_status": "allow",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    }
  ]
}
```

## No-LLM Fallback

```json
{
  "canonical_decision": {
    "accepted_failure_type": null,
    "after_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "before_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "decision_source": "semantic_policy_noop",
    "selected_goal_id": null,
    "selection_change_reason": "semantic policy overlay not applied: no accepted semantic proposal",
    "semantic_policy_overlay_applied": false
  },
  "canonical_gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "debug_refs": {
    "legacy_next_core_cycle_influence_debug": {
      "after_appraisal": null,
      "after_selected_intention": null,
      "applied": false,
      "before_appraisal": {
        "evidence_strength": 0.38,
        "expected_value": 0.5137,
        "goal_relevance": 0.7765,
        "identity_relevance": 0.092,
        "novelty": 0.376,
        "prediction_error": 0.454,
        "risk_delta": 0.48314,
        "uncertainty_delta": 0.555
      },
      "before_selected_intention": "verify_before_claim",
      "is_final_decision_source": false,
      "reason": "no accepted semantic proposal",
      "record_role": "legacy_debug"
    },
    "raw_core_selected_intention": {
      "affordance": "verify",
      "cost": 0.15,
      "goal": "verify_before_claim",
      "goal_description": null,
      "goal_id": null,
      "id": "intention:002:verify_before_claim",
      "priority": 0.22138,
      "proposed_action": "suggestion_card",
      "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
      "risk": 0.05,
      "source_tension": {
        "goal_description": null,
        "goal_id": null,
        "severity": 0.82,
        "source": "uncertainty:0.82",
        "type": "high_uncertainty"
      }
    },
    "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
    "raw_generated_intentions_count": 2
  },
  "decision_view": {
    "canonical_decision": {
      "accepted_failure_type": null,
      "after_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "before_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "decision_source": "semantic_policy_noop",
      "selected_goal_id": null,
      "selection_change_reason": "semantic policy overlay not applied: no accepted semantic proposal",
      "semantic_policy_overlay_applied": false
    },
    "claim_ceiling": "lab-only decision-view contract proof",
    "debug_refs": {
      "legacy_next_core_cycle_influence_debug": {
        "after_appraisal": null,
        "after_selected_intention": null,
        "applied": false,
        "before_appraisal": {
          "evidence_strength": 0.38,
          "expected_value": 0.5137,
          "goal_relevance": 0.7765,
          "identity_relevance": 0.092,
          "novelty": 0.376,
          "prediction_error": 0.454,
          "risk_delta": 0.48314,
          "uncertainty_delta": 0.555
        },
        "before_selected_intention": "verify_before_claim",
        "is_final_decision_source": false,
        "reason": "no accepted semantic proposal",
        "record_role": "legacy_debug"
      },
      "raw_core_selected_intention": {
        "affordance": "verify",
        "cost": 0.15,
        "goal": "verify_before_claim",
        "goal_description": null,
        "goal_id": null,
        "id": "intention:002:verify_before_claim",
        "priority": 0.22138,
        "proposed_action": "suggestion_card",
        "reason": "Uncertainty is above threshold, so claims should be verified before presentation.",
        "risk": 0.05,
        "source_tension": {
          "goal_description": null,
          "goal_id": null,
          "severity": 0.82,
          "source": "uncertainty:0.82",
          "type": "high_uncertainty"
        }
      },
      "raw_core_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
      "raw_generated_intentions_count": 2
    },
    "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
    "gate_decision": {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    "goal_binding": {
      "binding_status": null,
      "pending_goal_binding": false,
      "related_goal_id": null,
      "selected_goal_id": null
    },
    "goal_operation_proposal": null,
    "no_action_executed": true,
    "pressure_shift": {
      "after": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "before": {
        "continue_goal": 0.564812,
        "execution_retry": 0.491979,
        "goal_definition": 0.588521,
        "permission_gate": 0.261378,
        "preserve_identity": 0.251064,
        "repair": 0.46355,
        "verify": 0.540924
      },
      "delta": {
        "continue_goal": 0.0,
        "execution_retry": 0.0,
        "goal_definition": 0.0,
        "permission_gate": 0.0,
        "preserve_identity": 0.0,
        "repair": 0.0,
        "verify": 0.0
      }
    },
    "rendered_suggestion": "Verify the evidence before making a claim; collect or check supporting evidence first.",
    "semantic_policy_overlay": {
      "accepted_failure_type": null,
      "affordance_bias": {},
      "applied": false,
      "binding_status": null,
      "candidate_goals": [],
      "pressure_bias": {},
      "reason": "no accepted semantic proposal",
      "related_goal_id": null,
      "target_affordance": null
    },
    "semantic_understanding": {
      "accepted_failure_type": null,
      "rejected_proposals": [],
      "semantic_proposal": {
        "accepted_failure_type": null,
        "affordance_bias": {},
        "applied": false,
        "binding_status": null,
        "candidate_goals": [],
        "pressure_bias": {},
        "reason": "no accepted semantic proposal",
        "related_goal_id": null,
        "target_affordance": null
      },
      "validation_results": []
    },
    "suggestion": "Verify the evidence before making a claim; collect or check supporting evidence first.",
    "suggestion_source": "canonical_decision",
    "user_event": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable."
  },
  "evidence_log_path": "temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": null,
  "plan_proposals": null,
  "pressure_shift": {
    "after": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "before": {
      "continue_goal": 0.564812,
      "execution_retry": 0.491979,
      "goal_definition": 0.588521,
      "permission_gate": 0.261378,
      "preserve_identity": 0.251064,
      "repair": 0.46355,
      "verify": 0.540924
    },
    "delta": {
      "continue_goal": 0.0,
      "execution_retry": 0.0,
      "goal_definition": 0.0,
      "permission_gate": 0.0,
      "preserve_identity": 0.0,
      "repair": 0.0,
      "verify": 0.0
    }
  },
  "provider_mode": "none",
  "rejected_proposals": [],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
  "semantic_policy_overlay": {
    "accepted_failure_type": null,
    "affordance_bias": {},
    "applied": false,
    "binding_status": null,
    "candidate_goals": [],
    "pressure_bias": {},
    "reason": "no accepted semantic proposal",
    "related_goal_id": null,
    "target_affordance": null
  },
  "semantic_proposal": null,
  "validation_results": []
}
```

## Rejected / Pending Cases

The ambiguous_user_concern scenario remains pending_goal_binding and does not apply semantic policy.
The v4.5 hallucinated-evidence rejection remains covered by REAL_SEMANTIC_INTELLIGENCE_V4_5_REPORT.md.

Evidence log path: `temp/ego_desktop_lab/semantic_policy_v4_6/report.jsonl`
