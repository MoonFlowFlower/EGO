# EGO-R3-ADOPTION-SLICE-001A — Schema Notes

## Additive trace block

This slice adds one ignorable trace-row block named `kernel_adoption_v0`.
The existing `ego_desktop.joi_real_loop_trace_row.v0` fields and row hash
remain owned by the existing harness contract. The block is attached only
when the adoption runner injects `kernelAdoptionHook`; default trace-runner
calls do not emit it.

```json
{
  "kernel_adoption_v0": {
    "state_before_hash": "<sha256 over kernel_state_v0 envelope>",
    "state_after_hash": "<sha256 over kernel_state_v0 envelope>",
    "step_id": 1,
    "seed_context": {
      "seed": 123,
      "draw_index": 1
    }
  }
}
```

The block carries no action, tool, approval, memory-write, transport,
runtime-registration, or proactive authority fields. Existing readers can
ignore it as an unknown additive field.

## Kernel envelope

The adapter wraps the loop state opaquely as `joi_loop_state_v0` inside an
R0-compatible `kernel_state_v0` envelope:

```json
{
  "schema_version": "kernel_state_v0",
  "task_id": "ego-r3-adoption-slice-001a",
  "run_id": "<run id>",
  "episode_id": "<episode id>",
  "step_id": 0,
  "substates": {
    "joi_loop_state_v0": {}
  },
  "seed_registry": {},
  "ablations": {}
}
```

## Parity-safe value domain

Canonical hashes must byte-match
`scripts/ego_kernel/state.canonical_json_dumps`:
`sort_keys=True`, `ensure_ascii=False`, and compact separators.

The declared parity-safe value domain is:

- object
- array
- string
- bool
- null
- safe integer

Non-integer numeric state values are not hashed raw. At the adapter
boundary they are encoded as fixed-format decimal strings using `fixed_6`
(`Number(value).toFixed(6)` in JavaScript). Example: `1.25` becomes
`"1.250000"` before it enters the `kernel_state_v0` envelope.

This restriction is part of the measurement contract, not a mechanism
claim. It avoids Python/JavaScript float-rendering divergence without
forking the R0 canonicalization.
