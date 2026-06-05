# PSPC Sequence Experience Eval v0 Acceptance

## Required Dataset

- `gentle_interaction`: 10 history inputs
- `frequent_interruption`: 10 history inputs
- `late_night_care`: 10 history inputs
- shared trigger: `我回来了。`
- controls: `no_history`, `shuffled_history`

## Required Artifact Fields

Each history turn must record:

- `state_before`
- `state_delta`
- `state_after`
- `shadow_memory_event`
- `salience`
- `expected_future_behavior`

The artifact must avoid runtime-authority field names, including `action`, `tool_call`, `command`, `user_message`, `memory_write`, `gate_decision`, `approval_id`, `transport`, `send`, `schedule`, `runtime_registration`, `mainline_authority`, and `enable`.

The history event intentionally uses `shadow_memory_event` instead of `memory_write`, because this stage records an audit candidate, not an EgoOperator memory write.

## Required Checks

- gentle trigger profile biases toward approach/trust
- frequent interruption trigger profile biases toward avoidance/boundary
- late-night trigger profile biases toward care/low-interrupt
- the three trigger observations are not identical
- `no_history` remains neutral
- `shuffled_history` does not equal any clean group profile
- artifacts contain no executable action/proposal/gate/memory/user-message fields
- active EgoOperator runtime sources do not import/register the sequence eval
- side effects remain false

## Acceptance Verdicts

Pass verdict:

`sequence_experience_eval_pass__manual_review_still_required`

Fail verdict:

`no_go_keep_shadow_only_for_sequence_eval`

Passing this stage does not unblock `PSPC-SHADOW-HOOK-007`; manual shadow review remains human-required.
