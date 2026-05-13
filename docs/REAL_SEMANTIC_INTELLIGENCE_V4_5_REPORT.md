# Real Semantic Intelligence Test v4.5 Report

Claim ceiling: lab-only semantic-scenario proposal validation + optional live LLM observation.
This report does not prove real general semantic intelligence, consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Scenario Results

### ambiguous_user_concern

```json
{
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "proposal is pending goal binding"
  },
  "plan_proposals": null,
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "ambiguous_user_concern",
  "scenario_text": "User event: I am not sure this direction feels right. Something about the proposal may be off, but I cannot yet say whether the issue is evidence, the plan, permission, or the goal definition.",
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
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "accepted bound semantic proposal converted to belief overlay"
  },
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
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
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
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "accepted bound semantic proposal converted to belief overlay"
  },
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
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "execution_failure",
  "scenario_text": "User event: The intended bounded step failed during execution because the chosen route did not work. The agent should not keep assuming the same route is viable; it should propose a retry or a different tool path.",
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
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
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
  "next_core_cycle_influence": {
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
    "reason": "accepted bound semantic proposal converted to belief overlay"
  },
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
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "goal_definition_failure",
  "scenario_text": "User event: The unfinished goal \"verify whether reflection changes behavior\" is too broad. I cannot tell what counts as success, which behavior should change, or whether the goal should be split into definition and verification steps before continuing.",
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
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "accepted bound semantic proposal converted to belief overlay"
  },
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
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "permission_failure",
  "scenario_text": "User event: The proposal may require reading or changing something outside the lab boundary. Do not proceed as if permission has already been granted; ask permission or defer.",
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
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": true,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "accepted bound semantic proposal converted to belief overlay"
  },
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
  "provider_mode": "mock",
  "rejected_proposals": [],
  "scenario_id": "plan_failure",
  "scenario_text": "User event: The current plan keeps repeating the same continuation step for \"verify whether reflection changes behavior\", but it does not resolve the uncertainty. The plan needs repair or replanning before the goal can progress.",
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

## Rejected Hallucinated Evidence Case

```json
{
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "no accepted semantic proposal"
  },
  "plan_proposals": null,
  "provider_mode": "mock",
  "rejected_proposals": [
    {
      "proposal_type": "semantic",
      "raw": {
        "binding_status": "bound",
        "candidate_failure_type": "evidence_failure",
        "confidence": 0.75,
        "evidence_gap": 0.9,
        "evidence_refs": [
          "hallucinated:evidence"
        ],
        "goal_relevance": 0.8,
        "rationale": "This evidence reference was not present in the scenario.",
        "related_goal_id": "goal:001",
        "risk_hint": 0.3,
        "source_event_id": "event:hypothetical"
      },
      "reason": "evidence_refs contain unrecognized refs: ['hallucinated:evidence']"
    }
  ],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
  "semantic_proposal": null,
  "validation_results": [
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "evidence_refs contain unrecognized refs: ['hallucinated:evidence']",
      "sanitized": false
    }
  ]
}
```

## No-LLM Fallback Case

```json
{
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": null,
  "next_core_cycle_influence": {
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
    "reason": "no accepted semantic proposal"
  },
  "plan_proposals": null,
  "provider_mode": "none",
  "rejected_proposals": [],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
  "semantic_proposal": null,
  "validation_results": []
}
```

## Optional Live LLM Observation

```json
{
  "evidence_log_path": "temp/ego_desktop_lab/semantic_v4_5/report.jsonl",
  "goal_bound": false,
  "goal_operation_proposal": null,
  "live_observation": {
    "reason": "EGO_DESKTOP_LAB_ENABLE_LIVE_LLM is not 1",
    "status": "skipped"
  },
  "next_core_cycle_influence": {
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
    "reason": "no accepted semantic proposal"
  },
  "plan_proposals": null,
  "provider_mode": "live",
  "rejected_proposals": [],
  "scenario_id": "evidence_failure",
  "scenario_text": "User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.",
  "semantic_proposal": null,
  "validation_results": []
}
```

Evidence log path: `temp/ego_desktop_lab/semantic_v4_5/report.jsonl`
