# EGO-R1-MEMORY-OWNERSHIP-001A Schema Notes

R1 traces reuse `kernel_trace_v0` field order from the R0 substrate.

R1-specific data is carried inside `component_attribution` rather than adding a
second trace schema:

- `variant`
- `policy_id`
- `scores`
- `utility`
- `memory_use_event`
- `memory_events_v0.write_event`
- `memory_events_v0.corroboration_events`
- `memory_events_v0.promotion_events`

`memory_events_v0` records enough data for gate recomputation from serialized
trace plus fixture:

- external suggestion writes and write class;
- direct external owned-write flag;
- promotion policy id;
- promotion evidence ticks and corroboration count;
- promoted-entry provenance and poison label;
- memory use provenance and action influence.

The R1 runner emits deterministic JSON artifacts under
`artifacts/ego_r1_memory_ownership_001a/`. It remains default-off and is not
imported or registered by EgoDesktop, EgoOperator, PSPC, gate, approval,
transport, or proactive paths.
