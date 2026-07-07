# SCHEMA_NOTES — EGO-R0-KERNEL-STATE-SUBSTRATE-001A

The `kernel_trace_v0` rows reuse the existing G-ABLATION-compatible names
`run_id`, `episode_id`, `step_id`, `action`, `prediction_error`, and trace
hash vocabulary where the semantics match.

Intentional divergences:

- `state_before_hash` and `state_after_hash` replace the EgoDesktop backend
  snapshot's coarser `state_digest` field because R0 replay needs exact
  pre/post kernel-state equality per tick.
- `seed_context` is explicit because R0's seed registry is part of the
  replay contract; the EgoDesktop backend trace snapshot does not own RNG
  replay.
- `component_attribution` is kernel-local audit metadata only. It does not
  contain renderer identity, runtime authority, gate/approval state, memory
  write authority, or transport fields.

This is a default-off kernel substrate trace, not a second EgoDesktop runtime
schema and not a product trace registration.
