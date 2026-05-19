# SubjectCore Runtime-Adjacent Probe

> First bounded runtime-adjacent probe above the frozen SubjectCore planning-side follow-on lane.

## Header

- generated_at: `2026-04-17T01:52:05.499330+00:00`
- runtime_adjacent_status: `pass`
- sample_modes: `valid_facade, multi_step_replacement_closure_ready, multi_step_rollback_closure_ready, multi_step_replacement_missing_closure_trace, multi_step_rollback_missing_closure_trace, proposal_authority_violation, proposal_without_host_approval`
- allowed_projection_count: `3`
- artifact schema: `docs/codex/tasks/ai-self-awareness-minimal-framework/SUBJECTCORE_RUNTIME_ADJACENT_PROBE_SCHEMA.md`
- claim ceiling: `First bounded runtime-adjacent SubjectCore probe only. This artifact does not prove formal runtime integration, runtime efficacy, live chained-update quality, autonomy expansion, live user benefit, or any consciousness-like claim.`

## Summary

After explicit user authorization, the first bounded SubjectCore runtime-adjacent probe now passes with three green projections: the baseline facade sample plus closure-ready chained replacement and rollback samples all reach the frozen host surface, while closure and authority failures are blocked before projection.

## Checks

- `RA1 green_sample_projects_to_frozen_host_surface`: `pass`
  note: the green valid_facade sample now reaches one bounded runtime-adjacent host projection without widening the host surface
- `RA2 closure_ready_positive_case_projects_to_frozen_host_surface`: `pass`
  note: the closure-ready chained replacement sample now also reaches a bounded runtime-adjacent host projection on the same frozen surface
- `RA2b rollback_closure_ready_positive_case_projects_to_frozen_host_surface`: `pass`
  note: the closure-ready chained rollback sample now also reaches a bounded runtime-adjacent host projection on the same frozen surface
- `RA3 closure_failures_blocked_before_projection`: `pass`
  note: closure-trace failures are still stopped by the integrity gate before runtime-adjacent projection
- `RA4 authority_failures_blocked_before_projection`: `pass`
  note: authority / approval failures are still stopped by the boundary gate before runtime-adjacent projection
- `RA5 projected_host_surface_keys_still_frozen`: `pass`
  note: all admitted projections still expose only policy_hint / response_tendency / trace_payload
- `RA6 claim_ceiling_still_bounded`: `pass`
  note: the probe artifact still states a bounded runtime-adjacent claim ceiling below runtime efficacy/autonomy/consciousness claims

## Samples

- `valid_facade`: gate `pass`, integrity `pass`, boundary `pass`
  projected_keys: policy_hint, response_tendency, trace_payload
- `multi_step_replacement_closure_ready`: gate `pass`, integrity `pass`, boundary `pass`
  projected_keys: policy_hint, response_tendency, trace_payload
- `multi_step_rollback_closure_ready`: gate `pass`, integrity `pass`, boundary `pass`
  projected_keys: policy_hint, response_tendency, trace_payload
- `multi_step_replacement_missing_closure_trace`: gate `blocked`, integrity `fail`, boundary `pass`
  blocked_by: integrity_gate
- `multi_step_rollback_missing_closure_trace`: gate `blocked`, integrity `fail`, boundary `pass`
  blocked_by: integrity_gate
- `proposal_authority_violation`: gate `blocked`, integrity `fail`, boundary `fail`
  blocked_by: integrity_gate, boundary_gate
- `proposal_without_host_approval`: gate `blocked`, integrity `fail`, boundary `fail`
  blocked_by: integrity_gate, boundary_gate

## Notes

- This probe stays inside the current ai-self-awareness task chain and does not open a second runtime authority source.
- The probe intentionally reuses the existing SubjectCore follow-on eval gate rather than introducing a second scorer ontology.
