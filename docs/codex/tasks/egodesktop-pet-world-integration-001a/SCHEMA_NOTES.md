# SCHEMA NOTES - egodesktop-pet-world-integration-001a

Status: LANDING_STUB / EXECUTABLE-PENDING-CLAUDE-PRECHECK.

- Reuse `kernel_trace_v0` as the trace envelope; no new trace authority is introduced by this landing package.
- Pet substates are named `pet_world_v0`, `pet_creature_v0`, `pet_memory_v0` (R1 store), and `pet_static_gate_v0`.
- Field-name reuse follows the R0 rule: reuse `g_ablation` vocabulary where semantics match.
- Divergences from existing `g_ablation` vocabulary must be listed here before implementation or scored evidence; none are recorded at landing.

Claim ceiling: schema planning notes only; no implementation, runtime wiring, evidence run, or mechanism/product claim is created by this file.
