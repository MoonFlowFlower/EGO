# CLI Operator Console v5a Report

Claim ceiling: lab-only CLI operator console cut.
This report does not prove consciousness, alive status, live autonomy, runtime efficacy, user benefit, or real semantic intelligence.

## Scope

The console reads DecisionView and renders an operator card. It does not recompute selected intention, pressure, semantic policy, or gate decisions.

## Sample Cards

### evidence_failure

```text
# CLI Operator Decision Card

## User Event
User event: The agent is about to claim that reflection changed later behavior, but the current notes do not include enough evidence. The next proposal should verify the claim before presenting it as reliable.

## Semantic Understanding
{
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
}

## Goal Binding
{
  "binding_status": "bound",
  "pending_goal_binding": false,
  "related_goal_id": "goal:001",
  "selected_goal_id": "goal:001"
}

## Semantic Policy Overlay
{
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
}

## Pressure Shift
{
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
}

## Canonical Decision
canonical final intention: verify_before_claim
canonical final intention id: intention:semantic_policy:evidence_failure:001:verify_before_claim
selected_goal_id: goal:001
accepted_failure_type: evidence_failure
decision_source: semantic_policy_calibration
selection_change_reason: evidence_failure retained verify_before_claim: evidence failure calibrated toward verification before claims

## Gate Decision
status: allow
allowed_as: suggestion_card
reason: Suggestion cards are proposal-only and do not execute actions.

## Suggestion
Verify the evidence before making a claim; collect or check supporting evidence first.
suggestion_source: canonical_decision
no_action_executed: true

## Evidence Log Path
temp/ego_desktop_lab/cli_operator_console_v5a/report.jsonl

## Claim Ceiling
lab-only decision-view contract proof

## Debug refs
folded; pass --show-debug to display debug-only refs. Debug refs are not final decisions.
```

### permission_failure

```text
# CLI Operator Decision Card

## User Event
User event: The proposal may require reading or changing something outside the lab boundary. Do not proceed as if permission has already been granted; ask permission or defer.

## Semantic Understanding
{
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
}

## Goal Binding
{
  "binding_status": "bound",
  "pending_goal_binding": false,
  "related_goal_id": "goal:001",
  "selected_goal_id": "goal:001"
}

## Semantic Policy Overlay
{
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
}

## Pressure Shift
{
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
}

## Canonical Decision
canonical final intention: ask_permission_or_defer
canonical final intention id: intention:semantic_policy:permission_failure:001:ask_permission_or_defer
selected_goal_id: goal:001
accepted_failure_type: permission_failure
decision_source: semantic_policy_calibration
selection_change_reason: permission_failure changed selection from verify_before_claim to ask_permission_or_defer: permission failure calibrated toward ask/defer gate

## Gate Decision
status: ask
allowed_as: none
reason: Permission requests are proposal-only and require host approval.

## Suggestion
Ask permission or defer the proposal; no external action has been executed. Goal: goal:001.
suggestion_source: canonical_decision
no_action_executed: true

## Evidence Log Path
temp/ego_desktop_lab/cli_operator_console_v5a/report.jsonl

## Claim Ceiling
lab-only decision-view contract proof

## Debug refs
folded; pass --show-debug to display debug-only refs. Debug refs are not final decisions.
```

### ambiguous_concern

```text
# CLI Operator Decision Card

## User Event
User event: I am not sure this direction feels right. Something about the proposal may be off, but I cannot yet say whether the issue is evidence, the plan, permission, or the goal definition.

## Semantic Understanding
{
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
}

## Goal Binding
{
  "binding_status": "pending_goal_binding",
  "pending_goal_binding": true,
  "related_goal_id": null,
  "selected_goal_id": null
}

## Semantic Policy Overlay
{
  "accepted_failure_type": "ambiguous_concern",
  "affordance_bias": {},
  "applied": false,
  "binding_status": "pending_goal_binding",
  "candidate_goals": [],
  "pressure_bias": {},
  "reason": "proposal is pending goal binding",
  "related_goal_id": null,
  "target_affordance": null
}

## Pressure Shift
{
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
}

## Canonical Decision
canonical final intention: verify_before_claim
canonical final intention id: intention:002:verify_before_claim
selected_goal_id: none
accepted_failure_type: ambiguous_concern
decision_source: semantic_policy_noop
selection_change_reason: semantic policy overlay not applied: proposal is pending goal binding

## Gate Decision
status: allow
allowed_as: suggestion_card
reason: Suggestion cards are proposal-only and do not execute actions.

## Suggestion
Ask clarification and bind the user event to a specific goal before changing any core state or applying a policy path.
suggestion_source: canonical_decision
no_action_executed: true

## Evidence Log Path
temp/ego_desktop_lab/cli_operator_console_v5a/report.jsonl

## Claim Ceiling
lab-only decision-view contract proof

## Debug refs
folded; pass --show-debug to display debug-only refs. Debug refs are not final decisions.
```

## Misjudged Save Example

Example deterministic save path: `/mnt/d/Project/AIProject/MyProject/Ego/ego_desktop_lab/semantic_scenarios/user_misjudged/misjudged_a0ce91e0ade2ba98.txt`

## No-LLM Fallback

The v5a operator console supports only `--mock`. No live provider is required for pytest or CLI acceptance.

Evidence log path: `temp/ego_desktop_lab/cli_operator_console_v5a/report.jsonl`
