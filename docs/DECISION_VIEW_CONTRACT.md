# Decision View Contract v5a-pre

Claim ceiling: lab-only decision-view contract proof. This contract does not prove consciousness, alive status, live autonomy, runtime efficacy, user benefit, or real semantic intelligence.

## Authority Rule

`canonical_decision` is the only final decision source for semantic-to-policy observation.

The final selected intention must be read from:

```text
DecisionView.canonical_decision.after_selected_intention
```

Observation code must not treat any other selected-intention-like field as final.

## Debug-Only Fields

`legacy_next_core_cycle_influence_debug` and raw `next_core_cycle_influence` are debug-only references.

They may appear only under:

```text
DecisionView.debug_refs
```

They must carry `is_final_decision_source=false` when present. They must not override, repair, infer, or validate `canonical_decision`.

## No Recalculation Rule

The observation layer must not recalculate:

- `selected_intention`
- priority ranking
- pressure values
- gate decisions
- semantic policy overlay

`DecisionView` may summarize already-recorded before/after pressure maps as display-only `pressure_shift`, but this is not decision logic.

## Suggestion Rendering Rule

`DecisionView.suggestion` is a compatibility alias for `DecisionView.rendered_suggestion`.

The rendered suggestion must be produced from:

```text
DecisionView.canonical_decision
DecisionView.gate_decision
DecisionView.goal_binding
DecisionView.goal_operation_proposal
```

The suggestion renderer must not read pressure maps, generated intentions, legacy next-core-cycle influence, raw selected intention, or raw core suggestion as final decision evidence. Raw core suggestion may appear only under `DecisionView.debug_refs.raw_core_suggestion`.

`DecisionView.suggestion_source` must be `canonical_decision`. `DecisionView.no_action_executed` must be `true` unless a future gate record explicitly says an action was executed.

## Required Consumers

The semantic-scenario CLI / future GUI / explanation rendering paths must read `DecisionView` instead of directly reading internal calibration objects.

Allowed path:

```text
EvidenceRecord.canonical_decision -> DecisionView -> CLI / GUI / explanation
```

Disallowed path:

```text
semantic_policy_calibration.after_selected_intention -> CLI / GUI / explanation
next_core_cycle_influence.after_selected_intention -> CLI / GUI / explanation
generated_intentions -> CLI / GUI / explanation final decision
```

## Schema Update Rule

Update `DecisionView` and its contract tests whenever any of these records change:

- `canonical_decision`
- `canonical_gate_decision`
- semantic proposal / goal binding payload
- semantic policy overlay
- pressure map naming
- debug reference naming
- evidence log replay format

If a new final-decision-like field is added anywhere in semantic-policy evidence, the same change must explicitly document whether it is canonical, compatibility mirror, or debug-only.

## Fields Not Final By Themselves

The observation layer must not directly interpret these fields as final conclusions:

- raw `selected_intention`
- top-level compatibility `before_selected_intention`
- top-level compatibility `after_selected_intention`
- `next_selected_intention`
- `next_core_cycle_influence`
- `legacy_next_core_cycle_influence_debug`
- `debug_refs`
- raw pressure maps
- generated intentions
- LLM proposal payloads

Only `DecisionView.canonical_decision.after_selected_intention` is the final selected intention in the observation surface.
