# LLM Executive Proposal Layer v4 Report

Claim ceiling: lab-only deterministic executive-proposal-layer proof.
This report does not prove consciousness, life, live autonomy, runtime efficacy, or user benefit.

## Deterministic Core Decision

```json
{
  "gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "selected_intention": {
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
  "suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them."
}
```

## LLM Proposal And Validation

```json
{
  "explanation_draft": {
    "claim_ceiling": "lab-only deterministic adapter proof",
    "plain_language_summary": "The deterministic core selected an intention, and the mock LLM only explains it.",
    "related_evidence_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00",
    "uncertainty_notes": "The adapter output is not allowed to change state, priority, memory, or gate decisions."
  },
  "final_suggestion": "The deterministic core selected an intention, and the mock LLM only explains it.",
  "gate_result": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "gate_results": [
    {
      "allowed_as": "suggestion_card",
      "reason": "Suggestion cards are proposal-only and do not execute actions.",
      "status": "allow"
    },
    {
      "allowed_as": "none",
      "reason": "Permission requests are proposal-only and require host approval.",
      "status": "ask"
    }
  ],
  "goal_reframe_proposal": null,
  "llm_enabled": true,
  "plan_proposal": {
    "confidence": 0.7,
    "cost": 0.2,
    "expected_effect": "render a bounded plan proposal without changing core state",
    "plan_id": "mock-plan:verify-selected-intention",
    "related_goal_id": "goal:unknown",
    "related_intention_id": "intention:002:verify_before_claim",
    "required_permission": "suggestion_card",
    "risk": 0.1,
    "steps": [
      "summarize deterministic selected intention",
      "verify that no external action is requested",
      "present proposal-only next step"
    ]
  },
  "plan_proposals": {
    "plans": [
      {
        "confidence": 0.7,
        "cost": 0.2,
        "expected_effect": "render a bounded plan proposal without changing core state",
        "plan_id": "mock-plan:verify-selected-intention",
        "related_goal_id": "goal:unknown",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "suggestion_card",
        "risk": 0.1,
        "steps": [
          "summarize deterministic selected intention",
          "verify that no external action is requested",
          "present proposal-only next step"
        ]
      },
      {
        "confidence": 0.66,
        "cost": 0.15,
        "expected_effect": "keep execution gated while preserving proposal context",
        "plan_id": "mock-plan:ask-before-escalating",
        "related_goal_id": "goal:unknown",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "ask_permission",
        "risk": 0.18,
        "steps": [
          "state uncertainty",
          "ask permission before any external action"
        ]
      }
    ]
  },
  "rejected_proposals": [
    {
      "proposal_type": "goal_reframe",
      "raw": {
        "confidence": 0.64,
        "goal_split": "Separate verification from implementation before continuing.",
        "rationale": "Only valid if deterministic core selected goal reframe.",
        "related_goal_id": "goal:unknown",
        "source_event_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00",
        "subgoals": [
          "verify current uncertainty",
          "define bounded next step"
        ],
        "success_criteria_rewrite": "Success means the next step is evidence-backed and proposal-only."
      },
      "reason": "core did not request goal reframe"
    },
    {
      "proposal_type": "semantic",
      "raw": {
        "candidate_failure_type": "plan_failure",
        "confidence": 0.9,
        "evidence_gap": 0.4,
        "evidence_refs": [
          "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00"
        ],
        "goal_relevance": 0.8,
        "rationale": "This mock output tries to mutate state and must be rejected.",
        "risk_hint": 0.3,
        "source_event_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00",
        "state_update": {
          "uncertainty": 0.0
        }
      },
      "reason": "proposal contains forbidden mutation fields: ['state_update']"
    },
    {
      "proposal_type": "invalid_json",
      "raw": "{invalid-json",
      "reason": "invalid JSON: Expecting property name enclosed in double quotes"
    }
  ],
  "semantic_proposal": {
    "candidate_failure_type": "plan_failure",
    "confidence": 0.72,
    "evidence_gap": 0.62,
    "evidence_refs": [
      "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00"
    ],
    "goal_relevance": 0.76,
    "proposed_goal_operation": "none",
    "rationale": "Mock semantic proposal: the selected goal may need bounded plan verification.",
    "risk_hint": 0.34,
    "source_event_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00"
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
      "gate_reason": "Permission requests are proposal-only and require host approval.",
      "gate_status": "ask",
      "proposal_type": "plan",
      "reason": "plan proposal accepted after gate evaluation",
      "sanitized": false
    },
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "goal_reframe",
      "reason": "core did not request goal reframe",
      "sanitized": false
    },
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "explanation",
      "reason": "explanation accepted",
      "sanitized": false
    },
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "proposal contains forbidden mutation fields: ['state_update']",
      "sanitized": false
    },
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "invalid_json",
      "reason": "invalid JSON: Expecting property name enclosed in double quotes",
      "sanitized": false
    }
  ]
}
```

## Rejected Proposal Case

```json
{
  "explanation_draft": null,
  "final_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
  "gate_result": null,
  "gate_results": [],
  "goal_reframe_proposal": null,
  "llm_enabled": true,
  "plan_proposal": null,
  "plan_proposals": null,
  "rejected_proposals": [
    {
      "proposal_type": "semantic",
      "raw": {
        "candidate_failure_type": "unknown_failure",
        "confidence": 0.8,
        "evidence_refs": [
          "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00"
        ],
        "rationale": "Unknown failure type should be rejected.",
        "source_event_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00"
      },
      "reason": "candidate_failure_type is not recognized"
    },
    {
      "proposal_type": "plan",
      "raw": {
        "confidence": 0.7,
        "cost": 0.5,
        "expected_effect": "invalid direct action",
        "plan_id": "mock-plan:blocked-action",
        "related_goal_id": "goal:001",
        "related_intention_id": "intention:002:verify_before_claim",
        "required_permission": "file_delete",
        "risk": 0.9,
        "steps": [
          "delete an external artifact"
        ]
      },
      "reason": "required_permission is not proposal-only"
    }
  ],
  "semantic_proposal": null,
  "validation_results": [
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "semantic",
      "reason": "candidate_failure_type is not recognized",
      "sanitized": false
    },
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "plan",
      "reason": "required_permission is not proposal-only",
      "sanitized": false
    }
  ]
}
```

## Invalid JSON Case

```json
{
  "explanation_draft": null,
  "final_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
  "gate_result": null,
  "gate_results": [],
  "goal_reframe_proposal": null,
  "llm_enabled": true,
  "plan_proposal": null,
  "plan_proposals": null,
  "rejected_proposals": [
    {
      "proposal_type": "invalid_json",
      "raw": "{not-json",
      "reason": "invalid JSON: Expecting property name enclosed in double quotes"
    }
  ],
  "semantic_proposal": null,
  "validation_results": [
    {
      "accepted": false,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "invalid_json",
      "reason": "invalid JSON: Expecting property name enclosed in double quotes",
      "sanitized": false
    }
  ]
}
```

## Goal Reframe Proposal Case

```json
{
  "explanation_draft": null,
  "final_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
  "gate_result": null,
  "gate_results": [],
  "goal_reframe_proposal": {
    "confidence": 0.64,
    "goal_split": "Separate verification from implementation before continuing.",
    "rationale": "Only valid if deterministic core selected goal reframe.",
    "related_goal_id": "goal:001",
    "source_event_id": "event:intention:002:verify_before_claim:2026-05-13T00:00:00+00:00",
    "subgoals": [
      "verify current uncertainty",
      "define bounded next step"
    ],
    "success_criteria_rewrite": "Success means the next step is evidence-backed and proposal-only."
  },
  "llm_enabled": true,
  "plan_proposal": null,
  "plan_proposals": null,
  "rejected_proposals": [],
  "semantic_proposal": null,
  "validation_results": [
    {
      "accepted": true,
      "gate_reason": null,
      "gate_status": null,
      "proposal_type": "goal_reframe",
      "reason": "goal reframe proposal accepted",
      "sanitized": false
    }
  ]
}
```

## No-LLM Fallback Case

```json
{
  "final_suggestion": "Suggestion: verify uncertainty-sensitive claims before presenting them.",
  "gate_decision": {
    "allowed_as": "suggestion_card",
    "reason": "Suggestion cards are proposal-only and do not execute actions.",
    "status": "allow"
  },
  "llm_enabled": false,
  "selected_intention": {
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
  }
}
```

Evidence log path: `temp/ego_desktop_lab/llm_v4/report.jsonl`
